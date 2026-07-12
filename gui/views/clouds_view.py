"""CloudVault Clouds View - Gestion de proveedores de nube.

Muestra los proveedores configurados (Mega, Google Drive, OneDrive),
sus estados, barras de capacidad, y permite reconfigurar o verificar.
"""

import customtkinter as ctk
from typing import Optional, List, Dict
from ..core.theme import Theme
from ..core.script_runner import ScriptRunner
from ..core.settings_manager import SettingsManager


class ProviderCard(ctk.CTkFrame):
    """Tarjeta visual para un proveedor de nube."""

    PROVIDER_ICONS = {
        "mega": "\u2601",
        "drive": "\U0001F4BE",
        "onedrive": "\u2601",
    }

    PROVIDER_COLORS = {
        "mega": "#E53935",
        "drive": "#4285F4",
        "onedrive": "#0078D4",
    }

    def __init__(self, parent, provider_data: Dict, runner: ScriptRunner,
                 **kwargs):
        super().__init__(parent, fg_color=Theme.BG_CARD,
                         corner_radius=Theme.CARD_CORNER_RADIUS,
                         border_width=1, border_color=Theme.BORDER, **kwargs)

        self.provider = provider_data
        self.runner = runner
        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz de la tarjeta."""
        self.grid_columnconfigure(1, weight=1)

        provider_type = self.provider.get("type", "")
        icon = self.PROVIDER_ICONS.get(provider_type, "\u2601")
        color = self.PROVIDER_COLORS.get(provider_type, Theme.PURPLE)
        name = self.provider.get("name", "Desconocido")
        capacity = self.provider.get("capacity_gb", 0)
        enabled = self.provider.get("enabled", False)
        priority = self.provider.get("priority", 0)

        # Icono
        icon_label = ctk.CTkLabel(
            self, text=icon, font=Theme.font(28),
            text_color=color, width=50
        )
        icon_label.grid(row=0, column=0, rowspan=3, padx=(12, 8), pady=12)

        # Nombre y tipo
        name_label = ctk.CTkLabel(
            self, text=name.replace("-", " ").title(),
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.TEXT_PRIMARY, anchor="w"
        )
        name_label.grid(row=0, column=1, sticky="w", padx=4, pady=(12, 0))

        # Info
        info_text = (
            f"Capacidad: {capacity} GB | "
            f"Prioridad: {priority} | "
            f"{'Habilitado' if enabled else 'Deshabilitado'}"
        )
        info_label = ctk.CTkLabel(
            self, text=info_text,
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_SECONDARY, anchor="w"
        )
        info_label.grid(row=1, column=1, sticky="w", padx=4, pady=2)

        # Barra de capacidad
        bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        bar_frame.grid(row=2, column=1, sticky="ew", padx=4, pady=(4, 12))
        bar_frame.grid_columnconfigure(0, weight=1)

        self.capacity_bar = ctk.CTkProgressBar(
            bar_frame, height=12,
            fg_color=Theme.BG_DARK, progress_color=color,
            corner_radius=6
        )
        self.capacity_bar.grid(row=0, column=0, sticky="ew", pady=2)
        self.capacity_bar.set(0.0)  # Se actualizara con datos reales

        self.usage_label = ctk.CTkLabel(
            bar_frame, text=f"0 / {capacity} GB",
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED, anchor="w"
        )
        self.usage_label.grid(row=1, column=0, sticky="w")

        # Estado indicador
        status_color = Theme.SUCCESS if enabled else Theme.TEXT_MUTED
        status_text = "\u25CF Activo" if enabled else "\u25CF Inactivo"
        self.status_label = ctk.CTkLabel(
            self, text=status_text,
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=status_color
        )
        self.status_label.grid(row=0, column=2, padx=12, pady=(12, 0))

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=2, rowspan=2, padx=12, pady=8)

        ctk.CTkButton(
            btn_frame, text="Verificar", width=90,
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=28, command=self._verify_provider
        ).pack(pady=2)

        ctk.CTkButton(
            btn_frame, text="Reconfigurar", width=90,
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            fg_color=Theme.BG_DARK, hover_color=Theme.BG_HOVER,
            height=28, command=self._reconfigure_provider
        ).pack(pady=2)

    def _verify_provider(self):
        """Verifica la conexion con el proveedor."""
        name = self.provider.get("name", "")
        self.status_label.configure(
            text="\u25CF Verificando...", text_color=Theme.WARNING
        )

        def on_result(result):
            try:
                if result.success:
                    self.after(0, lambda: self.status_label.configure(
                        text="\u25CF Verificado", text_color=Theme.SUCCESS
                    ))
                else:
                    self.after(0, lambda: self.status_label.configure(
                        text="\u25CF Error", text_color=Theme.ERROR
                    ))
            except Exception:
                pass

        self.runner.run_async(
            "configure",
            params={"Provider": name, "Verify": True},
            callback=on_result
        )

    def _reconfigure_provider(self):
        """Inicia la reconfiguracion del proveedor."""
        name = self.provider.get("name", "")
        self.runner.configure_cloud(provider=name)

    def update_usage(self, used_gb: float):
        """Actualiza la barra de uso con datos reales."""
        capacity = self.provider.get("capacity_gb", 1)
        ratio = min(used_gb / capacity, 1.0) if capacity > 0 else 0
        self.capacity_bar.set(ratio)
        self.usage_label.configure(text=f"{used_gb:.1f} / {capacity} GB")


class CloudsView(ctk.CTkFrame):
    """Vista de gestion de proveedores de nube."""

    def __init__(self, parent, script_runner: Optional[ScriptRunner] = None,
                 settings: Optional[SettingsManager] = None, **kwargs):
        super().__init__(parent, fg_color=Theme.JET_BLACK, **kwargs)

        self.runner = script_runner or ScriptRunner()
        self.settings = settings or SettingsManager()
        self._provider_cards: List[ProviderCard] = []

        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz de nubes."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Encabezado
        self._build_header()

        # Resumen
        self._build_summary()

        # Lista de proveedores
        self._build_providers_list()

    def _build_header(self):
        """Construye el encabezado."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew",
                    padx=Theme.PADDING_LARGE, pady=(Theme.PADDING_LARGE, 8))

        ctk.CTkLabel(
            header, text="\u2601 Proveedores de Nube",
            font=Theme.font(Theme.FONT_SIZE_TITLE, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkButton(
            header, text="\u2699 Configurar Nuevos",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            fg_color=Theme.PURPLE, hover_color=Theme.PURPLE_HOVER,
            height=36, width=160, command=self._configure_all
        ).pack(side="right")

    def _build_summary(self):
        """Construye el resumen de capacidad total."""
        summary = ctk.CTkFrame(
            self, fg_color=Theme.BG_CARD,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        summary.grid(row=1, column=0, sticky="ew",
                     padx=Theme.PADDING_LARGE, pady=8)

        summary_inner = ctk.CTkFrame(summary, fg_color="transparent")
        summary_inner.pack(fill="x", padx=Theme.PADDING, pady=Theme.PADDING)

        providers = self.settings.get_enabled_providers()
        total_capacity = self.settings.get_total_cloud_capacity()
        num_providers = len(providers)

        # Info general
        ctk.CTkLabel(
            summary_inner,
            text=f"Almacenamiento Unificado: {total_capacity} GB "
                 f"({num_providers} proveedores activos)",
            font=Theme.font(Theme.FONT_SIZE_SUBTITLE, "bold"),
            text_color=Theme.PURPLE_LIGHT, anchor="w"
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            summary_inner,
            text=f"Union: {self.settings.get('cloud.union_name', 'cloudvault-union')} | "
                 f"Cifrado: AES-256 | Nombres cifrados",
            font=Theme.font(Theme.FONT_SIZE_BODY),
            text_color=Theme.TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", pady=2)

        # Barra total
        self.total_bar = ctk.CTkProgressBar(
            summary_inner, height=14,
            fg_color=Theme.BG_DARK, progress_color=Theme.PURPLE,
            corner_radius=7
        )
        self.total_bar.pack(fill="x", pady=(8, 4))
        self.total_bar.set(0.0)

        self.total_label = ctk.CTkLabel(
            summary_inner,
            text=f"0 / {total_capacity} GB utilizados",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_MUTED, anchor="w"
        )
        self.total_label.pack(fill="x")

    def _build_providers_list(self):
        """Construye la lista de tarjetas de proveedores."""
        # Frame scrollable
        scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Theme.SCROLLBAR,
            scrollbar_button_hover_color=Theme.SCROLLBAR_HOVER
        )
        scroll_frame.grid(row=2, column=0, sticky="nsew",
                          padx=Theme.PADDING_LARGE,
                          pady=(8, Theme.PADDING_LARGE))
        scroll_frame.grid_columnconfigure(0, weight=1)

        providers = self.settings.cloud_providers
        for i, provider in enumerate(providers):
            card = ProviderCard(scroll_frame, provider, self.runner)
            card.grid(row=i, column=0, sticky="ew", pady=4)
            self._provider_cards.append(card)

        # Si no hay proveedores
        if not providers:
            ctk.CTkLabel(
                scroll_frame,
                text="No hay proveedores configurados.\n"
                     "Usa el boton 'Configurar Nuevos' para agregar nubes.",
                font=Theme.font(Theme.FONT_SIZE_BODY),
                text_color=Theme.TEXT_MUTED, justify="center"
            ).grid(row=0, column=0, pady=40)

    def _configure_all(self):
        """Inicia la configuracion de todos los proveedores."""
        self.runner.configure_cloud()

    def refresh(self):
        """Recarga la informacion de proveedores."""
        self.settings.load()
        # Reconstruir la vista
        for widget in self.winfo_children():
            widget.destroy()
        self._provider_cards.clear()
        self._build_ui()
