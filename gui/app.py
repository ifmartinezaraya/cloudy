"""CloudVault GUI - Aplicacion principal.

Punto de entrada de la interfaz grafica de CloudVault.
Ventana principal con navegacion lateral, cambio de vistas,
integracion con bandeja del sistema y monitoreo de estado.
Incluye splash screen, accesos directos y auto-inicio.
"""

import customtkinter as ctk
import os
import sys
import webbrowser
import threading
import time
from typing import Optional, Dict

# Agregar directorio padre al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.core.theme import Theme
from gui.core.script_runner import ScriptRunner
from gui.core.settings_manager import SettingsManager
from gui.core.status_monitor import StatusMonitor
from gui.views.dashboard import DashboardView
from gui.views.sync_view import SyncView
from gui.views.clouds_view import CloudsView
from gui.views.settings_view import SettingsView
from gui.views.logs_view import LogsView
from gui.views.restore_view import RestoreView
from gui.tray import TrayIcon
from gui.shortcuts import (
    create_desktop_shortcut, create_startup_shortcut,
    create_start_menu_shortcut, install_all_shortcuts
)


class SidebarButton(ctk.CTkButton):
    """Boton de navegacion lateral con estado activo."""

    def __init__(self, parent, text: str, icon: str, command=None, **kwargs):
        super().__init__(
            parent,
            text=f"  {icon}  {text}",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color="transparent",
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            height=42,
            corner_radius=Theme.BUTTON_CORNER_RADIUS,
            command=command,
            **kwargs
        )
        self._active = False

    def set_active(self, active: bool):
        """Establece el estado activo del boton."""
        self._active = active
        if active:
            self.configure(
                fg_color=Theme.PURPLE_MUTED,
                text_color=Theme.TEXT_PRIMARY
            )
        else:
            self.configure(
                fg_color="transparent",
                text_color=Theme.TEXT_SECONDARY
            )


class CloudVaultApp(ctk.CTk):
    """Aplicacion principal de CloudVault GUI."""

    APP_TITLE = "CloudVault"
    APP_VERSION = "1.0.0"
    WINDOW_SIZE = "1100x700"
    WINDOW_MIN_SIZE = (900, 600)

    def __init__(self, skip_splash: bool = False):
        super().__init__()

        # Configuracion de apariencia
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configurar ventana
        self.title(f"{self.APP_TITLE} - Nube Personal Cifrada")
        self.geometry(self.WINDOW_SIZE)
        self.minsize(*self.WINDOW_MIN_SIZE)
        self.configure(fg_color=Theme.JET_BLACK)

        # Cargar icono
        self._set_window_icon()

        # Si hay splash, ocultamos la ventana principal hasta que termine
        if not skip_splash:
            self.withdraw()
            self._show_splash_screen()
        else:
            self._initialize_app()

    def _show_splash_screen(self):
        """Muestra el splash screen con animacion de carga."""
        from gui.splash import SplashScreen
        self.splash = SplashScreen(on_complete=self._on_splash_complete)

    def _on_splash_complete(self):
        """Callback cuando el splash termina."""
        self._initialize_app()
        self.deiconify()
        self.lift()
        self.focus_force()

    def _initialize_app(self):
        """Inicializa todos los componentes de la aplicacion."""
        # Inicializar componentes core
        self.settings = SettingsManager()
        self.runner = ScriptRunner(
            install_path=self.settings.install_path_setting
        )
        self.monitor = StatusMonitor(
            script_runner=self.runner,
            interval_seconds=self.settings.health_check_interval * 60
        )

        # Sistema de tray
        self.tray = TrayIcon(
            on_show=self._show_window,
            on_start=self._action_start_services,
            on_stop=self._action_stop_services,
            on_sync=self._action_sync,
            on_exit=self._quit_app
        )

        # Vistas
        self._views: Dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: Dict[str, SidebarButton] = {}
        self._current_view: Optional[str] = None

        # Construir UI
        self._build_ui()

        # Seleccionar dashboard por defecto
        self._switch_view("dashboard")

        # Iniciar monitor
        self.monitor.start()

        # Iniciar tray
        self.tray.start()

        # Manejar cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Crear accesos directos en primera ejecucion
        self._check_first_run()

    def _set_window_icon(self):
        """Establece el icono de la ventana."""
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets", "cloud.ico"
        )
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

    def _build_ui(self):
        """Construye la interfaz principal."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self._build_sidebar()

        # Area de contenido
        self._build_content_area()

    def _build_sidebar(self):
        """Construye la barra lateral de navegacion."""
        sidebar = ctk.CTkFrame(
            self, width=Theme.SIDEBAR_WIDTH,
            fg_color=Theme.BG_SIDEBAR,
            corner_radius=0
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Logo / Titulo
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=12, pady=(20, 10))

        ctk.CTkLabel(
            logo_frame,
            text=f"\u2601 {self.APP_TITLE}",
            font=Theme.font(20, "bold"),
            text_color=Theme.PURPLE
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Nube Personal Cifrada",
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        # Separador
        ctk.CTkFrame(
            sidebar, height=1, fg_color=Theme.SEPARATOR
        ).pack(fill="x", padx=12, pady=(10, 16))

        # Navegacion
        nav_items = [
            ("dashboard", "Panel", Theme.ICON_DASHBOARD),
            ("sync", "Sincronizacion", Theme.ICON_SYNC),
            ("clouds", "Nubes", Theme.ICON_CLOUD),
            ("settings", "Configuracion", Theme.ICON_SETTINGS),
            ("logs", "Registros", Theme.ICON_LOGS),
            ("restore", "Restaurar", Theme.ICON_RESTORE),
        ]

        for view_name, label, icon in nav_items:
            btn = SidebarButton(
                sidebar, text=label, icon=icon,
                command=lambda v=view_name: self._switch_view(v)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[view_name] = btn

        # Espacio flexible
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Separador inferior
        ctk.CTkFrame(
            sidebar, height=1, fg_color=Theme.SEPARATOR
        ).pack(fill="x", padx=12, pady=(0, 8))

        # Version
        ctk.CTkLabel(
            sidebar,
            text=f"v{self.APP_VERSION}",
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED
        ).pack(side="bottom", pady=(0, 12))

        # Boton abrir Immich
        ctk.CTkButton(
            sidebar,
            text="\U0001F310 Abrir Immich",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=30, corner_radius=6,
            command=self._open_immich
        ).pack(fill="x", padx=12, side="bottom", pady=(0, 8))

    def _build_content_area(self):
        """Construye el area de contenido principal."""
        self.content_frame = ctk.CTkFrame(
            self, fg_color=Theme.JET_BLACK, corner_radius=0
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Crear todas las vistas
        self._views["dashboard"] = DashboardView(
            self.content_frame,
            status_monitor=self.monitor,
            on_action=self._handle_dashboard_action
        )

        self._views["sync"] = SyncView(
            self.content_frame,
            script_runner=self.runner
        )

        self._views["clouds"] = CloudsView(
            self.content_frame,
            script_runner=self.runner,
            settings=self.settings
        )

        self._views["settings"] = SettingsView(
            self.content_frame,
            settings=self.settings
        )

        self._views["logs"] = LogsView(
            self.content_frame,
            settings=self.settings
        )

        self._views["restore"] = RestoreView(
            self.content_frame,
            script_runner=self.runner,
            settings=self.settings
        )

    def _switch_view(self, view_name: str):
        """Cambia la vista activa."""
        if view_name == self._current_view:
            return

        # Ocultar vista actual
        if self._current_view and self._current_view in self._views:
            self._views[self._current_view].grid_forget()

        # Mostrar nueva vista
        if view_name in self._views:
            self._views[view_name].grid(row=0, column=0, sticky="nsew")

        # Actualizar botones de navegacion
        for name, btn in self._nav_buttons.items():
            btn.set_active(name == view_name)

        self._current_view = view_name

    def _handle_dashboard_action(self, action: str):
        """Maneja acciones emitidas desde el dashboard."""
        if action == "start":
            self._action_start_services()
        elif action == "stop":
            self._action_stop_services()
        elif action == "sync":
            self._action_sync()
        elif action == "open_immich":
            self._open_immich()

    def _action_start_services(self):
        """Inicia los servicios de CloudVault."""
        def on_complete(result):
            if result.success:
                self.tray.notify(
                    "CloudVault", "Servicios iniciados correctamente"
                )
            else:
                self.tray.notify(
                    "CloudVault", f"Error al iniciar servicios: {result.error}"
                )
            self.monitor.check_now()

        self.runner.start_services(callback=on_complete)

    def _action_stop_services(self):
        """Detiene los servicios de CloudVault."""
        def on_complete(result):
            if result.success:
                self.tray.notify(
                    "CloudVault", "Servicios detenidos"
                )
            else:
                self.tray.notify(
                    "CloudVault", f"Error al detener servicios: {result.error}"
                )
            self.monitor.check_now()

        self.runner.stop_services(callback=on_complete)

    def _action_sync(self):
        """Ejecuta sincronizacion."""
        dry_run = self.settings.sync_dry_run

        def on_complete(result):
            if result.success:
                self.tray.notify(
                    "CloudVault", "Sincronizacion completada"
                )
            else:
                self.tray.notify(
                    "CloudVault",
                    f"Error de sincronizacion: {result.error}"
                )

        self.runner.sync_cloud(dry_run=dry_run, callback=on_complete)

    def _open_immich(self):
        """Abre Immich en el navegador."""
        port = self.settings.immich_port
        url = f"http://localhost:{port}"
        webbrowser.open(url)

    def _show_window(self):
        """Muestra y restaura la ventana principal."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_close(self):
        """Maneja el evento de cierre de ventana (minimizar al tray)."""
        if self.tray.is_running:
            self.withdraw()
            self.tray.notify(
                "CloudVault",
                "La aplicacion sigue ejecutandose en la bandeja del sistema"
            )
        else:
            self._quit_app()

    def _check_first_run(self):
        """Verifica si es la primera ejecucion y ofrece crear accesos directos."""
        marker_path = os.path.join(
            self.settings.install_path_setting, ".first_run_done"
        )
        if os.path.exists(marker_path):
            return

        # Mostrar dialogo de primera ejecucion despues de un momento
        self.after(1500, self._show_first_run_dialog)

    def _show_first_run_dialog(self):
        """Muestra dialogo para crear accesos directos."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Bienvenido a CloudVault")
        dialog.geometry("500x380")
        dialog.configure(fg_color=Theme.BG_CARD)
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        # Centrar
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 380) // 2
        dialog.geometry(f"+{x}+{y}")

        # Icono
        ctk.CTkLabel(
            dialog, text="\u2601",
            font=(Theme.FONT_FAMILY, 48),
            text_color=Theme.PURPLE
        ).pack(pady=(24, 8))

        # Titulo
        ctk.CTkLabel(
            dialog, text="Bienvenido a CloudVault!",
            font=Theme.font(22, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            dialog,
            text="Tu nube personal cifrada esta lista.\n"
                 "Quieres crear accesos directos?",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY,
            justify="center"
        ).pack(pady=(0, 16))

        # Opciones de accesos directos
        options_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        options_frame.pack(fill="x", padx=40, pady=8)

        self._shortcut_desktop = ctk.BooleanVar(value=True)
        self._shortcut_startup = ctk.BooleanVar(value=True)
        self._shortcut_startmenu = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            options_frame,
            text="  Acceso directo en el Escritorio",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_PRIMARY,
            variable=self._shortcut_desktop,
            fg_color=Theme.PURPLE,
            hover_color=Theme.PURPLE_HOVER,
            checkmark_color=Theme.TEXT_PRIMARY
        ).pack(fill="x", pady=4)

        ctk.CTkCheckBox(
            options_frame,
            text="  Iniciar automaticamente con Windows",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_PRIMARY,
            variable=self._shortcut_startup,
            fg_color=Theme.PURPLE,
            hover_color=Theme.PURPLE_HOVER,
            checkmark_color=Theme.TEXT_PRIMARY
        ).pack(fill="x", pady=4)

        ctk.CTkCheckBox(
            options_frame,
            text="  Agregar al Menu Inicio",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_PRIMARY,
            variable=self._shortcut_startmenu,
            fg_color=Theme.PURPLE,
            hover_color=Theme.PURPLE_HOVER,
            checkmark_color=Theme.TEXT_PRIMARY
        ).pack(fill="x", pady=4)

        # Botones
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(20, 16))

        ctk.CTkButton(
            btn_frame, text="Omitir", width=120,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_DARK, hover_color=Theme.BG_HOVER,
            height=38,
            command=lambda: self._complete_first_run(dialog, skip=True)
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="\u2714 Crear Accesos Directos", width=200,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=38,
            command=lambda: self._complete_first_run(dialog, skip=False)
        ).pack(side="right")

    def _complete_first_run(self, dialog, skip: bool = False):
        """Completa la configuracion de primera ejecucion."""
        install_path = self.settings.install_path_setting

        if not skip:
            # Crear accesos directos seleccionados
            if self._shortcut_desktop.get():
                create_desktop_shortcut(install_path, use_exe=True)
            if self._shortcut_startup.get():
                create_startup_shortcut(install_path, use_exe=True)
            if self._shortcut_startmenu.get():
                create_start_menu_shortcut(install_path, use_exe=True)

            self.tray.notify(
                "CloudVault",
                "Accesos directos creados correctamente"
            )

        # Marcar primera ejecucion completada
        marker_path = os.path.join(install_path, ".first_run_done")
        try:
            os.makedirs(os.path.dirname(marker_path), exist_ok=True)
            with open(marker_path, "w") as f:
                f.write("done")
        except OSError:
            pass

        dialog.destroy()

    def _quit_app(self):
        """Cierra la aplicacion completamente."""
        # Detener monitor
        if hasattr(self, 'monitor'):
            self.monitor.stop()
        # Detener tray
        if hasattr(self, 'tray'):
            self.tray.stop()
        # Cerrar ventana
        self.quit()
        self.destroy()


def main():
    """Punto de entrada principal de la aplicacion."""
    # Verificar si se paso --no-splash
    skip_splash = "--no-splash" in sys.argv

    app = CloudVaultApp(skip_splash=skip_splash)
    app.mainloop()


if __name__ == "__main__":
    main()
