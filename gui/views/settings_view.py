"""CloudVault Settings View - Editor de configuracion.

Permite editar los campos principales de config/settings.json
con validacion y guardado seguro.
"""

import customtkinter as ctk
from typing import Optional
from ..core.theme import Theme
from ..core.settings_manager import SettingsManager


class SettingRow(ctk.CTkFrame):
    """Fila individual de configuracion con etiqueta y control."""

    def __init__(self, parent, label: str, description: str = "",
                 **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(1, weight=1)

        # Etiqueta
        ctk.CTkLabel(
            self, text=label,
            font=Theme.font(Theme.FONT_SIZE_BODY, "bold"),
            text_color=Theme.TEXT_PRIMARY, anchor="w", width=200
        ).grid(row=0, column=0, sticky="w", padx=(0, 12), pady=4)

        # Descripcion
        if description:
            ctk.CTkLabel(
                self, text=description,
                font=Theme.font(Theme.FONT_SIZE_CAPTION),
                text_color=Theme.TEXT_MUTED, anchor="w"
            ).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(0, 4))


class SettingsView(ctk.CTkFrame):
    """Vista de configuracion de CloudVault."""

    def __init__(self, parent, settings: Optional[SettingsManager] = None,
                 **kwargs):
        super().__init__(parent, fg_color=Theme.JET_BLACK, **kwargs)

        self.settings = settings or SettingsManager()
        self._widgets = {}

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        """Construye la interfaz de configuracion."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Encabezado
        self._build_header()

        # Contenido scrollable
        self._build_settings_form()

    def _build_header(self):
        """Construye el encabezado con boton guardar."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew",
                    padx=Theme.PADDING_LARGE, pady=(Theme.PADDING_LARGE, 8))

        ctk.CTkLabel(
            header, text="\u2699 Configuracion",
            font=Theme.font(Theme.FONT_SIZE_TITLE, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        # Botones
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Descartar", width=100,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_DARK, hover_color=Theme.BG_HOVER,
            height=34, command=self._discard_changes
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="\u2714 Guardar", width=100,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_DARK,
            height=34, command=self._save_settings
        ).pack(side="left", padx=4)

        # Mensaje de estado
        self.status_msg = ctk.CTkLabel(
            header, text="",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_MUTED
        )
        self.status_msg.pack(side="right", padx=12)

    def _build_settings_form(self):
        """Construye el formulario de configuracion."""
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Theme.SCROLLBAR,
            scrollbar_button_hover_color=Theme.SCROLLBAR_HOVER
        )
        scroll.grid(row=1, column=0, sticky="nsew",
                    padx=Theme.PADDING_LARGE,
                    pady=(8, Theme.PADDING_LARGE))
        scroll.grid_columnconfigure(0, weight=1)

        row = 0

        # --- Seccion General ---
        row = self._add_section(scroll, "General", row)
        row = self._add_entry(scroll, "general.install_path",
                              "Ruta de Instalacion",
                              "Directorio base de CloudVault", row)
        row = self._add_switch(scroll, "general.auto_start_on_boot",
                               "Inicio Automatico",
                               "Iniciar CloudVault al encender Windows", row)
        row = self._add_switch(scroll, "general.notifications_enabled",
                               "Notificaciones",
                               "Mostrar notificaciones del sistema", row)
        row = self._add_option(scroll, "general.log_level",
                               "Nivel de Log",
                               ["DEBUG", "INFO", "WARN", "ERROR"],
                               "Detalle de los registros", row)

        # --- Seccion Immich ---
        row = self._add_section(scroll, "Immich Server", row)
        row = self._add_entry(scroll, "immich.port",
                              "Puerto",
                              "Puerto web de Immich (default: 2283)", row)
        row = self._add_switch(scroll, "immich.machine_learning",
                               "Machine Learning",
                               "Reconocimiento facial y clasificacion", row)

        # --- Seccion Almacenamiento ---
        row = self._add_section(scroll, "Almacenamiento", row)
        row = self._add_entry(scroll, "storage.upload_path",
                              "Ruta de Uploads",
                              "Donde se guardan las fotos subidas", row)
        row = self._add_entry(scroll, "storage.max_local_usage_gb",
                              "Uso Local Maximo (GB)",
                              "Limite de espacio en disco para CloudVault", row)
        row = self._add_switch(scroll, "storage.auto_cleanup",
                               "Limpieza Automatica",
                               "Eliminar archivos locales despues de subir a nube",
                               row)

        # --- Seccion Sincronizacion ---
        row = self._add_section(scroll, "Sincronizacion", row)
        row = self._add_entry(scroll, "sync.schedule",
                              "Hora de Sync",
                              "Hora programada (HH:MM)", row)
        row = self._add_option(scroll, "sync.frequency",
                               "Frecuencia",
                               ["daily", "weekly", "hourly"],
                               "Con que frecuencia sincronizar", row)
        row = self._add_entry(scroll, "sync.transfers",
                              "Transferencias Paralelas",
                              "Numero de archivos simultaneos", row)
        row = self._add_entry(scroll, "sync.bandwidth_limit",
                              "Limite de Ancho de Banda",
                              "Vacio = sin limite (ej: 10M, 1G)", row)
        row = self._add_switch(scroll, "sync.dry_run",
                               "Modo Prueba (Dry Run)",
                               "Solo simular, no transferir archivos", row)
        row = self._add_switch(scroll, "sync.verify_after_upload",
                               "Verificar Uploads",
                               "Comprobar integridad despues de subir", row)

        # --- Seccion Salud ---
        row = self._add_section(scroll, "Monitoreo de Salud", row)
        row = self._add_entry(scroll, "health.check_interval_minutes",
                              "Intervalo de Chequeo (min)",
                              "Cada cuantos minutos verificar el sistema", row)

    def _add_section(self, parent, title: str, row: int) -> int:
        """Agrega un encabezado de seccion."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", pady=(16, 4))

        ctk.CTkLabel(
            frame, text=title,
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.PURPLE_LIGHT, anchor="w"
        ).pack(fill="x")

        sep = ctk.CTkFrame(frame, height=1, fg_color=Theme.SEPARATOR)
        sep.pack(fill="x", pady=(4, 0))

        return row + 1

    def _add_entry(self, parent, key: str, label: str,
                   description: str, row: int) -> int:
        """Agrega un campo de texto editable."""
        frame = ctk.CTkFrame(
            parent, fg_color=Theme.BG_CARD,
            corner_radius=8, border_width=1, border_color=Theme.BORDER
        )
        frame.grid(row=row, column=0, sticky="ew", pady=3)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame, text=label,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_PRIMARY, width=220, anchor="w"
        ).grid(row=0, column=0, padx=(12, 8), pady=(8, 0), sticky="w")

        ctk.CTkLabel(
            frame, text=description,
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED, anchor="w"
        ).grid(row=1, column=0, padx=(12, 8), pady=(0, 8), sticky="w")

        entry = ctk.CTkEntry(
            frame, font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_INPUT, border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY, width=250
        )
        entry.grid(row=0, column=1, rowspan=2, padx=(8, 12), pady=8,
                   sticky="e")

        self._widgets[key] = ("entry", entry)
        return row + 1

    def _add_switch(self, parent, key: str, label: str,
                    description: str, row: int) -> int:
        """Agrega un switch on/off."""
        frame = ctk.CTkFrame(
            parent, fg_color=Theme.BG_CARD,
            corner_radius=8, border_width=1, border_color=Theme.BORDER
        )
        frame.grid(row=row, column=0, sticky="ew", pady=3)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame, text=label,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_PRIMARY, width=220, anchor="w"
        ).grid(row=0, column=0, padx=(12, 8), pady=(8, 0), sticky="w")

        ctk.CTkLabel(
            frame, text=description,
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED, anchor="w"
        ).grid(row=1, column=0, padx=(12, 8), pady=(0, 8), sticky="w")

        var = ctk.BooleanVar()
        switch = ctk.CTkSwitch(
            frame, text="", variable=var,
            fg_color=Theme.BG_DARK, progress_color=Theme.PURPLE,
            button_color=Theme.TEXT_PRIMARY
        )
        switch.grid(row=0, column=1, rowspan=2, padx=(8, 12), pady=8,
                    sticky="e")

        self._widgets[key] = ("switch", var)
        return row + 1

    def _add_option(self, parent, key: str, label: str,
                    options: list, description: str, row: int) -> int:
        """Agrega un menu de opciones."""
        frame = ctk.CTkFrame(
            parent, fg_color=Theme.BG_CARD,
            corner_radius=8, border_width=1, border_color=Theme.BORDER
        )
        frame.grid(row=row, column=0, sticky="ew", pady=3)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame, text=label,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_PRIMARY, width=220, anchor="w"
        ).grid(row=0, column=0, padx=(12, 8), pady=(8, 0), sticky="w")

        ctk.CTkLabel(
            frame, text=description,
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED, anchor="w"
        ).grid(row=1, column=0, padx=(12, 8), pady=(0, 8), sticky="w")

        menu = ctk.CTkOptionMenu(
            frame, values=options,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_INPUT, button_color=Theme.PURPLE,
            button_hover_color=Theme.PURPLE_HOVER,
            text_color=Theme.TEXT_PRIMARY, width=180
        )
        menu.grid(row=0, column=1, rowspan=2, padx=(8, 12), pady=8,
                  sticky="e")

        self._widgets[key] = ("option", menu)
        return row + 1

    def _load_values(self):
        """Carga los valores actuales de settings en los widgets."""
        for key, (widget_type, widget) in self._widgets.items():
            value = self.settings.get(key)
            if value is None:
                continue

            if widget_type == "entry":
                widget.delete(0, "end")
                widget.insert(0, str(value))
            elif widget_type == "switch":
                widget.set(bool(value))
            elif widget_type == "option":
                widget.set(str(value))

    def _save_settings(self):
        """Guarda todos los cambios en settings.json."""
        for key, (widget_type, widget) in self._widgets.items():
            if widget_type == "entry":
                value = widget.get().strip()
                # Intentar convertir a numero si corresponde
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
                self.settings.set(key, value)
            elif widget_type == "switch":
                self.settings.set(key, widget.get())
            elif widget_type == "option":
                self.settings.set(key, widget.get())

        if self.settings.save():
            self.status_msg.configure(
                text="\u2714 Configuracion guardada",
                text_color=Theme.SUCCESS
            )
        else:
            self.status_msg.configure(
                text="\u2716 Error al guardar",
                text_color=Theme.ERROR
            )

        # Limpiar mensaje despues de 3 segundos
        self.after(3000, lambda: self.status_msg.configure(text=""))

    def _discard_changes(self):
        """Descarta cambios y recarga valores originales."""
        self.settings.discard_changes()
        self._load_values()
        self.status_msg.configure(
            text="Cambios descartados", text_color=Theme.TEXT_MUTED
        )
        self.after(3000, lambda: self.status_msg.configure(text=""))

    def reload(self):
        """Recarga la configuracion desde disco."""
        self.settings.load()
        self._load_values()
