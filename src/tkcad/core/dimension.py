"""Geometría pura de cotas (dimensiones). Sin dependencias de UI."""

import math

from . import Point


def measure_dimension(dim_type, p1=None, p2=None, center=None, p=None):
    """Devuelve el valor numérico que mide la cota."""
    if dim_type == "linear_h":
        return abs(p2.x - p1.x)
    if dim_type == "linear_v":
        return abs(p2.y - p1.y)
    if dim_type == "aligned":
        return math.hypot(p2.x - p1.x, p2.y - p1.y)
    if dim_type in ("radius", "diameter"):
        r = math.hypot(p.x - center.x, p.y - center.y)
        return r if dim_type == "radius" else 2.0 * r
    return 0.0


def linear_geometry(p1, p2, offset, horizontal):
    """Geometría de cota lineal horizontal o vertical."""
    if horizontal:
        dim_y = max(p1.y, p2.y) + offset
        dim_start = Point(p1.x, dim_y)
        dim_end = Point(p2.x, dim_y)
    else:
        dim_x = max(p1.x, p2.x) + offset
        dim_start = Point(dim_x, p1.y)
        dim_end = Point(dim_x, p2.y)

    text_point = Point(
        (dim_start.x + dim_end.x) / 2,
        (dim_start.y + dim_end.y) / 2,
    )
    return {
        "dim_start": dim_start, "dim_end": dim_end,
        "ext1": (p1, dim_start), "ext2": (p2, dim_end),
        "text_point": text_point,
        "value": measure_dimension(
            "linear_h" if horizontal else "linear_v", p1, p2
        ),
    }


def aligned_geometry(p1, p2, offset):
    """Cota alineada: línea de cota paralela a p1→p2."""
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    length = math.hypot(dx, dy)
    ux, uy = (dx / length, dy / length) if length > 1e-9 else (1.0, 0.0)
    nx, ny = -uy, ux                      # vector perpendicular

    dim_start = Point(p1.x + nx * offset, p1.y + ny * offset)
    dim_end = Point(p2.x + nx * offset, p2.y + ny * offset)
    text_point = Point(
        (dim_start.x + dim_end.x) / 2,
        (dim_start.y + dim_end.y) / 2,
    )
    return {
        "dim_start": dim_start, "dim_end": dim_end,
        "ext1": (p1, dim_start), "ext2": (p2, dim_end),
        "text_point": text_point,
        "value": length,
    }


def radius_geometry(center, p):
    """Cota de radio: línea centro→punto."""
    return {
        "dim_start": center, "dim_end": p,
        "ext1": None, "ext2": None,
        "text_point": Point((center.x + p.x) / 2, (center.y + p.y) / 2),
        "value": math.hypot(p.x - center.x, p.y - center.y),
    }


def dimension_geometry(data):
    """Dispatch según el tipo de cota."""
    t = data["dim_type"]
    offset = data.get("offset", 10.0)
    if t in ("linear_h", "linear_v"):
        return linear_geometry(data["p1"], data["p2"], offset, t == "linear_h")
    if t == "aligned":
        return aligned_geometry(data["p1"], data["p2"], offset)
    return radius_geometry(data["center"], data["p"])


def dimension_points(data):
    """Todos los puntos que ocupa la cota (para bbox/selección)."""
    g = dimension_geometry(data)
    pts = [g["dim_start"], g["dim_end"], g["text_point"]]
    for ext in (g["ext1"], g["ext2"]):
        if ext:
            pts.extend(ext)
    for key in ("p1", "p2", "center", "p"):
        if key in data:
            pts.append(data[key])
    return pts


def offset_from_point(data, p):
    """Calcula el offset que haría pasar la línea de cota por el punto p."""
    t = data["dim_type"]

    if t == "linear_h":
        return p.y - max(data["p1"].y, data["p2"].y)

    if t == "linear_v":
        return p.x - max(data["p1"].x, data["p2"].x)

    if t == "aligned":
        p1, p2 = data["p1"], data["p2"]
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        length = math.hypot(dx, dy)
        if length < 1e-9:
            return data.get("offset", 10.0)
        nx, ny = -dy / length, dx / length
        return (p.x - p1.x) * nx + (p.y - p1.y) * ny

    return data.get("offset", 10.0)
