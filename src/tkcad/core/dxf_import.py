"""Importación de DXF (ezdxf) a entidades tkCAD."""
import math

import ezdxf

from .point import Point


def _p(v):
    return Point(float(v.x), float(v.y))


def convert_entity(e):
    """Convierte una entidad ezdxf en lista de (kind, data, layer)."""
    t = e.dxftype()
    layer = str(getattr(e.dxf, "layer", "0") or "0")

    if t == "LINE":
        return [("line", {"start": _p(e.dxf.start),
                          "end": _p(e.dxf.end)}, layer)]

    if t == "CIRCLE":
        return [("circle", {"center": _p(e.dxf.center),
                            "radius": float(e.dxf.radius)}, layer)]

    if t == "ARC":
        ext = (float(e.dxf.end_angle) - float(e.dxf.start_angle)) % 360.0
        return [("arc", {"center": _p(e.dxf.center),
                         "radius": float(e.dxf.radius),
                         "start_angle": float(e.dxf.start_angle),
                         "extent": ext}, layer)]

    if t == "LWPOLYLINE":
        pts = [Point(float(x), float(y))
               for x, y in e.get_points(format="xy")]
        if len(pts) < 2:
            return []
        kind = "polygon" if getattr(e, "closed", False) and len(pts) >= 3 \
            else "polyline"
        return [(kind, {"points": pts}, layer)]

    if t == "POLYLINE":
        pts = [_p(v.dxf.location) for v in e.vertices]
        if len(pts) < 2:
            return []
        kind = "polygon" if e.is_closed and len(pts) >= 3 else "polyline"
        return [(kind, {"points": pts}, layer)]

    if t == "ELLIPSE":
        mx = float(e.dxf.major_axis.x)
        my = float(e.dxf.major_axis.y)
        rx = math.hypot(mx, my)
        ry = rx * float(e.dxf.ratio)
        rot = math.degrees(math.atan2(my, mx))
        return [("ellipse", {"center": _p(e.dxf.center),
                             "radius_x": rx, "radius_y": ry,
                             "rotation": rot}, layer)]

    if t == "SPLINE":
        pts = [_p(p) for p in e.control_points]
        if len(pts) < 2:
            return []
        return [("spline", {"points": pts, "closed": False}, layer)]

    if t == "TEXT":
        return [("text", {"position": _p(e.dxf.insert),
                          "height": float(e.dxf.height),
                          "content": str(e.dxf.text)}, layer)]

    if t == "MTEXT":
        try:
            content = e.plain_text()
        except Exception:
            content = e.text
        return [("text", {"position": _p(e.dxf.insert),
                          "height": float(e.dxf.char_height),
                          "content": str(content)}, layer)]

    if t == "DIMENSION":
        return _convert_dimension(e, layer)

    return []


def import_dxf(path):
    """Lee un DXF. Devuelve ([(kind, data, layer)], block_defs)."""
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    # --- Bloques del DXF → definiciones de nivel 2 ---
    block_defs = {}
    for block in doc.blocks:
        if block.name.startswith("*"):
            continue
        ents = []
        for e in block:
            ents.extend(convert_entity(e))
        if ents:
            block_defs[block.name] = {
                "base": Point(0.0, 0.0),
                "entities": ents,
                "radius": 10.0,   # el radio real lo calcula el app al fusionar
            }

    # --- Entidades del modelo ---
    out = []
    for e in msp:
        if e.dxftype() == "INSERT" and e.dxf.name in block_defs:
            out.append(("insert", {
                "name": e.dxf.name,
                "position": _p(e.dxf.insert),
                "rotation": float(getattr(e.dxf, "rotation", 0.0)),
                "scale": float(getattr(e.dxf, "xscale", 1.0)),
            }, str(getattr(e.dxf, "layer", "0") or "0")))
            continue
        out.extend(convert_entity(e))

    return out, block_defs

def _linear_offset(data, dimline):
    """Offset firmado de la cota lineal según el punto de la línea de cota.
    Convención: línea de cota = base + offset."""
    if data["dim_type"] == "linear_h":
        return dimline.y - max(data["p1"].y, data["p2"].y)
    if data["dim_type"] == "linear_v":
        return dimline.x - max(data["p1"].x, data["p2"].x)
    # aligned: distancia perpendicular firmada a la recta p1-p2
    p1, p2 = data["p1"], data["p2"]
    ux, uy = p2.x - p1.x, p2.y - p1.y
    L = math.hypot(ux, uy) or 1.0
    ux, uy = ux / L, uy / L
    wx, wy = dimline.x - p1.x, dimline.y - p1.y
    return wx * (-uy) + wy * ux


def _convert_dimension(e, layer):
    """Convierte un DIMENSION de DXF en nuestra cota (lineal/radio).
    Lee solo los atributos realmente presentes en el archivo."""
    try:
        attrs = e.dxfattribs()
        dt = int(attrs.get("dim_type", 0) or 0) & 7
        p1 = attrs.get("defpoint2")
        p2 = attrs.get("defpoint3")
        dimline = attrs.get("defpoint")
        tip = attrs.get("defpoint4")

        # ---------- radio / diámetro (lleva defpoint4) ----------
        if tip is not None and dimline is not None:
            t = _p(tip)
            if dt == 3:                       # diámetro → radio equivalente
                a = _p(dimline)
                center = Point((a.x + t.x) / 2.0, (a.y + t.y) / 2.0)
            else:                             # radio: defpoint = centro
                center = _p(dimline)
            return [("dimension", {
                "dim_type": "radius", "center": center, "p": t,
                "text_height": 2.5}, layer)]

        # ---------- lineal / alineada (lleva defpoint2 y 3) ----------
        if p1 is not None and p2 is not None:
            p1w, p2w = _p(p1), _p(p2)
            dimline_w = _p(dimline) if dimline is not None else p1w
            if dt == 1:
                dim_type = "aligned"
            else:
                ang = float(attrs.get("angle", 0.0) or 0.0) % 180.0
                dx = p2w.x - p1w.x
                dy = p2w.y - p1w.y
                if abs(ang) < 1e-6:
                    dim_type = "linear_h" if abs(dy) < 1e-9 else "aligned"
                elif abs(ang - 90.0) < 1e-6:
                    dim_type = "linear_v" if abs(dx) < 1e-9 else "aligned"
                else:
                    dim_type = "aligned"
            data = {"dim_type": dim_type, "p1": p1w, "p2": p2w,
                    "text_height": 2.5}
            data["offset"] = _linear_offset(data, dimline_w)
            return [("dimension", data, layer)]
    except Exception:
        return []   # cota no soportada → se ignora sin romper la importación
    return []