"""Utilidades puras para bloques de nivel 2 (definiciones + inserciones)."""
import copy
import math

from .point import Point


def transform_block_data(kind, data, base, position, rotation, scale):
    """Devuelve una copia de data transformada al mundo del insert."""
    a = math.radians(rotation)
    ca, sa = math.cos(a), math.sin(a)

    def xf(p):
        dx, dy = (p.x - base.x) * scale, (p.y - base.y) * scale
        return Point(position.x + dx * ca - dy * sa,
                     position.y + dx * sa + dy * ca)

    d = copy.deepcopy(data)
    if kind == "line":
        d["start"] = xf(d["start"])
        d["end"] = xf(d["end"])
    elif kind in ("polyline", "polygon", "spline"):
        d["points"] = [xf(p) for p in d["points"]]
    elif kind in ("circle", "arc"):
        d["center"] = xf(d["center"])
        d["radius"] = d["radius"] * scale
        if kind == "arc":
            d["start_angle"] = (d["start_angle"] + rotation) % 360.0
    elif kind == "ellipse":
        d["center"] = xf(d["center"])
        d["radius_x"] *= scale
        d["radius_y"] *= scale
        d["rotation"] = (d.get("rotation", 0.0) + rotation) % 360.0
    elif kind == "text":
        d["position"] = xf(d["position"])
        d["height"] = d["height"] * scale
    elif kind == "dimension":
        for key in ("p1", "p2", "center", "p", "vertex"):
            if key in d:
                d[key] = xf(d[key])
        d["offset"] = d.get("offset", 10.0) * scale
    return d


def block_world_entities(block_defs, insert_data):
    """Devuelve [(kind, data_mundo, layer)] para un data de insert."""
    defn = block_defs.get(insert_data["name"])
    if defn is None:
        return []
    base = defn["base"]
    return [
        (kind,
         transform_block_data(kind, data, base,
                              insert_data["position"],
                              insert_data.get("rotation", 0.0),
                              insert_data.get("scale", 1.0)),
         layer)
        for kind, data, layer in defn["entities"]
    ]