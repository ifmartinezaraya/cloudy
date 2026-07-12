"""CloudVault Splash Screen - Pantalla de bienvenida animada.

Muestra una pantalla morada con el icono de la nube y una
barra de progreso mientras la aplicacion se inicializa.
"""

import customtkinter as ctk
import threading
import time
from typing import Optional, Callable

try:
    from PIL import Image, ImageDraw, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from gui.core.theme import Theme


class SplashScreen(ctk.CTkToplevel):
    """Pantalla de splash con animacion de carga."""

    WIDTH = 480
    HEIGHT = 360

    def __init__(self, on_complete: Optional[Callable] = None):
        super().__init__()

        self.on_complete = on_complete
        self._progress = 0.0
        self._status_text = "Iniciando CloudVault..."
        self._steps_done = 0
        self._total_steps = 5

        # Configurar ventana
        self.overrideredirect(True)  # Sin barra de titulo
        self.configure(fg_color=Theme.BG_SIDEBAR)

        # Centrar en pantalla
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self.WIDTH) // 2
        y = (screen_h - self.HEIGHT) // 2
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        # Mantener encima
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.97)

        self._build_ui()
        self.after(200, self._start_loading)

    def _build_ui(self):
        """Construye la interfaz del splash."""
        # Frame principal con borde morado
        main_frame = ctk.CTkFrame(
            self, fg_color=Theme.BG_SIDEBAR,
            corner_radius=16,
            border_width=2,
            border_color=Theme.PURPLE
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Icono de nube grande
        self.cloud_label = ctk.CTkLabel(
            main_frame,
            text="\u2601",
            font=(Theme.FONT_FAMILY, 72),
            text_color=Theme.PURPLE
        )
        self.cloud_label.pack(pady=(40, 8))

        # Nombre de la app
        ctk.CTkLabel(
            main_frame,
            text="CloudVault",
            font=Theme.font(32, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(pady=(0, 4))

        # Subtitulo
        ctk.CTkLabel(
            main_frame,
            text="Nube Personal Cifrada",
            font=Theme.font(14),
            text_color=Theme.PURPLE_LIGHT
        ).pack(pady=(0, 24))

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            width=320, height=6,
            fg_color=Theme.BG_DARK,
            progress_color=Theme.PURPLE,
            corner_radius=3
        )
        self.progress_bar.pack(pady=(0, 12))
        self.progress_bar.set(0)

        # Texto de estado
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Iniciando CloudVault...",
            font=Theme.font(Theme.FONT_SIZE_SMALL),
            text_color=Theme.TEXT_MUTED
        )
        self.status_label.pack(pady=(0, 8))

        # Version
        ctk.CTkLabel(
            main_frame,
            text="v1.0.0",
            font=Theme.font(Theme.FONT_SIZE_CAPTION),
            text_color=Theme.TEXT_MUTED
        ).pack(side="bottom", pady=(0, 16))

    def _start_loading(self):
        """Inicia la secuencia de carga."""
        thread = threading.Thread(target=self._loading_sequence, daemon=True)
        thread.start()

    def _loading_sequence(self):
        """Secuencia de pasos de carga con animacion."""
        steps = [
            ("Verificando configuracion...", 0.15),
            ("Cargando tema visual...", 0.30),
            ("Conectando con Docker...", 0.55),
            ("Inicializando monitor de estado...", 0.75),
            ("Preparando interfaz...", 0.95),
        ]

        for text, target_progress in steps:
            self._update_status(text)
            # Animar la barra gradualmente
            current = self._progress
            step_size = (target_progress - current) / 20
            for i in range(20):
                self._progress = current + step_size * (i + 1)
                try:
                    self.after(0, lambda p=self._progress: self.progress_bar.set(p))
                except Exception:
                    return
                time.sleep(0.03)
            time.sleep(0.2)

        # Finalizar
        self._update_status("Listo!")
        try:
            self.after(0, lambda: self.progress_bar.set(1.0))
        except Exception:
            return
        time.sleep(0.5)

        # Llamar callback de completado
        try:
            self.after(0, self._finish)
        except Exception:
            pass

    def _update_status(self, text: str):
        """Actualiza el texto de estado de forma thread-safe."""
        try:
            self.after(0, lambda: self.status_label.configure(text=text))
        except Exception:
            pass

    def _finish(self):
        """Cierra el splash y notifica que esta listo."""
        if self.on_complete:
            self.on_complete()
        self.destroy()


def show_splash(on_complete: Callable):
    """Muestra el splash screen y ejecuta callback al completar.

    Args:
        on_complete: Funcion a ejecutar cuando el splash termina.
    """
    # Crear ventana raiz temporal invisible para el splash
    root = ctk.CTk()
    root.withdraw()

    splash = SplashScreen(on_complete=lambda: _finish_splash(root, on_complete))
    root.mainloop()


def _finish_splash(root, callback):
    """Cierra la raiz temporal y ejecuta el callback."""
    root.quit()
    root.destroy()
    callback()
