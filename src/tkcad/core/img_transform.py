"""Transformación mundo→píxel para exportar imágenes (SVG/PNG).

Convención de imagen: origen arriba-izquierda, Y hacia abajo.
Convención de mundo: Y hacia arriba. Por eso se invierte Y.
"""


def compute_image_fit(bbox, width, height, margin=20):
    """
    Calcula (scale, off_x, off_y, min_x, max_y) para encuadrar `bbox`
    en una imagen de width×height con margen, centrando el dibujo.
    """
    min_x, min_y, max_x, max_y = bbox
    w = max(max_x - min_x, 1e-9)
    h = max(max_y - min_y, 1e-9)

    avail_w = max(width - 2 * margin, 1)
    avail_h = max(height - 2 * margin, 1)
    scale = min(avail_w / w, avail_h / h)

    # Centrar el dibujo en la imagen
    off_x = (width - w * scale) / 2
    off_y = (height - h * scale) / 2

    return scale, off_x, off_y, min_x, max_y


def world_to_pixel(x, y, bbox, width, height, margin=20):
    """Convierte coordenadas de mundo a píxeles de imagen (Y invertida)."""
    scale, off_x, off_y, min_x, max_y = compute_image_fit(
        bbox, width, height, margin,
    )
    px = (x - min_x) * scale + off_x
    py = (max_y - y) * scale + off_y
    return px, py