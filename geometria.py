# geometria.py

from core import Point


EPS = 1e-9


def line_line_intersection(a: Point, b: Point, c: Point, d: Point):
    """
    Calcula la intersección entre la recta AB y la recta CD.

    Devuelve:
        Point, t, u

    donde:
        Point = punto de intersección
        t = posición sobre AB:  A + t*(B-A)
        u = posición sobre CD:  C + u*(D-C)

    Si son paralelas, devuelve None.
    """
    rx = b.x - a.x
    ry = b.y - a.y

    sx = d.x - c.x
    sy = d.y - c.y

    cross = rx * sy - ry * sx

    if abs(cross) < EPS:
        return None

    qpx = c.x - a.x
    qpy = c.y - a.y

    t = (qpx * sy - qpy * sx) / cross
    u = (qpx * ry - qpy * rx) / cross

    x = a.x + t * rx
    y = a.y + t * ry

    return Point(x, y), t, u


def projection_param(p: Point, a: Point, b: Point) -> float:
    """
    Proyecta el punto P sobre la recta AB.

    Devuelve un parámetro t tal que:

        proyección = A + t*(B-A)

    t = 0 -> A
    t = 1 -> B
    t < 0 -> antes de A
    t > 1 -> después de B
    """
    vx = b.x - a.x
    vy = b.y - a.y

    denom = vx * vx + vy * vy

    if denom < EPS:
        return 0.0

    return ((p.x - a.x) * vx + (p.y - a.y) * vy) / denom