"""CloudVault Restore View - Gestion de restauracion.

Permite seleccionar proveedor, elegir destino, listar archivos
disponibles en la nube y ejecutar restauraciones.
"""

import customtkinter as ctk
from typing import Optional, List
from ..core.theme import Theme
from ..core.script_runner import ScriptRunner
from ..core.settings_manager import SettingsManager


class RestoreView(ctk.CTkFrame):
    """Vista de restauracion de archivos desde la nube."""

    def __init__(self, parent, script_runner: Optional[ScriptRunner] = None,
                 settings: Optional[SettingsManager] = None, **kwargs):
        super().__init__(parent, fg_color=Theme.JET_BLACK, **kwargs)

        self.runner = script_runner or ScriptRunner()
        self.settings = settings or SettingsManager()
        self._is_restoring = False

        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz de restauracion."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Encabezado
        self._build_header()

        # Configuracion de restauracion
        self._build_config()

        # Lista de archivos y log
        self._build_file_list()

    def _build_header(self):
        """Construye el encabezado."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew",
                    padx=Theme.PADDING_LARGE, pady=(Theme.PADDING_LARGE, 8))

        ctk.CTkLabel(
            header, text="\u21A9 Restaurar desde Nube",
            font=Theme.font(Theme.FONT_SIZE_TITLE, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.restore_status = ctk.CTkLabel(
            header, text="",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY
        )
        self.restore_status.pack(side="right")

    def _build_config(self):
        """Construye la seccion de configuracion."""
        config_frame = ctk.CTkFrame(
            self, fg_color=Theme.BG_CARD,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        config_frame.grid(row=1, column=0, sticky="ew",
                          padx=Theme.PADDING_LARGE, pady=8)

        inner = ctk.CTkFrame(config_frame, fg_color="transparent")
        inner.pack(fill="x", padx=Theme.PADDING, pady=Theme.PADDING)
        inner.grid_columnconfigure(1, weight=1)

        # Proveedor
        ctk.CTkLabel(
            inner, text="Proveedor:",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY
        ).grid(row=0, column=0, padx=(0, 8), pady=8, sticky="w")

        providers = [
            p.get("name", "unknown")
            for p in self.settings.cloud_providers
        ]
        if not providers:
            providers = ["mega", "google-drive", "onedrive"]

        self.provider_menu = ctk.CTkOptionMenu(
            inner, values=providers,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_INPUT, button_color=Theme.PURPLE,
            button_hover_color=Theme.PURPLE_HOVER,
            text_color=Theme.TEXT_PRIMARY, width=180
        )
        self.provider_menu.grid(row=0, column=1, padx=4, pady=8, sticky="w")

        # Destino
        ctk.CTkLabel(
            inner, text="Destino:",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY
        ).grid(row=1, column=0, padx=(0, 8), pady=8, sticky="w")

        dest_frame = ctk.CTkFrame(inner, fg_color="transparent")
        dest_frame.grid(row=1, column=1, columnspan=2, sticky="ew", pady=8)
        dest_frame.grid_columnconfigure(0, weight=1)

        self.dest_entry = ctk.CTkEntry(
            dest_frame, placeholder_text="C:\\CloudVault\\restored",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_INPUT, border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY
        )
        self.dest_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            dest_frame, text="\U0001F4C1 Elegir", width=90,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_DARK, hover_color=Theme.BG_HOVER,
            height=32, command=self._choose_destination
        ).grid(row=0, column=1)

        # Botones de accion
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        self.btn_list = ctk.CTkButton(
            btn_frame, text="\U0001F4CB Listar Archivos",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=38, width=160, command=self._list_files
        )
        self.btn_list.pack(side="left", padx=(0, 8))

        self.btn_restore = ctk.CTkButton(
            btn_frame, text="\u21A9 Restaurar",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_DARK,
            height=38, width=140, command=self._start_restore
        )
        self.btn_restore.pack(side="left", padx=8)

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(
            inner, height=8,
            fg_color=Theme.BG_DARK, progress_color=Theme.PURPLE,
            corner_radius=4
        )
        self.progress_bar.grid(row=3, column=0, columnspan=3,
                               sticky="ew", pady=(12, 0))
        self.progress_bar.set(0)

    def _build_file_list(self):
        """Construye la lista de archivos y log de restauracion."""
        list_frame = ctk.CTkFrame(
            self, fg_color=Theme.BG_CARD,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        list_frame.grid(row=2, column=0, sticky="nsew",
                        padx=Theme.PADDING_LARGE,
                        pady=(8, Theme.PADDING_LARGE))

        # Encabezado
        list_header = ctk.CTkFrame(list_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=Theme.PADDING, pady=(Theme.PADDING, 4))

        ctk.CTkLabel(
            list_header, text="Archivos Disponibles / Registro",
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.PURPLE_LIGHT
        ).pack(side="left")

        self.file_count_label = ctk.CTkLabel(
            list_header, text="0 archivos",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_MUTED
        )
        self.file_count_label.pack(side="right")

        # Area de texto
        self.output_text = ctk.CTkTextbox(
            list_frame, font=("Consolas", 12),
            fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_SECONDARY,
            border_color=Theme.BORDER, corner_radius=8,
            scrollbar_button_color=Theme.SCROLLBAR
        )
        self.output_text.pack(
            fill="both", expand=True,
            padx=Theme.PADDING, pady=(4, Theme.PADDING)
        )
        self.output_text.insert(
            "1.0",
            "Usa 'Listar Archivos' para ver los archivos disponibles "
            "en el proveedor seleccionado.\n\n"
            "Luego selecciona un destino y presiona 'Restaurar' para "
            "recuperar tus archivos.\n"
        )
        self.output_text.configure(state="disabled")

    def _choose_destination(self):
        """Abre dialogo para elegir carpeta de destino."""
        try:
            from tkinter import filedialog
            folder = filedialog.askdirectory(
                title="Seleccionar carpeta de destino"
            )
            if folder:
                self.dest_entry.delete(0, "end")
                self.dest_entry.insert(0, folder)
        except Exception:
            pass

    def _list_files(self):
        """Lista los archivos disponibles en el proveedor seleccionado."""
        provider = self.provider_menu.get()
        self._append_output(
            f"\n[LISTANDO] Archivos en {provider}...\n"
        )
        self.btn_list.configure(state="disabled")

        def on_result(result):
            try:
                self.after(0, lambda: self._handle_list_result(result))
            except Exception:
                pass

        self.runner.restore(
            provider=provider, list_only=True, callback=on_result
        )

    def _handle_list_result(self, result):
        """Procesa el resultado de listar archivos."""
        self.btn_list.configure(state="normal")
        if result.success:
            output = result.output or "No se encontraron archivos."
            self._append_output(output + "\n")
            # Contar lineas como archivos aproximados
            lines = [l for l in result.output.split("\n") if l.strip()]
            self.file_count_label.configure(
                text=f"{len(lines)} elementos encontrados"
            )
        else:
            self._append_output(
                f"[ERROR] {result.error}\n"
            )

    def _start_restore(self):
        """Inicia la restauracion con confirmacion."""
        if self._is_restoring:
            return

        provider = self.provider_menu.get()
        destination = self.dest_entry.get().strip()

        if not destination:
            self._append_output(
                "[ERROR] Debes especificar una carpeta de destino.\n"
            )
            return

        # Confirmar restauracion
        self._show_confirm_dialog(provider, destination)

    def _show_confirm_dialog(self, provider: str, destination: str):
        """Muestra dialogo de confirmacion."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirmar Restauracion")
        dialog.geometry("400x200")
        dialog.configure(fg_color=Theme.BG_CARD)
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="\u26A0 Confirmar Restauracion",
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.WARNING
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            dialog,
            text=f"Proveedor: {provider}\nDestino: {destination}",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY, justify="center"
        ).pack(pady=10)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=100,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_DARK, hover_color=Theme.BG_HOVER,
            command=dialog.destroy
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="\u2714 Restaurar", width=100,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_DARK,
            command=lambda: self._confirm_restore(dialog, provider, destination)
        ).pack(side="left", padx=8)

    def _confirm_restore(self, dialog, provider: str, destination: str):
        """Ejecuta la restauracion confirmada."""
        dialog.destroy()
        self._is_restoring = True
        self.btn_restore.configure(state="disabled")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.restore_status.configure(
            text="Restaurando...", text_color=Theme.PURPLE_LIGHT
        )

        self._append_output(
            f"\n[RESTAURANDO] Desde {provider} hacia {destination}...\n"
        )

        def on_result(result):
            try:
                self.after(0, lambda: self._handle_restore_result(result))
            except Exception:
                pass

        self.runner.restore(
            provider=provider, destination=destination, callback=on_result
        )

    def _handle_restore_result(self, result):
        """Procesa el resultado de la restauracion."""
        self._is_restoring = False
        self.btn_restore.configure(state="normal")
        self.progress_bar.stop()
        self.progress_bar.set(1.0 if result.success else 0)

        if result.success:
            self._append_output("[OK] Restauracion completada.\n")
            if result.output:
                self._append_output(result.output + "\n")
            self.restore_status.configure(
                text="Restauracion exitosa", text_color=Theme.SUCCESS
            )
        else:
            self._append_output(f"[ERROR] {result.error}\n")
            if result.output:
                self._append_output(result.output + "\n")
            self.restore_status.configure(
                text="Error en restauracion", text_color=Theme.ERROR
            )

    def _append_output(self, text: str):
        """Agrega texto al area de salida."""
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text)
        self.output_text.see("end")
        self.output_text.configure(state="disabled")
