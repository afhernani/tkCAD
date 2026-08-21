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
    if t == "angular":                      # acotacion angular
        return angular_geometry(data)
    return radius_geometry(data["center"], data["p"])


def dimension_points(data):
    """Todos los puntos que ocupa la cota (para bbox/selección)."""
    if data["dim_type"] == "angular":
        g = angular_geometry(data)
        pts = [data["vertex"], data["p1"], data["p2"], g["text_point"]]
        pts.extend(g["arc_points"])
        return pts
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


def resolve_assoc(data, entity):
    """
    Resuelve los puntos de una cota asociativa a partir de la entidad
    referenciada.
    
    Args:
        data: dict de datos de la cota (con assoc_kind y opcionalmente
              assoc_angle)
        entity: entidad referenciada (Entity)
    
    Returns:
        dict con los puntos resueltos para actualizar en data,
        o None si el tipo de asociación no aplica.
    """
    kind = data.get("assoc_kind")

    # Línea → sus extremos son los puntos de la cota
    if kind == "line" and entity.kind == "line":
        return {"p1": entity.data["start"], "p2": entity.data["end"]}

    # Radio de círculo/arco → centro + punto al ángulo guardado
    if kind == "radius" and entity.kind in ("circle", "arc"):
        center = entity.data["center"]
        r = entity.data["radius"]
        ang = math.radians(data.get("assoc_angle", 0.0))
        p = Point(
            center.x + r * math.cos(ang),
            center.y + r * math.sin(ang),
        )
        return {"center": center, "p": p}

    return None


def dimension_text_position(data):
    """Posición del texto = punto medio de la línea de cota + text_offset."""
    g = dimension_geometry(data)
    off = data.get("text_offset") or Point(0, 0)
    return Point(g["text_point"].x + off.x, g["text_point"].y + off.y)


def dimension_text_height(data):
    """Altura del texto de la cota (unidades de mundo)."""
    return float(data.get("text_height", 2.5))


def detach_assoc(data):
    """Convierte una cota asociativa en libre (elimina la referencia)."""
    data.pop("assoc_entity_id", None)
    data.pop("assoc_kind", None)
    return data

def angular_measure(vertex, p1, p2):
    """
    Ángulo en grados [0, 360) barrido en sentido antihorario
    desde el rayo vertex→p1 hasta el rayo vertex→p2.
    """
    a1 = math.degrees(math.atan2(p1.y - vertex.y, p1.x - vertex.x)) % 360.0
    a2 = math.degrees(math.atan2(p2.y - vertex.y, p2.x - vertex.x)) % 360.0
    return (a2 - a1) % 360.0


def angular_geometry(data):
    """Geometría completa de una cota angular."""
    vertex = data["vertex"]
    p1 = data["p1"]
    p2 = data["p2"]
    radius = float(data.get("radius", 15.0))

    a1 = math.degrees(math.atan2(p1.y - vertex.y, p1.x - vertex.x)) % 360.0
    extent = angular_measure(vertex, p1, p2)

    r1 = math.radians(a1)
    r2 = math.radians(a1 + extent)
    arc_start = Point(vertex.x + radius * math.cos(r1),
                      vertex.y + radius * math.sin(r1))
    arc_end = Point(vertex.x + radius * math.cos(r2),
                    vertex.y + radius * math.sin(r2))

    # Arco muestreado (para render y bbox)
    n = 32
    arc_points = []
    for i in range(n + 1):
        t = math.radians(a1 + extent * i / n)
        arc_points.append(Point(vertex.x + radius * math.cos(t),
                                vertex.y + radius * math.sin(t)))

    # Texto en el punto medio del arco
    mid = math.radians(a1 + extent / 2.0)
    text_point = Point(vertex.x + radius * math.cos(mid),
                       vertex.y + radius * math.sin(mid))

    return {
        "vertex": vertex,
        "radius": radius,
        "a1": a1,
        "extent": extent,
        "arc_start": arc_start,
        "arc_end": arc_end,
        "arc_points": arc_points,
        "text_point": text_point,
        "value": extent,
    }


def angular_text_position(data):
    """Posición del texto angular: punto medio del arco, empujado hacia fuera."""
    g = angular_geometry(data)
    mid = math.radians(g["a1"] + g["extent"] / 2.0)
    r = g["radius"] + 3.0 * dimension_text_height(data)
    v = g["vertex"]
    base = Point(v.x + r * math.cos(mid), v.y + r * math.sin(mid))
    off = data.get("text_offset") or Point(0, 0)
    return Point(base.x + off.x, base.y + off.y)

def angular_ray_ends(data):
    """Extremos de las líneas de extensión: p1/p2, extendidos
    como mínimo hasta el radio del arco."""
    g = angular_geometry(data)
    v = g["vertex"]
    ends = []
    for key in ("p1", "p2"):
        t = data[key]
        dx = t.x - v.x
        dy = t.y - v.y
        d = math.hypot(dx, dy)
        if d < 1e-9:
            ends.append(Point(v.x, v.y))
            continue
        L = max(d, g["radius"])
        ends.append(Point(v.x + dx / d * L, v.y + dy / d * L))
    return ends


def lines_intersection(a1, a2, b1, b2):
    """Intersección de las rectas (a1-a2) y (b1-b2). None si paralelas."""
    d1x, d1y = a2.x - a1.x, a2.y - a1.y
    d2x, d2y = b2.x - b1.x, b2.y - b1.y
    den = d1x * d2y - d1y * d2x
    if abs(den) < 1e-12:
        return None
    t = ((b1.x - a1.x) * d2y - (b1.y - a1.y) * d2x) / den
    return Point(a1.x + t * d1x, a1.y + t * d1y)


def refresh_angular_assoc(line_a, line_b, dim):
    """Recalcula vertex/p1/p2 de una cota angular desde sus DOS líneas.
    Devuelve True si la actualizó."""
    if line_a.kind != "line" or line_b.kind != "line":
        return False
    a1, a2 = line_a.data["start"], line_a.data["end"]
    b1, b2 = line_b.data["start"], line_b.data["end"]
    v = lines_intersection(a1, a2, b1, b2)
    if v is None:
        return False                      # paralelas → no se toca

    # rayo de cada línea = el extremo más lejano al vértice
    p1 = a1 if math.hypot(a1.x - v.x, a1.y - v.y) >= \
        math.hypot(a2.x - v.x, a2.y - v.y) else a2
    p2 = b1 if math.hypot(b1.x - v.x, b1.y - v.y) >= \
        math.hypot(b2.x - v.x, b2.y - v.y) else b2

    dim.data["vertex"] = Point(v.x, v.y)
    dim.data["p1"] = Point(p1.x, p1.y)
    dim.data["p2"] = Point(p2.x, p2.y)
    return True