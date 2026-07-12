"""CloudVault Sync View - Gestion de sincronizacion.

Permite ejecutar sincronizaciones manuales, forzar sync completo,
toggle dry-run, ver progreso y configurar la programacion.
"""

import customtkinter as ctk
import threading
from typing import Optional, Callable
from ..core.theme import Theme
from ..core.script_runner import ScriptRunner


class SyncView(ctk.CTkFrame):
    """Vista de gestion de sincronizacion de CloudVault."""

    def __init__(self, parent, script_runner: Optional[ScriptRunner] = None,
                 **kwargs):
        super().__init__(parent, fg_color=Theme.JET_BLACK, **kwargs)

        self.runner = script_runner or ScriptRunner()
        self._is_syncing = False

        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz de sincronizacion."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Encabezado
        self._build_header()

        # Controles de sync
        self._build_controls()

        # Configuracion de programacion
        self._build_schedule()

        # Visor de log
        self._build_log_viewer()

    def _build_header(self):
        """Construye el encabezado."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew",
                    padx=Theme.PADDING_LARGE, pady=(Theme.PADDING_LARGE, 8))

        title = ctk.CTkLabel(
            header, text="\u21BB Sincronizacion",
            font=Theme.font(Theme.FONT_SIZE_TITLE, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack(side="left")

        self.sync_status = ctk.CTkLabel(
            header, text="Listo para sincronizar",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY
        )
        self.sync_status.pack(side="right")

    def _build_controls(self):
        """Construye los controles de sincronizacion."""
        controls_frame = ctk.CTkFrame(
            self, fg_color=Theme.BG_CARD,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        controls_frame.grid(row=1, column=0, sticky="ew",
                            padx=Theme.PADDING_LARGE, pady=8)

        # Titulo seccion
        ctk.CTkLabel(
            controls_frame, text="Ejecutar Sincronizacion",
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.PURPLE_LIGHT
        ).pack(fill="x", padx=Theme.PADDING, pady=(Theme.PADDING, 8))

        # Frame de botones
        btn_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=Theme.PADDING, pady=8)

        # Boton sync normal
        self.btn_sync = ctk.CTkButton(
            btn_frame, text="\u21BB Sincronizar",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=40, width=160, command=self._start_sync
        )
        self.btn_sync.pack(side="left", padx=(0, 8))

        # Boton sync forzado
        self.btn_force = ctk.CTkButton(
            btn_frame, text="\u26A1 Forzar Sync Completo",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.WARNING, hover_color=Theme.WARNING_DARK,
            text_color=Theme.JET_BLACK, height=40, width=180,
            command=self._start_force_sync
        )
        self.btn_force.pack(side="left", padx=8)

        # Boton cancelar (oculto inicialmente)
        self.btn_cancel = ctk.CTkButton(
            btn_frame, text="\u2716 Cancelar",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.ERROR, hover_color=Theme.ERROR_DARK,
            height=40, width=120, command=self._cancel_sync
        )

        # Frame opciones
        opts_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        opts_frame.pack(fill="x", padx=Theme.PADDING, pady=(0, Theme.PADDING))

        # Toggle dry-run
        self.dry_run_var = ctk.BooleanVar(value=True)
        self.dry_run_switch = ctk.CTkSwitch(
            opts_frame, text="Modo prueba (Dry Run - no transfiere archivos)",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY,
            variable=self.dry_run_var,
            fg_color=Theme.BG_DARK,
            progress_color=Theme.PURPLE,
            button_color=Theme.TEXT_PRIMARY
        )
        self.dry_run_switch.pack(side="left", pady=4)

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(
            controls_frame, height=8,
            fg_color=Theme.BG_DARK, progress_color=Theme.PURPLE,
            corner_radius=4
        )
        self.progress_bar.pack(
            fill="x", padx=Theme.PADDING, pady=(0, Theme.PADDING)
        )
        self.progress_bar.set(0)

    def _build_schedule(self):
        """Construye la seccion de programacion."""
        sched_frame = ctk.CTkFrame(
            self, fg_color=Theme.BG_CARD,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        sched_frame.grid(row=2, column=0, sticky="ew",
                         padx=Theme.PADDING_LARGE, pady=8)

        ctk.CTkLabel(
            sched_frame, text="Programacion Automatica",
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.PURPLE_LIGHT
        ).pack(fill="x", padx=Theme.PADDING, pady=(Theme.PADDING, 8))

        config_frame = ctk.CTkFrame(sched_frame, fg_color="transparent")
        config_frame.pack(fill="x", padx=Theme.PADDING, pady=(0, Theme.PADDING))

        # Hora
        ctk.CTkLabel(
            config_frame, text="Hora:",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY
        ).grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")

        self.time_entry = ctk.CTkEntry(
            config_frame, width=80, placeholder_text="02:00",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_INPUT, border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY
        )
        self.time_entry.grid(row=0, column=1, padx=4, pady=4)
        self.time_entry.insert(0, "02:00")

        # Frecuencia
        ctk.CTkLabel(
            config_frame, text="Frecuencia:",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY
        ).grid(row=0, column=2, padx=(16, 8), pady=4, sticky="w")

        self.freq_menu = ctk.CTkOptionMenu(
            config_frame, values=["daily", "weekly", "hourly"],
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.BG_INPUT, button_color=Theme.PURPLE,
            button_hover_color=Theme.PURPLE_HOVER,
            text_color=Theme.TEXT_PRIMARY, width=120
        )
        self.freq_menu.grid(row=0, column=3, padx=4, pady=4)
        self.freq_menu.set("daily")

        # Boton aplicar
        self.btn_schedule = ctk.CTkButton(
            config_frame, text="Aplicar Programacion",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=32, width=160, command=self._apply_schedule
        )
        self.btn_schedule.grid(row=0, column=4, padx=(16, 0), pady=4)

    def _build_log_viewer(self):
        """Construye el visor de log de sincronizacion."""
        log_frame = ctk.CTkFrame(
            self, fg_color=Theme.BG_CARD,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        log_frame.grid(row=3, column=0, sticky="nsew",
                       padx=Theme.PADDING_LARGE,
                       pady=(8, Theme.PADDING_LARGE))

        # Encabezado del log
        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=Theme.PADDING, pady=(Theme.PADDING, 4))

        ctk.CTkLabel(
            log_header, text="Registro de Sincronizacion",
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.PURPLE_LIGHT
        ).pack(side="left")

        ctk.CTkButton(
            log_header, text="Limpiar", width=80,
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            fg_color=Theme.BG_DARK, hover_color=Theme.BG_HOVER,
            height=28, command=self._clear_log
        ).pack(side="right")

        # Area de texto para el log
        self.log_text = ctk.CTkTextbox(
            log_frame, font=("Consolas", 12),
            fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_SECONDARY,
            border_color=Theme.BORDER, corner_radius=8,
            scrollbar_button_color=Theme.SCROLLBAR
        )
        self.log_text.pack(
            fill="both", expand=True,
            padx=Theme.PADDING, pady=(4, Theme.PADDING)
        )
        self.log_text.insert("1.0", "Esperando operacion de sincronizacion...\n")
        self.log_text.configure(state="disabled")

    def _start_sync(self):
        """Inicia sincronizacion normal."""
        if self._is_syncing:
            return
        self._set_syncing(True)
        dry_run = self.dry_run_var.get()
        self._append_log(
            f"[SYNC] Iniciando sincronizacion "
            f"{'(Dry Run)' if dry_run else ''}...\n"
        )
        self.runner.sync_cloud(
            dry_run=dry_run, callback=self._on_sync_complete
        )

    def _start_force_sync(self):
        """Inicia sincronizacion forzada."""
        if self._is_syncing:
            return
        self._set_syncing(True)
        dry_run = self.dry_run_var.get()
        self._append_log(
            f"[SYNC] Iniciando sincronizacion FORZADA "
            f"{'(Dry Run)' if dry_run else ''}...\n"
        )
        self.runner.sync_cloud(
            force=True, dry_run=dry_run, callback=self._on_sync_complete
        )

    def _cancel_sync(self):
        """Cancela la sincronizacion actual."""
        self._set_syncing(False)
        self._append_log("[SYNC] Sincronizacion cancelada por el usuario.\n")

    def _on_sync_complete(self, result):
        """Callback cuando la sincronizacion termina."""
        try:
            self.after(0, lambda: self._handle_sync_result(result))
        except Exception:
            pass

    def _handle_sync_result(self, result):
        """Procesa el resultado de la sincronizacion."""
        self._set_syncing(False)
        if result.success:
            self._append_log(f"[OK] Sincronizacion completada.\n")
            if result.output:
                self._append_log(result.output + "\n")
            self.sync_status.configure(
                text="Sincronizacion exitosa", text_color=Theme.SUCCESS
            )
        else:
            self._append_log(f"[ERROR] {result.error}\n")
            if result.output:
                self._append_log(result.output + "\n")
            self.sync_status.configure(
                text="Error en sincronizacion", text_color=Theme.ERROR
            )

    def _apply_schedule(self):
        """Aplica la configuracion de programacion."""
        time_val = self.time_entry.get().strip()
        freq_val = self.freq_menu.get()

        self._append_log(
            f"[SCHEDULE] Programando sync: {freq_val} a las {time_val}\n"
        )

        def on_result(result):
            try:
                self.after(0, lambda: self._handle_schedule_result(result))
            except Exception:
                pass

        self.runner.schedule_sync(
            time=time_val, frequency=freq_val, callback=on_result
        )

    def _handle_schedule_result(self, result):
        """Procesa resultado de programacion."""
        if result.success:
            self._append_log("[OK] Programacion aplicada correctamente.\n")
        else:
            self._append_log(f"[ERROR] {result.error}\n")

    def _set_syncing(self, syncing: bool):
        """Actualiza el estado de sincronizacion en la UI."""
        self._is_syncing = syncing
        if syncing:
            self.btn_sync.configure(state="disabled")
            self.btn_force.configure(state="disabled")
            self.btn_cancel.pack(side="left", padx=8)
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.sync_status.configure(
                text="Sincronizando...", text_color=Theme.PURPLE_LIGHT
            )
        else:
            self.btn_sync.configure(state="normal")
            self.btn_force.configure(state="normal")
            self.btn_cancel.pack_forget()
            self.progress_bar.stop()
            self.progress_bar.set(0)

    def _append_log(self, text: str):
        """Agrega texto al visor de log."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        """Limpia el visor de log."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", "Log limpiado.\n")
        self.log_text.configure(state="disabled")
