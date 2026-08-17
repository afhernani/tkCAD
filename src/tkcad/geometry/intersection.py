"""
Funciones de intersección geométrica para tkCAD.

Todas las funciones devuelven:
- None si no hay intersección
- Una tupla (Point, t, u) para intersecciones únicas
- Una lista de (Point, t, u) cuando hay múltiples intersecciones
"""

import math
from ..core import Point
from .utils import EPS


def line_line_intersection(a: Point, b: Point, c: Point, d: Point):
    """
    Intersección entre dos segmentos de línea.
    
    Args:
        a, b: Extremos del primer segmento
        c, d: Extremos del segundo segmento
    
    Returns:
        (Point, t, u) donde t es el parámetro sobre AB y u sobre CD,
        o None si no se intersectan.
    """
    dx1 = b.x - a.x
    dy1 = b.y - a.y
    dx2 = d.x - c.x
    dy2 = d.y - c.y

    denom = dx1 * dy2 - dy1 * dx2
    if abs(denom) < EPS:
        return None  # Paralelas o colineales

    t = ((c.x - a.x) * dy2 - (c.y - a.y) * dx2) / denom
    u = ((c.x - a.x) * dy1 - (c.y - a.y) * dx1) / denom

    if -EPS <= t <= 1 + EPS and -EPS <= u <= 1 + EPS:
        px = a.x + t * dx1
        py = a.y + t * dy1
        return (Point(px, py), t, u)

    return None


def line_line_intersection_infinite(a: Point, b: Point, c: Point, d: Point):
    """
    Intersección entre dos RECTAS infinitas (no segmentos).
    
    Args:
        a, b: Dos puntos que definen la primera recta
        c, d: Dos puntos que definen la segunda recta
    
    Returns:
        (Point, t, u) donde t y u son parámetros sobre cada recta,
        o None si son paralelas.
        A diferencia de line_line_intersection, NO restringe t y u a [0,1].
    """
    dx1 = b.x - a.x
    dy1 = b.y - a.y
    dx2 = d.x - c.x
    dy2 = d.y - c.y

    denom = dx1 * dy2 - dy1 * dx2
    if abs(denom) < EPS:
        return None  # Paralelas o colineales

    t = ((c.x - a.x) * dy2 - (c.y - a.y) * dx2) / denom
    u = ((c.x - a.x) * dy1 - (c.y - a.y) * dx1) / denom

    px = a.x + t * dx1
    py = a.y + t * dy1
    return (Point(px, py), t, u)


def line_circle_intersection(a: Point, b: Point, center: Point, radius: float):
    """
    Intersección entre un segmento de línea y un círculo.
    
    Args:
        a, b: Extremos del segmento
        center: Centro del círculo
        radius: Radio del círculo
    
    Returns:
        Lista de tuplas (Point, t) donde t es el parámetro sobre AB.
        Lista vacía si no hay intersección.
    """
    dx = b.x - a.x
    dy = b.y - a.y

    # Vector del centro al punto a
    fx = a.x - center.x
    fy = a.y - center.y

    # Ecuación cuadrática: |a + t*d - center|² = r²
    # (dx² + dy²)t² + 2(fx*dx + fy*dy)t + (fx² + fy² - r²) = 0
    A = dx * dx + dy * dy
    B = 2 * (fx * dx + fy * dy)
    C = fx * fx + fy * fy - radius * radius

    if A < EPS:
        # Segmento degenerado (punto)
        dist_sq = fx * fx + fy * fy
        if abs(dist_sq - radius * radius) < EPS:
            return [(a, 0.0)]
        return []

    discriminant = B * B - 4 * A * C

    if discriminant < -EPS:
        return []  # No hay intersección

    results = []

    if abs(discriminant) < EPS:
        # Tangente: una intersección
        t = -B / (2 * A)
        if -EPS <= t <= 1 + EPS:
            px = a.x + t * dx
            py = a.y + t * dy
            results.append((Point(px, py), t))
    else:
        # Dos intersecciones
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-B - sqrt_disc) / (2 * A)
        t2 = (-B + sqrt_disc) / (2 * A)

        for t in (t1, t2):
            if -EPS <= t <= 1 + EPS:
                px = a.x + t * dx
                py = a.y + t * dy
                results.append((Point(px, py), t))

    return results


def circle_circle_intersection(c1: Point, r1: float, c2: Point, r2: float):
    """
    Intersección entre dos círculos.
    
    Args:
        c1, r1: Centro y radio del primer círculo
        c2, r2: Centro y radio del segundo círculo
    
    Returns:
        Lista de Point con los puntos de intersección.
        Lista vacía si no hay intersección.
    """
    dx = c2.x - c1.x
    dy = c2.y - c1.y
    d = math.sqrt(dx * dx + dy * dy)

    # Casos sin intersección
    if d < EPS:
        # Centros coincidentes
        return []  # Infinitas o ninguna, devolvemos vacía

    if d > r1 + r2 + EPS:
        return []  # Separados

    if d < abs(r1 - r2) - EPS:
        return []  # Uno dentro del otro

    # Distancia desde c1 hasta la línea de intersección
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)

    # Altura desde la línea de centros hasta los puntos de intersección
    h_sq = r1 * r1 - a * a
    if h_sq < -EPS:
        return []
    h = math.sqrt(max(0, h_sq))

    # Punto base sobre la línea de centros
    px = c1.x + a * dx / d
    py = c1.y + a * dy / d

    if h < EPS:
        # Tangentes: un punto
        return [Point(px, py)]

    # Dos puntos de intersección
    rx = -dy * (h / d)
    ry = dx * (h / d)

    return [
        Point(px + rx, py + ry),
        Point(px - rx, py - ry),
    ]


def line_arc_intersection(a: Point, b: Point, center: Point, radius: float,
                          start_angle: float, end_angle: float):
    """
    Intersección entre un segmento de línea y un arco.
    
    Args:
        a, b: Extremos del segmento
        center: Centro del arco
        radius: Radio del arco
        start_angle: Ángulo inicial en grados
        end_angle: Ángulo final en grados
    
    Returns:
        Lista de tuplas (Point, t) donde t es el parámetro sobre AB.
    """
    # Primero obtenemos intersecciones con el círculo completo
    circle_hits = line_circle_intersection(a, b, center, radius)

    # Filtramos solo las que están dentro del rango angular del arco
    results = []
    for point, t in circle_hits:
        angle = math.degrees(math.atan2(point.y - center.y, point.x - center.x))
        if _angle_in_arc(angle, start_angle, end_angle):
            results.append((point, t))

    return results


def arc_arc_intersection(c1: Point, r1: float, start1: float, end1: float,
                         c2: Point, r2: float, start2: float, end2: float):
    """
    Intersección entre dos arcos.
    
    Args:
        c1, r1, start1, end1: Centro, radio y ángulos del primer arco
        c2, r2, start2, end2: Centro, radio y ángulos del segundo arco
    
    Returns:
        Lista de Point con los puntos de intersección.
    """
    # Primero obtenemos intersecciones de los círculos completos
    circle_hits = circle_circle_intersection(c1, r1, c2, r2)

    # Filtramos los puntos que están en ambos arcos
    results = []
    for point in circle_hits:
        angle1 = math.degrees(math.atan2(point.y - c1.y, point.x - c1.x))
        angle2 = math.degrees(math.atan2(point.y - c2.y, point.x - c2.x))

        if _angle_in_arc(angle1, start1, end1) and _angle_in_arc(angle2, start2, end2):
            results.append(point)

    return results


def _angle_in_arc(angle: float, start: float, end: float) -> bool:
    """
    Verifica si un ángulo está dentro del rango de un arco.
    Maneja arcos que cruzan el límite de 0°/360°.
    
    Args:
        angle: Ángulo a verificar en grados
        start: Ángulo inicial del arco en grados
        end: Ángulo final del arco en grados
    
    Returns:
        True si el ángulo está dentro del arco.
    """
    # Normalizar todos los ángulos a [0, 360)
    angle = angle % 360
    start = start % 360
    end = end % 360

    if start <= end:
        # Arco normal (no cruza 0°)
        return start - EPS <= angle <= end + EPS
    else:
        # Arco que cruza 0° (ej: de 350° a 10°)
        return angle >= start - EPS or angle <= end + EPS