"""CloudVault Logs View - Visor de registros en tiempo real.

Muestra los logs de la aplicacion con filtrado por nivel,
auto-scroll, y opciones de exportacion.
"""

import customtkinter as ctk
import os
import threading
import time
from typing import Optional, List
from ..core.theme import Theme
from ..core.settings_manager import SettingsManager


class LogsView(ctk.CTkFrame):
    """Vista de logs en tiempo real de CloudVault."""

    # Colores por nivel de log
    LEVEL_COLORS = {
        "INFO": Theme.TEXT_SECONDARY,
        "WARN": Theme.WARNING,
        "WARNING": Theme.WARNING,
        "ERROR": Theme.ERROR,
        "DEBUG": Theme.TEXT_MUTED,
        "SUCCESS": Theme.SUCCESS,
    }

    def __init__(self, parent, settings: Optional[SettingsManager] = None,
                 **kwargs):
        super().__init__(parent, fg_color=Theme.JET_BLACK, **kwargs)

        self.settings = settings or SettingsManager()
        self._logs_dir = os.path.join(self.settings.install_path_setting, "logs")
        self._auto_scroll = True
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._current_filter = "TODOS"
        self._all_lines: List[str] = []

        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz del visor de logs."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Barra de herramientas
        self._build_toolbar()

        # Area de texto
        self._build_text_area()

        # Barra de estado
        self._build_status_bar()

    def _build_toolbar(self):
        """Construye la barra de herramientas."""
        toolbar = ctk.CTkFrame(
            self, fg_color=Theme.BG_CARD,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        toolbar.grid(row=0, column=0, sticky="ew",
                     padx=Theme.PADDING_LARGE, pady=(Theme.PADDING_LARGE, 8))

        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=Theme.PADDING, pady=Theme.PADDING_SMALL)

        # Titulo
        ctk.CTkLabel(
            inner, text="\u2263 Registros del Sistema",
            font=Theme.font(Theme.FONT_SIZE_TITLE, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        # Filtro de nivel
        ctk.CTkLabel(
            inner, text="Filtrar:",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left", padx=(24, 4))

        self.filter_menu = ctk.CTkOptionMenu(
            inner,
            values=["TODOS", "INFO", "WARN", "ERROR", "DEBUG"],
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_INPUT, button_color=Theme.PURPLE,
            button_hover_color=Theme.PURPLE_HOVER,
            text_color=Theme.TEXT_PRIMARY, width=120,
            command=self._on_filter_change
        )
        self.filter_menu.pack(side="left", padx=4)
        self.filter_menu.set("TODOS")

        # Selector de archivo
        ctk.CTkLabel(
            inner, text="Archivo:",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left", padx=(16, 4))

        self.file_menu = ctk.CTkOptionMenu(
            inner, values=self._get_log_files(),
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_INPUT, button_color=Theme.PURPLE,
            button_hover_color=Theme.PURPLE_HOVER,
            text_color=Theme.TEXT_PRIMARY, width=200,
            command=self._on_file_change
        )
        self.file_menu.pack(side="left", padx=4)

        # Botones derecha
        ctk.CTkButton(
            inner, text="Exportar", width=80,
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=28, command=self._export_log
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            inner, text="Limpiar", width=80,
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            fg_color=Theme.BG_DARK, hover_color=Theme.BG_HOVER,
            height=28, command=self._clear_display
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            inner, text="\u21BB Actualizar", width=100,
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            fg_color=Theme.BG_DARK, hover_color=Theme.BG_HOVER,
            height=28, command=self._refresh_log
        ).pack(side="right", padx=4)

        # Toggle auto-scroll
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            inner, text="Auto-scroll",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_SECONDARY,
            variable=self.auto_scroll_var,
            fg_color=Theme.BG_DARK, progress_color=Theme.PURPLE,
            button_color=Theme.TEXT_PRIMARY, width=40,
            command=self._toggle_auto_scroll
        ).pack(side="right", padx=(4, 12))

    def _build_text_area(self):
        """Construye el area de texto para los logs."""
        self.log_text = ctk.CTkTextbox(
            self, font=("Consolas", 12),
            fg_color=Theme.BG_INPUT,
            text_color=Theme.TEXT_SECONDARY,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            scrollbar_button_color=Theme.SCROLLBAR,
            scrollbar_button_hover_color=Theme.SCROLLBAR_HOVER,
            wrap="none"
        )
        self.log_text.grid(row=1, column=0, sticky="nsew",
                           padx=Theme.PADDING_LARGE, pady=4)
        self.log_text.insert("1.0", "Selecciona un archivo de log para ver...\n")
        self.log_text.configure(state="disabled")

    def _build_status_bar(self):
        """Construye la barra de estado inferior."""
        status = ctk.CTkFrame(self, fg_color="transparent", height=24)
        status.grid(row=2, column=0, sticky="ew",
                    padx=Theme.PADDING_LARGE,
                    pady=(4, Theme.PADDING_SMALL))

        self.lines_label = ctk.CTkLabel(
            status, text="0 lineas",
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED
        )
        self.lines_label.pack(side="left")

        self.file_path_label = ctk.CTkLabel(
            status, text="",
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED
        )
        self.file_path_label.pack(side="right")

    def _get_log_files(self) -> List[str]:
        """Obtiene la lista de archivos de log disponibles."""
        log_files = []
        if os.path.exists(self._logs_dir):
            try:
                files = os.listdir(self._logs_dir)
                log_files = sorted(
                    [f for f in files if f.endswith(".log")],
                    reverse=True
                )
            except OSError:
                pass
        if not log_files:
            log_files = ["(sin archivos)"]
        return log_files

    def _on_file_change(self, filename: str):
        """Maneja el cambio de archivo seleccionado."""
        if filename == "(sin archivos)":
            return
        self._load_log_file(filename)

    def _on_filter_change(self, level: str):
        """Maneja el cambio de filtro de nivel."""
        self._current_filter = level
        self._apply_filter()

    def _load_log_file(self, filename: str):
        """Carga un archivo de log en el visor."""
        filepath = os.path.join(self._logs_dir, filename)
        self._all_lines = []

        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8",
                          errors="replace") as f:
                    self._all_lines = f.readlines()
        except (IOError, OSError):
            self._all_lines = ["Error al leer el archivo de log.\n"]

        self._apply_filter()
        self.file_path_label.configure(text=filepath)

    def _apply_filter(self):
        """Aplica el filtro de nivel actual al texto mostrado."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")

        if self._current_filter == "TODOS":
            filtered = self._all_lines
        else:
            filtered = [
                line for line in self._all_lines
                if self._current_filter in line.upper()
            ]

        for line in filtered:
            self.log_text.insert("end", line)

        self.log_text.configure(state="disabled")
        self.lines_label.configure(
            text=f"{len(filtered)} lineas (de {len(self._all_lines)} totales)"
        )

        if self._auto_scroll:
            self.log_text.see("end")

    def _refresh_log(self):
        """Recarga el archivo de log actual."""
        current_file = self.file_menu.get()
        if current_file and current_file != "(sin archivos)":
            self._load_log_file(current_file)

        # Actualizar lista de archivos
        files = self._get_log_files()
        self.file_menu.configure(values=files)

    def _clear_display(self):
        """Limpia la pantalla del visor."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", "Pantalla limpiada.\n")
        self.log_text.configure(state="disabled")
        self.lines_label.configure(text="0 lineas")

    def _toggle_auto_scroll(self):
        """Toggle del auto-scroll."""
        self._auto_scroll = self.auto_scroll_var.get()

    def _export_log(self):
        """Exporta el log actual a un archivo."""
        try:
            from tkinter import filedialog
            filepath = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt")],
                title="Exportar Log"
            )
            if filepath:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(self._all_lines)
        except Exception:
            pass

    def start_monitoring(self):
        """Inicia el monitoreo en tiempo real del log activo."""
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Detiene el monitoreo en tiempo real."""
        self._monitoring = False

    def _monitor_loop(self):
        """Bucle de monitoreo de nuevas lineas."""
        last_size = 0
        while self._monitoring:
            current_file = self.file_menu.get()
            if current_file and current_file != "(sin archivos)":
                filepath = os.path.join(self._logs_dir, current_file)
                try:
                    if os.path.exists(filepath):
                        current_size = os.path.getsize(filepath)
                        if current_size > last_size:
                            # Hay nuevas lineas
                            with open(filepath, "r", encoding="utf-8",
                                      errors="replace") as f:
                                f.seek(last_size)
                                new_lines = f.readlines()
                            last_size = current_size
                            if new_lines:
                                try:
                                    self.after(
                                        0,
                                        lambda nl=new_lines:
                                            self._append_new_lines(nl)
                                    )
                                except Exception:
                                    pass
                        elif current_size < last_size:
                            # Archivo fue rotado/truncado
                            last_size = 0
                except (IOError, OSError):
                    pass
            time.sleep(2)

    def _append_new_lines(self, lines: List[str]):
        """Agrega nuevas lineas al visor."""
        self._all_lines.extend(lines)
        if self._current_filter == "TODOS":
            filtered = lines
        else:
            filtered = [
                l for l in lines if self._current_filter in l.upper()
            ]

        if filtered:
            self.log_text.configure(state="normal")
            for line in filtered:
                self.log_text.insert("end", line)
            self.log_text.configure(state="disabled")

            if self._auto_scroll:
                self.log_text.see("end")

        total = len(self._all_lines)
        self.lines_label.configure(text=f"{total} lineas")
