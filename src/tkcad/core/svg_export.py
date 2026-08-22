"""Exportación del dibujo a SVG (vectorial, sin dependencias)."""

import math

from .hatch import hatch_segments

from .dimension import (angular_geometry, angular_ray_ends, angular_text_position, dimension_geometry, dimension_points,
                        dimension_text_position, dimension_text_height)
from .img_transform import compute_image_fit
from .spline import eval_cubic_spline
from .text_layout import text_block_size, split_lines
from .blocks import expand_inserts


def export_svg(entities, get_layer_color, path,
               width=800, height=600, margin=20, background="black", block_defs=None):
    """
    Exporta entidades a un archivo SVG.
    
    Args:
        entities: lista de Entity
        get_layer_color: callable(nombre_capa) -> color o None
        path: ruta de salida
    """
    if block_defs:
        entities = expand_inserts(entities, block_defs)
    bbox = _all_bbox(entities)
    if bbox is None:
        return False, "No hay nada que exportar."

    scale, off_x, off_y, min_x, max_y = compute_image_fit(
        bbox, width, height, margin,
    )

    def w2p(x, y):
        return ((x - min_x) * scale + off_x, (max_y - y) * scale + off_y)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" '
        f'fill="{background}"/>',
    ]

    for entity in entities:
        color = get_layer_color(entity.layer) or "white"
        parts.extend(_entity_svg(entity, w2p, scale, color))

    parts.append("</svg>")

    with open(str(path), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return True, f"SVG exportado a: {path}"


# ============================================================
# Elementos SVG por entidad
# ============================================================

def _entity_svg(entity, w2p, scale, color):
    d = entity.data
    k = entity.kind
    sw = 1

    if k == "line":
        x1, y1 = w2p(d["start"].x, d["start"].y)
        x2, y2 = w2p(d["end"].x, d["end"].y)
        return [f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
                f'y2="{y2:.2f}" stroke="{color}" stroke-width="{sw}"/>']

    if k in ("polyline", "polygon"):
        pts = " ".join(
            f"{w2p(p.x, p.y)[0]:.2f},{w2p(p.x, p.y)[1]:.2f}"
            for p in d["points"]
        )
        tag = "polygon" if k == "polygon" else "polyline"
        return [f'<{tag} points="{pts}" fill="none" stroke="{color}" '
                f'stroke-width="{sw}"/>']

    if k == "circle":
        cx, cy = w2p(d["center"].x, d["center"].y)
        r = d["radius"] * scale
        return [f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                f'fill="none" stroke="{color}" stroke-width="{sw}"/>']

    if k == "arc":
        # Muestreo del arco a polilínea (robusto y simple)
        n = 32
        a0 = math.radians(d["start_angle"])
        a1 = math.radians(d["start_angle"] + d["extent"])
        pts = []
        for i in range(n + 1):
            t = a0 + (a1 - a0) * i / n
            px = d["center"].x + d["radius"] * math.cos(t)
            py = d["center"].y + d["radius"] * math.sin(t)
            x, y = w2p(px, py)
            pts.append(f"{x:.2f},{y:.2f}")
        return [f'<polyline points="{" ".join(pts)}" fill="none" '
                f'stroke="{color}" stroke-width="{sw}"/>']

    if k == "ellipse":
        cx, cy = w2p(d["center"].x, d["center"].y)
        rx = d["radius_x"] * scale
        ry = d["radius_y"] * scale
        rot = -float(d.get("rotation", 0.0))   # Y invertida → rotación opuesta
        return [f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" '
                f'ry="{ry:.2f}" fill="none" stroke="{color}" '
                f'stroke-width="{sw}" '
                f'transform="rotate({rot:.2f} {cx:.2f} {cy:.2f})"/>']

    if k == "text":
        from .text_layout import split_lines
        x, y = w2p(d["position"].x, d["position"].y)
        fs = max(d["height"] * scale, 4)
        line_h = fs *1.4
        lines = split_lines(d["content"])
        tspans = []
        for i, line in enumerate(lines):
            dy = i * line_h
            tspans.append(
                f'<tspan x="{x:.2f}" y="{y + dy:.2f}">{_esc(line)}</tspan>'
            )
        return [
            f'<text fill="{color}" font-size="{fs:.2f}" text-anchor="middle">'
            + "".join(tspans) + "</text>"
        ]

    if k == "dimension":
        if d["dim_type"] == "angular":
            return _angular_svg(d, w2p, scale, color)
        return _dimension_svg(d, w2p, scale, color)

    if k == "spline":
        curve = eval_cubic_spline(
            d["points"],
            samples_per_segment=50,
            closed=d.get("closed", False),
        )
        pts = " ".join(
            f"{w2p(p.x, p.y)[0]:.2f},{w2p(p.x, p.y)[1]:.2f}" for p in curve
        )
        return [f'<polyline points="{pts}" fill="none" stroke="{color}" '
                f'stroke-width="{sw}"/>']

    if k == "hatch":
        out = []
        pts = d.get("points", [])
        if len(pts) >= 3:
            coords = " ".join(
                f"{w2p(p.x, p.y)[0]:.2f},{w2p(p.x, p.y)[1]:.2f}"
                for p in pts )
            if d.get("style", "solid") == "solid":
                out.append(f'<polygon points="{coords}" '
                           f'fill="{color}" stroke="none"/>')
            else:
                for a, b in hatch_segments(
                        pts, d.get("spacing", 5.0), d.get("angle", 45.0)):
                    x1, y1 = w2p(a.x, a.y)
                    x2, y2 = w2p(b.x, b.y)
                    out.append(
                        f'<line x1="{x1:.2f}" y1="{y1:.2f}" '
                        f'x2="{x2:.2f}" y2="{y2:.2f}" '
                        f'stroke="{color}" stroke-width="1"/>')
        return out

    return []


def _angular_svg(d, w2p, scale, color):
    g = angular_geometry(d)
    out = []

    vx, vy = w2p(g["vertex"].x, g["vertex"].y)
    for endp in angular_ray_ends(d):                 # ← mismo cambio
        ex, ey = w2p(endp.x, endp.y)
        out.append(f'<line x1="{vx:.2f}" y1="{vy:.2f}" x2="{ex:.2f}" '
                   f'y2="{ey:.2f}" stroke="{color}" stroke-width="1"/>')

    pts = " ".join(
        f"{w2p(p.x, p.y)[0]:.2f},{w2p(p.x, p.y)[1]:.2f}"
        for p in g["arc_points"]
    )
    out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" '
               f'stroke-width="1"/>')

    tp = angular_text_position(d)
    tx, ty = w2p(tp.x, tp.y)
    fs = max(dimension_text_height(d) * scale, 4)
    out.append(f'<text x="{tx:.2f}" y="{ty:.2f}" fill="{color}" '
               f'font-size="{fs:.2f}" text-anchor="middle">'
               f'{g["value"]:.1f}°</text>')
    return out

def _dimension_svg(d, w2p, scale, color):
    g = dimension_geometry(d)
    out = []

    for ext in (g["ext1"], g["ext2"]):
        if ext is None:
            continue
        a, b = ext
        x1, y1 = w2p(a.x, a.y)
        x2, y2 = w2p(b.x, b.y)
        out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
                   f'y2="{y2:.2f}" stroke="{color}" stroke-width="1"/>')

    x1, y1 = w2p(g["dim_start"].x, g["dim_start"].y)
    x2, y2 = w2p(g["dim_end"].x, g["dim_end"].y)
    out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
               f'y2="{y2:.2f}" stroke="{color}" stroke-width="1"/>')

    tp = dimension_text_position(d)          # respeta text_offset
    tx, ty = w2p(tp.x, tp.y)
    fs = max(dimension_text_height(d) * scale, 4)   # respeta text_height
    prefix = {"radius": "R", "diameter": "Ø"}.get(d["dim_type"], "")
    out.append(f'<text x="{tx:.2f}" y="{ty - fs:.2f}" fill="{color}" '
               f'font-size="{fs:.2f}" text-anchor="middle">'
               f'{prefix}{g["value"]:.2f}</text>')
    return out


# ============================================================
# Bounding box (para el encuadre)
# ============================================================

def _all_bbox(entities):
    xs, ys = [], []
    for e in entities:
        b = _entity_bbox(e)
        if b is None:
            continue
        xs += [b[0], b[2]]
        ys += [b[1], b[3]]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _entity_bbox(entity):
    d = entity.data
    k = entity.kind

    if k == "line":
        pts = [d["start"], d["end"]]
    elif k in ("polyline", "polygon"):
        pts = d["points"]
    elif k in ("circle", "arc"):
        c, r = d["center"], d["radius"]
        return (c.x - r, c.y - r, c.x + r, c.y + r)
    elif k == "ellipse":
        c = d["center"]
        m = max(d["radius_x"], d["radius_y"])
        return (c.x - m, c.y - m, c.x + m, c.y + m)
    elif k == "text":
        c, h = d["position"], d["height"]
        w = max(len(d["content"]), 1) * h * 0.6
        return (c.x - w / 2, c.y - h / 2, c.x + w / 2, c.y + h / 2)
    elif k == "dimension":
        pts = dimension_points(d)

    elif k == "spline":
        pts = eval_cubic_spline(
            d["points"],
            samples_per_segment=10,
            closed=d.get("closed", False),
        )
    elif k == "hatch":
        pts = d.get("points", [])
        if not pts:
            return None
    else:
        return None

    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _esc(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))