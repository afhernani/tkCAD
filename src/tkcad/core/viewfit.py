"""Cálculo de encuadre: ajusta un rectángulo de mundo a la pantalla."""


def fit_rect_to_view(min_x, min_y, max_x, max_y, width, height, margin=20):
    """
    Calcula (scale, pan_x, pan_y) para que el rectángulo de mundo
    quede centrado y ajustado en una pantalla de width×height.
    
    Usa la misma convención de transformación del canvas:
        x = (px - pan_x) * scale + margin
        y = height - ((py - pan_y) * scale + margin)
    """
    w = max(max_x - min_x, 1e-9)
    h = max(max_y - min_y, 1e-9)

    avail_w = max(width - 2 * margin, 1)
    avail_h = max(height - 2 * margin, 1)

    scale = min(avail_w / w, avail_h / h)
    scale = min(max(scale, 0.02), 50.0)

    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2

    pan_x = cx - (width / 2 - margin) / scale
    pan_y = cy - (height / 2 - margin) / scale

    return scale, pan_x, pan_y