"""CloudVault System Tray - Integracion con la bandeja del sistema.

Proporciona icono en la bandeja del sistema con menu contextual,
usando pystray para compatibilidad con Windows.
"""

import threading
import os
from typing import Optional, Callable, Dict

try:
    import pystray
    from pystray import MenuItem, Menu
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

try:
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class TrayIcon:
    """Icono de bandeja del sistema para CloudVault."""

    def __init__(self, on_show: Optional[Callable] = None,
                 on_start: Optional[Callable] = None,
                 on_stop: Optional[Callable] = None,
                 on_sync: Optional[Callable] = None,
                 on_exit: Optional[Callable] = None):
        """Inicializa el icono de bandeja.

        Args:
            on_show: Callback para mostrar la ventana principal
            on_start: Callback para iniciar servicios
            on_stop: Callback para detener servicios
            on_sync: Callback para sincronizar
            on_exit: Callback para salir de la aplicacion
        """
        self.on_show = on_show
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_sync = on_sync
        self.on_exit = on_exit
        self._icon = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def _create_icon_image(self, size: int = 64):
        """Crea la imagen del icono de nube programaticamente.

        Args:
            size: Tamano del icono en pixeles

        Returns:
            Imagen PIL con el icono de nube morado
        """
        if not PILLOW_AVAILABLE:
            return None

        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Color morado del tema
        purple = (139, 92, 246, 255)  # #8B5CF6

        # Dibujar nube usando elipses
        cx, cy = size // 2, size // 2 + 4
        r = size // 4

        # Cuerpo principal de la nube
        draw.ellipse(
            [cx - r, cy - r // 2, cx + r, cy + r],
            fill=purple
        )
        # Parte izquierda
        draw.ellipse(
            [cx - r - r // 2, cy - r // 4, cx - r // 4, cy + r],
            fill=purple
        )
        # Parte derecha
        draw.ellipse(
            [cx + r // 4, cy - r // 4, cx + r + r // 2, cy + r],
            fill=purple
        )
        # Parte superior
        draw.ellipse(
            [cx - r // 2, cy - r, cx + r // 2, cy + r // 4],
            fill=purple
        )
        # Parte superior derecha
        draw.ellipse(
            [cx, cy - r + r // 4, cx + r, cy + r // 4],
            fill=purple
        )
        # Base plana
        draw.rectangle(
            [cx - r - r // 2, cy + r // 2, cx + r + r // 2, cy + r],
            fill=purple
        )

        return image

    def _load_icon_file(self):
        """Intenta cargar el icono desde archivo .ico."""
        if not PILLOW_AVAILABLE:
            return None

        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets", "cloud.ico"
        )
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception:
                pass
        return None

    def _get_icon(self):
        """Obtiene la imagen del icono (archivo o generada)."""
        icon = self._load_icon_file()
        if icon is None:
            icon = self._create_icon_image()
        return icon

    def _build_menu(self):
        """Construye el menu contextual del tray."""
        if not PYSTRAY_AVAILABLE:
            return None

        return Menu(
            MenuItem(
                "Mostrar CloudVault",
                self._action_show,
                default=True
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Iniciar Servicios",
                self._action_start
            ),
            MenuItem(
                "Detener Servicios",
                self._action_stop
            ),
            MenuItem(
                "Sincronizar Ahora",
                self._action_sync
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Salir",
                self._action_exit
            ),
        )

    def start(self):
        """Inicia el icono de la bandeja del sistema."""
        if not PYSTRAY_AVAILABLE:
            return False

        icon_image = self._get_icon()
        if icon_image is None:
            return False

        self._icon = pystray.Icon(
            name="CloudVault",
            icon=icon_image,
            title="CloudVault - Nube Personal Cifrada",
            menu=self._build_menu()
        )

        self._running = True
        self._thread = threading.Thread(
            target=self._icon.run, daemon=True
        )
        self._thread.start()
        return True

    def stop(self):
        """Detiene y elimina el icono de la bandeja."""
        self._running = False
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def update_tooltip(self, text: str):
        """Actualiza el tooltip del icono."""
        if self._icon:
            self._icon.title = text

    def notify(self, title: str, message: str):
        """Muestra una notificacion desde la bandeja."""
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception:
                pass

    # --- Acciones del menu ---

    def _action_show(self, icon=None, item=None):
        """Accion: Mostrar ventana principal."""
        if self.on_show:
            self.on_show()

    def _action_start(self, icon=None, item=None):
        """Accion: Iniciar servicios."""
        if self.on_start:
            self.on_start()

    def _action_stop(self, icon=None, item=None):
        """Accion: Detener servicios."""
        if self.on_stop:
            self.on_stop()

    def _action_sync(self, icon=None, item=None):
        """Accion: Sincronizar ahora."""
        if self.on_sync:
            self.on_sync()

    def _action_exit(self, icon=None, item=None):
        """Accion: Salir de la aplicacion."""
        self.stop()
        if self.on_exit:
            self.on_exit()

    @property
    def is_available(self) -> bool:
        """Verifica si pystray esta disponible."""
        return PYSTRAY_AVAILABLE

    @property
    def is_running(self) -> bool:
        """Verifica si el icono esta activo."""
        return self._running and self._icon is not None
