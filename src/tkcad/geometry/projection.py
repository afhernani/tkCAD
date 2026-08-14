from ..core import Point
from .utils import EPS

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