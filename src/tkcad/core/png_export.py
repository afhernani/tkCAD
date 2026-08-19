"""Exportación del dibujo a PNG (raster) con Pillow."""

import math

from .dimension import dimension_geometry
from .img_transform import compute_image_fit
from .svg_export import _all_bbox   # reutilizamos el bbox del exportador SVG
from .spline import eval_cubic_spline


def export_png(entities, get_layer_color, path,
               width=800, height=600, margin=20, background="black"):
    """Exporta entidades a un archivo PNG. Returns (bool, str)."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False, "Pillow no está instalado. Ejecuta: pixi add pillow"

    bbox = _all_bbox(entities)
    if bbox is None:
        return False, "No hay nada que exportar."

    scale, off_x, off_y, min_x, max_y = compute_image_fit(
        bbox, width, height, margin,
    )

    def w2p(x, y):
        return ((x - min_x) * scale + off_x, (max_y - y) * scale + off_y)

    img = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(img)

    for entity in entities:
        color = get_layer_color(entity.layer) or "white"
        _draw_entity(draw, entity, w2p, scale, color)

    try:
        img.save(str(path), "PNG")
    except Exception as ex:
        return False, f"Error al guardar PNG: {ex}"
    return True, f"PNG exportado a: {path}"


# ============================================================
# Dibujo por entidad
# ============================================================

def _draw_entity(draw, entity, w2p, scale, color):
    d = entity.data
    k = entity.kind

    if k == "line":
        draw.line([w2p(d["start"].x, d["start"].y),
                   w2p(d["end"].x, d["end"].y)], fill=color, width=1)

    elif k in ("polyline", "polygon"):
        pts = [w2p(p.x, p.y) for p in d["points"]]
        if k == "polygon" and pts:
            pts.append(pts[0])
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=1)

    elif k == "circle":
        cx, cy = w2p(d["center"].x, d["center"].y)
        r = d["radius"] * scale
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color)

    elif k == "arc":
        # Muestreo (evita peleas con convenciones de ángulos de PIL)
        pts = _sampled_arc(d, w2p)
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=1)

    elif k == "ellipse":
        pts = _sampled_ellipse(d, w2p)
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=1)

    elif k == "text":
        x, y = w2p(d["position"].x, d["position"].y)
        fs = max(d["height"] * scale, 6)
        draw.text((x, y), d["content"], fill=color, font=_get_font(fs))

    elif k == "dimension":
        _draw_dimension(draw, d, w2p, scale, color)

    elif k == "spline":
        pts = [
            w2p(p.x, p.y)
            for p in eval_cubic_spline(
                d["points"],
                samples_per_segment=50,
                closed=d.get("closed", False),
            )
        ]
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=1)


def _sampled_arc(d, w2p, n=32):
    a0 = math.radians(d["start_angle"])
    a1 = math.radians(d["start_angle"] + d["extent"])
    pts = []
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        px = d["center"].x + d["radius"] * math.cos(t)
        py = d["center"].y + d["radius"] * math.sin(t)
        pts.append(w2p(px, py))
    return pts


def _sampled_ellipse(d, w2p, n=64):
    rot = math.radians(d.get("rotation", 0.0))
    cr, sr = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        ex = d["radius_x"] * math.cos(t)
        ey = d["radius_y"] * math.sin(t)
        wx = d["center"].x + ex * cr - ey * sr
        wy = d["center"].y + ex * sr + ey * cr
        pts.append(w2p(wx, wy))
    return pts


def _draw_dimension(draw, d, w2p, scale, color):
    g = dimension_geometry(d)

    for ext in (g["ext1"], g["ext2"]):
        if ext is None:
            continue
        a, b = ext
        draw.line([w2p(a.x, a.y), w2p(b.x, b.y)], fill=color, width=1)

    draw.line([w2p(g["dim_start"].x, g["dim_start"].y),
               w2p(g["dim_end"].x, g["dim_end"].y)], fill=color, width=1)

    tx, ty = w2p(g["text_point"].x, g["text_point"].y)
    fs = max(2.5 * scale, 6)
    prefix = {"radius": "R", "diameter": "Ø"}.get(d["dim_type"], "")
    draw.text((tx, ty - fs), f"{prefix}{g['value']:.2f}",
              fill=color, font=_get_font(fs))


def _get_font(fs):
    from PIL import ImageFont
    try:
        return ImageFont.truetype("arial.ttf", int(fs))
    except Exception:
        try:
            return ImageFont.load_default(int(fs))   # Pillow >= 10.1
        except Exception:
            return ImageFont.load_default()