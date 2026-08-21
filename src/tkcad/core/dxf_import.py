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