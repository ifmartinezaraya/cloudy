"""CloudVault Theme - Constantes de color y configuracion visual.

Paleta principal:
- Morado (#8B5CF6) como color de acento principal
- Negro azabache (#0a0a0a) como color de fondo
- Complementos derivados para estados, hover y bordes
"""


class Theme:
    """Constantes de color y estilo para la aplicacion CloudVault."""

    # Colores principales
    PURPLE = "#8B5CF6"
    PURPLE_HOVER = "#7C3AED"
    PURPLE_DARK = "#6D28D9"
    PURPLE_LIGHT = "#A78BFA"
    PURPLE_MUTED = "#4C1D95"

    # Fondos
    JET_BLACK = "#0a0a0a"
    BG_DARK = "#111111"
    BG_CARD = "#1A1A2E"
    BG_SIDEBAR = "#0F0F1A"
    BG_INPUT = "#16162A"
    BG_HOVER = "#1E1E3A"

    # Texto
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#A0A0B0"
    TEXT_MUTED = "#6B7280"
    TEXT_ACCENT = "#C4B5FD"

    # Estados
    SUCCESS = "#10B981"
    SUCCESS_DARK = "#065F46"
    WARNING = "#F59E0B"
    WARNING_DARK = "#92400E"
    ERROR = "#EF4444"
    ERROR_DARK = "#991B1B"
    INFO = "#3B82F6"
    INFO_DARK = "#1E40AF"

    # Bordes
    BORDER = "#2D2D4A"
    BORDER_HOVER = "#4C4C6A"
    BORDER_ACTIVE = PURPLE

    # Componentes
    SCROLLBAR = "#3D3D5C"
    SCROLLBAR_HOVER = "#5D5D7C"
    SEPARATOR = "#2A2A40"

    # Dimensiones
    SIDEBAR_WIDTH = 220
    CORNER_RADIUS = 12
    BUTTON_CORNER_RADIUS = 8
    CARD_CORNER_RADIUS = 10
    PADDING = 16
    PADDING_SMALL = 8
    PADDING_LARGE = 24

    # Tipografia
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_TITLE = 24
    FONT_SIZE_SUBTITLE = 18
    FONT_SIZE_BODY = 14
    FONT_SIZE_SMALL = 12
    FONT_SIZE_CAPTION = 11

    # Iconos sidebar (unicode)
    ICON_DASHBOARD = "\u2302"  # Casa
    ICON_SYNC = "\u21BB"       # Flechas circulares
    ICON_CLOUD = "\u2601"      # Nube
    ICON_SETTINGS = "\u2699"   # Engranaje
    ICON_LOGS = "\u2263"       # Lineas
    ICON_RESTORE = "\u21A9"    # Flecha regreso
    ICON_TRAY = "\u2601"       # Nube (tray)

    @classmethod
    def get_ctk_theme(cls):
        """Retorna configuracion de tema para CustomTkinter."""
        return {
            "CTk": {
                "fg_color": [cls.JET_BLACK, cls.JET_BLACK]
            },
            "CTkFrame": {
                "fg_color": [cls.BG_CARD, cls.BG_CARD],
                "border_color": [cls.BORDER, cls.BORDER],
                "corner_radius": cls.CARD_CORNER_RADIUS
            },
            "CTkButton": {
                "fg_color": [cls.PURPLE, cls.PURPLE],
                "hover_color": [cls.PURPLE_HOVER, cls.PURPLE_HOVER],
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY],
                "corner_radius": cls.BUTTON_CORNER_RADIUS
            },
            "CTkLabel": {
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY]
            },
            "CTkEntry": {
                "fg_color": [cls.BG_INPUT, cls.BG_INPUT],
                "border_color": [cls.BORDER, cls.BORDER],
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY],
                "placeholder_text_color": [cls.TEXT_MUTED, cls.TEXT_MUTED]
            },
            "CTkProgressBar": {
                "fg_color": [cls.BG_DARK, cls.BG_DARK],
                "progress_color": [cls.PURPLE, cls.PURPLE],
                "corner_radius": 6
            },
            "CTkSwitch": {
                "fg_color": [cls.BG_DARK, cls.BG_DARK],
                "progress_color": [cls.PURPLE, cls.PURPLE],
                "button_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY],
                "button_hover_color": [cls.PURPLE_LIGHT, cls.PURPLE_LIGHT]
            },
            "CTkOptionMenu": {
                "fg_color": [cls.BG_INPUT, cls.BG_INPUT],
                "button_color": [cls.PURPLE, cls.PURPLE],
                "button_hover_color": [cls.PURPLE_HOVER, cls.PURPLE_HOVER],
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY]
            },
            "CTkTextbox": {
                "fg_color": [cls.BG_INPUT, cls.BG_INPUT],
                "border_color": [cls.BORDER, cls.BORDER],
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY],
                "scrollbar_button_color": [cls.SCROLLBAR, cls.SCROLLBAR],
                "scrollbar_button_hover_color": [
                    cls.SCROLLBAR_HOVER, cls.SCROLLBAR_HOVER
                ]
            }
        }

    @classmethod
    def font(cls, size=None, weight="normal"):
        """Retorna tupla de fuente para CTkinter."""
        s = size or cls.FONT_SIZE_BODY
        if weight == "bold":
            return (cls.FONT_FAMILY, s, "bold")
        return (cls.FONT_FAMILY, s)
