"""Generador de icono de CloudVault.

Genera un archivo cloud.ico con una nube morada (#8B5CF6)
sobre fondo transparente en multiples tamanos (32x32, 48x48, 256x256).

Uso:
    python generate_icon.py

Requiere: Pillow >= 10.0.0
"""

import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Pillow no esta instalado.")
    print("Instala con: pip install Pillow>=10.0.0")
    sys.exit(1)


# Color principal - Morado CloudVault
PURPLE = (139, 92, 246, 255)  # #8B5CF6
PURPLE_DARK = (109, 40, 217, 255)  # #6D28D9
TRANSPARENT = (0, 0, 0, 0)


def draw_cloud(draw, size, color=PURPLE):
    """Dibuja una forma de nube en el canvas.

    Args:
        draw: ImageDraw object
        size: Tamano del canvas (cuadrado)
        color: Color RGBA de la nube
    """
    # Calcular proporciones relativas al tamano
    margin = size * 0.1
    w = size - 2 * margin
    h = w * 0.6

    # Centro vertical desplazado un poco hacia abajo
    cx = size / 2
    cy = size / 2 + size * 0.05

    # Radios de las elipses que forman la nube
    r_main = w * 0.22
    r_left = w * 0.18
    r_right = w * 0.20
    r_top = w * 0.16

    # Parte central (elipse principal)
    draw.ellipse(
        [cx - r_main, cy - r_main * 0.6,
         cx + r_main, cy + r_main * 0.8],
        fill=color
    )

    # Parte izquierda
    left_cx = cx - w * 0.22
    draw.ellipse(
        [left_cx - r_left, cy - r_left * 0.3,
         left_cx + r_left, cy + r_left * 0.9],
        fill=color
    )

    # Parte derecha
    right_cx = cx + w * 0.22
    draw.ellipse(
        [right_cx - r_right, cy - r_right * 0.4,
         right_cx + r_right, cy + r_right * 0.8],
        fill=color
    )

    # Parte superior izquierda
    top_left_cx = cx - w * 0.08
    top_left_cy = cy - h * 0.35
    draw.ellipse(
        [top_left_cx - r_top, top_left_cy - r_top,
         top_left_cx + r_top, top_left_cy + r_top],
        fill=color
    )

    # Parte superior derecha (mas grande)
    top_right_cx = cx + w * 0.12
    top_right_cy = cy - h * 0.28
    r_top_r = r_top * 1.2
    draw.ellipse(
        [top_right_cx - r_top_r, top_right_cy - r_top_r,
         top_right_cx + r_top_r, top_right_cy + r_top_r],
        fill=color
    )

    # Base plana para unir las partes inferiores
    base_top = cy + r_main * 0.2
    base_bottom = cy + r_main * 0.7
    draw.rectangle(
        [left_cx - r_left * 0.5, base_top,
         right_cx + r_right * 0.5, base_bottom],
        fill=color
    )


def generate_icon(output_path=None):
    """Genera el archivo cloud.ico con multiples tamanos.

    Args:
        output_path: Ruta de salida. Si es None, usa el directorio actual.

    Returns:
        Ruta al archivo generado.
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "cloud.ico"
        )

    # Tamanos de icono para Windows
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), TRANSPARENT)
        draw = ImageDraw.Draw(img)
        draw_cloud(draw, size, PURPLE)
        images.append(img)

    # Guardar como .ico con multiples tamanos
    # El primer tamano en la lista sera el principal
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )

    print(f"Icono generado: {output_path}")
    print(f"Tamanos incluidos: {', '.join(f'{s}x{s}' for s in sizes)}")
    return output_path


def generate_png(output_path=None, size=512):
    """Genera una version PNG de alta resolucion del icono.

    Args:
        output_path: Ruta de salida
        size: Tamano en pixeles

    Returns:
        Ruta al archivo generado.
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "cloud.png"
        )

    img = Image.new("RGBA", (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(img)
    draw_cloud(draw, size, PURPLE)
    img.save(output_path, format="PNG")

    print(f"PNG generado: {output_path} ({size}x{size})")
    return output_path


if __name__ == "__main__":
    print("CloudVault - Generador de Icono")
    print("=" * 40)
    generate_icon()
    generate_png()
    print("\nListo!")
