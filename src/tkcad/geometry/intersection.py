from ..core import Point
from .utils import EPS

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

