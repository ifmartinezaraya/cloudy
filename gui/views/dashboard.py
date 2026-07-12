"""CloudVault Dashboard - Vista principal del panel de control.

Muestra el estado general del sistema: servicios, uso de disco,
ultima sincronizacion, resumen de nubes y acciones rapidas.
"""

import customtkinter as ctk
from typing import Optional, Callable
from ..core.theme import Theme
from ..core.status_monitor import StatusMonitor, SystemHealth


class StatusIndicator(ctk.CTkFrame):
    """Widget indicador de estado de un servicio."""

    def __init__(self, parent, service_name: str, **kwargs):
        super().__init__(parent, fg_color=Theme.BG_CARD,
                         corner_radius=Theme.CARD_CORNER_RADIUS, **kwargs)
        self.service_name = service_name

        self.grid_columnconfigure(1, weight=1)

        # Indicador de color (circulo)
        self.indicator = ctk.CTkLabel(
            self, text="\u25CF", font=Theme.font(16),
            text_color=Theme.TEXT_MUTED, width=24
        )
        self.indicator.grid(row=0, column=0, padx=(8, 4), pady=8)

        # Nombre del servicio
        self.name_label = ctk.CTkLabel(
            self, text=service_name,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_PRIMARY, anchor="w"
        )
        self.name_label.grid(row=0, column=1, padx=4, pady=8, sticky="w")

        # Estado texto
        self.status_label = ctk.CTkLabel(
            self, text="Desconocido",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_MUTED
        )
        self.status_label.grid(row=0, column=2, padx=(4, 12), pady=8)

    def set_status(self, status: str):
        """Actualiza el estado visual del indicador."""
        status_lower = status.lower()
        if status_lower == "running":
            color = Theme.SUCCESS
            text = "Activo"
        elif status_lower == "stopped":
            color = Theme.TEXT_MUTED
            text = "Detenido"
        elif status_lower == "error":
            color = Theme.ERROR
            text = "Error"
        else:
            color = Theme.WARNING
            text = "Desconocido"

        self.indicator.configure(text_color=color)
        self.status_label.configure(text=text, text_color=color)


class DashboardCard(ctk.CTkFrame):
    """Tarjeta visual para secciones del dashboard."""

    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, fg_color=Theme.BG_CARD,
                         corner_radius=Theme.CARD_CORNER_RADIUS,
                         border_width=1, border_color=Theme.BORDER, **kwargs)

        # Titulo de la tarjeta
        self.title_label = ctk.CTkLabel(
            self, text=title,
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.PURPLE_LIGHT, anchor="w"
        )
        self.title_label.pack(
            fill="x", padx=Theme.PADDING, pady=(Theme.PADDING, 8)
        )

        # Separador
        self.separator = ctk.CTkFrame(
            self, height=1, fg_color=Theme.SEPARATOR
        )
        self.separator.pack(fill="x", padx=Theme.PADDING)

        # Contenedor de contenido
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(
            fill="both", expand=True,
            padx=Theme.PADDING, pady=(8, Theme.PADDING)
        )


class DashboardView(ctk.CTkFrame):
    """Vista principal del Dashboard de CloudVault."""

    def __init__(self, parent, status_monitor: Optional[StatusMonitor] = None,
                 on_action: Optional[Callable] = None, **kwargs):
        super().__init__(parent, fg_color=Theme.JET_BLACK, **kwargs)

        self.monitor = status_monitor
        self.on_action = on_action
        self._service_indicators = {}

        self._build_ui()

        # Registrar callback de monitor
        if self.monitor:
            self.monitor.add_callback(self._on_status_update)

    def _build_ui(self):
        """Construye la interfaz del dashboard."""
        # Configurar grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Encabezado
        self._build_header()

        # Tarjeta de servicios
        self._build_services_card()

        # Tarjeta de almacenamiento
        self._build_storage_card()

        # Tarjeta de sincronizacion
        self._build_sync_card()

        # Tarjeta de acciones rapidas
        self._build_actions_card()

    def _build_header(self):
        """Construye el encabezado del dashboard."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew",
                    padx=Theme.PADDING_LARGE, pady=(Theme.PADDING_LARGE, 8))
        header.grid_columnconfigure(1, weight=1)

        # Titulo
        title = ctk.CTkLabel(
            header, text="\u2601 Panel de Control",
            font=Theme.font(Theme.FONT_SIZE_TITLE, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, sticky="w")

        # Estado general
        self.overall_status = ctk.CTkLabel(
            header, text="\u25CF Sistema sin verificar",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_MUTED
        )
        self.overall_status.grid(row=0, column=1, sticky="e", padx=8)

        # Boton refrescar
        refresh_btn = ctk.CTkButton(
            header, text="\u21BB Actualizar", width=120,
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            command=self._refresh_status
        )
        refresh_btn.grid(row=0, column=2, sticky="e")

    def _build_services_card(self):
        """Construye la tarjeta de estado de servicios."""
        card = DashboardCard(self, title="Servicios Docker")
        card.grid(row=1, column=0, sticky="nsew",
                  padx=(Theme.PADDING_LARGE, 8),
                  pady=8)

        # Contenedores conocidos
        services = [
            ("cloudvault_server", "Immich Server"),
            ("cloudvault_ml", "Machine Learning"),
            ("cloudvault_redis", "Redis Cache"),
            ("cloudvault_db", "PostgreSQL DB"),
        ]

        for name, display_name in services:
            indicator = StatusIndicator(card.content, display_name)
            indicator.pack(fill="x", pady=2)
            self._service_indicators[name] = indicator

    def _build_storage_card(self):
        """Construye la tarjeta de almacenamiento."""
        card = DashboardCard(self, title="Almacenamiento")
        card.grid(row=1, column=1, sticky="nsew",
                  padx=(8, Theme.PADDING_LARGE),
                  pady=8)

        # Disco local
        local_label = ctk.CTkLabel(
            card.content, text="Disco Local",
            font=Theme.font(Theme.FONT_SIZE_BODY, "bold"),
            text_color=Theme.TEXT_PRIMARY, anchor="w"
        )
        local_label.pack(fill="x", pady=(4, 2))

        self.disk_bar = ctk.CTkProgressBar(
            card.content, height=16,
            fg_color=Theme.BG_DARK, progress_color=Theme.PURPLE,
            corner_radius=8
        )
        self.disk_bar.pack(fill="x", pady=2)
        self.disk_bar.set(0)

        self.disk_label = ctk.CTkLabel(
            card.content, text="-- GB libres de -- GB",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_SECONDARY, anchor="w"
        )
        self.disk_label.pack(fill="x", pady=(0, 8))

        # Nube
        cloud_label = ctk.CTkLabel(
            card.content, text="Almacenamiento en Nube",
            font=Theme.font(Theme.FONT_SIZE_BODY, "bold"),
            text_color=Theme.TEXT_PRIMARY, anchor="w"
        )
        cloud_label.pack(fill="x", pady=(8, 2))

        self.cloud_bar = ctk.CTkProgressBar(
            card.content, height=16,
            fg_color=Theme.BG_DARK, progress_color=Theme.PURPLE_LIGHT,
            corner_radius=8
        )
        self.cloud_bar.pack(fill="x", pady=2)
        self.cloud_bar.set(0)

        self.cloud_label = ctk.CTkLabel(
            card.content, text="-- GB usados de 40 GB (3 nubes)",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_SECONDARY, anchor="w"
        )
        self.cloud_label.pack(fill="x")

    def _build_sync_card(self):
        """Construye la tarjeta de informacion de sincronizacion."""
        card = DashboardCard(self, title="Sincronizacion")
        card.grid(row=2, column=0, sticky="nsew",
                  padx=(Theme.PADDING_LARGE, 8),
                  pady=(8, Theme.PADDING_LARGE))

        # Ultima sincronizacion
        self.sync_time_label = ctk.CTkLabel(
            card.content, text="Ultima sync: Nunca",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_PRIMARY, anchor="w"
        )
        self.sync_time_label.pack(fill="x", pady=4)

        self.sync_status_label = ctk.CTkLabel(
            card.content, text="Estado: Sin datos",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY, anchor="w"
        )
        self.sync_status_label.pack(fill="x", pady=4)

        # Proxima sincronizacion
        self.next_sync_label = ctk.CTkLabel(
            card.content, text="Programada: diariamente a las 02:00",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_MUTED, anchor="w"
        )
        self.next_sync_label.pack(fill="x", pady=4)

        # Immich info
        self.immich_label = ctk.CTkLabel(
            card.content,
            text="\u2601 Immich: puerto 2283",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_ACCENT, anchor="w"
        )
        self.immich_label.pack(fill="x", pady=(8, 0))

    def _build_actions_card(self):
        """Construye la tarjeta de acciones rapidas."""
        card = DashboardCard(self, title="Acciones Rapidas")
        card.grid(row=2, column=1, sticky="nsew",
                  padx=(8, Theme.PADDING_LARGE),
                  pady=(8, Theme.PADDING_LARGE))

        # Botones de accion
        btn_start = ctk.CTkButton(
            card.content, text="\u25B6 Iniciar Servicios",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_DARK,
            height=36, command=lambda: self._emit_action("start")
        )
        btn_start.pack(fill="x", pady=4)

        btn_stop = ctk.CTkButton(
            card.content, text="\u25A0 Detener Servicios",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.ERROR, hover_color=Theme.ERROR_DARK,
            height=36, command=lambda: self._emit_action("stop")
        )
        btn_stop.pack(fill="x", pady=4)

        btn_sync = ctk.CTkButton(
            card.content, text="\u21BB Sincronizar Ahora",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=36, command=lambda: self._emit_action("sync")
        )
        btn_sync.pack(fill="x", pady=4)

        btn_immich = ctk.CTkButton(
            card.content, text="\U0001F310 Abrir Immich",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.INFO, hover_color=Theme.INFO_DARK,
            height=36, command=lambda: self._emit_action("open_immich")
        )
        btn_immich.pack(fill="x", pady=4)

    def _refresh_status(self):
        """Ejecuta una verificacion de estado inmediata."""
        if self.monitor:
            self.monitor.check_now()

    def _emit_action(self, action: str):
        """Emite una accion al controlador principal."""
        if self.on_action:
            self.on_action(action)

    def _on_status_update(self, health: SystemHealth):
        """Callback cuando se actualiza el estado del sistema."""
        # Actualizar en el hilo principal de tkinter
        try:
            self.after(0, lambda: self._update_ui(health))
        except Exception:
            pass

    def _update_ui(self, health: SystemHealth):
        """Actualiza la interfaz con los datos de salud."""
        # Estado general
        status_map = {
            "healthy": ("\u25CF Sistema operativo", Theme.SUCCESS),
            "degraded": ("\u25CF Sistema degradado", Theme.WARNING),
            "error": ("\u25CF Sistema con errores", Theme.ERROR),
            "stopped": ("\u25CF Sistema detenido", Theme.TEXT_MUTED),
        }
        text, color = status_map.get(
            health.overall_status,
            ("\u25CF Estado desconocido", Theme.TEXT_MUTED)
        )
        self.overall_status.configure(text=text, text_color=color)

        # Servicios
        for name, indicator in self._service_indicators.items():
            service = health.services.get(name)
            if service:
                indicator.set_status(service.status)

        # Disco
        if health.disk_total_gb > 0:
            usage_ratio = health.disk_usage_percent / 100.0
            self.disk_bar.set(min(usage_ratio, 1.0))
            self.disk_label.configure(
                text=f"{health.disk_free_gb:.1f} GB libres de "
                     f"{health.disk_total_gb:.1f} GB"
            )

        # Nube
        if health.cloud_total_gb > 0:
            cloud_ratio = health.cloud_usage_gb / health.cloud_total_gb
            self.cloud_bar.set(min(cloud_ratio, 1.0))
            self.cloud_label.configure(
                text=f"{health.cloud_usage_gb:.1f} GB usados de "
                     f"{health.cloud_total_gb:.0f} GB (3 nubes)"
            )

        # Sync
        self.sync_time_label.configure(
            text=f"Ultima sync: {health.last_sync}"
        )
        sync_status_text = health.last_sync_status.capitalize()
        self.sync_status_label.configure(
            text=f"Estado: {sync_status_text}"
        )

        # Immich
        if health.immich_accessible:
            self.immich_label.configure(
                text=f"\u2601 Immich: Activo | "
                     f"{health.photos_count} fotos, {health.videos_count} videos",
                text_color=Theme.SUCCESS
            )
        else:
            self.immich_label.configure(
                text="\u2601 Immich: No accesible",
                text_color=Theme.TEXT_MUTED
            )

    def update_status(self, health: SystemHealth):
        """Metodo publico para actualizar estado desde fuera."""
        self._update_ui(health)
