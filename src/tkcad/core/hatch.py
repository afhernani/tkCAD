"""Relleno rayado de polígonos: segmentos interiores paralelos."""
import math


def hatch_segments(points, spacing=5.0, angle=45.0):
    """Devuelve [(Point, Point)] con los segmentos de relleno
    de un polígono, en líneas paralelas separadas `spacing`,
    inclinadas `angle` grados."""
    if len(points) < 3 or spacing <= 1e-9:
        return []

    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)     # dirección de las líneas
    nx, ny = -dy, dx                      # normal (avance entre líneas)

    proj = [p.x * nx + p.y * ny for p in points]
    lo, hi = min(proj), max(proj)

    from .point import Point
    segs = []
    n = int((hi - lo) // spacing) + 1
    for i in range(n + 1):
        off = lo + i * spacing
        bx, by = off * nx, off * ny       # punto base de la línea
        ts = []
        m = len(points)
        for j in range(m):
            p = points[j]
            q = points[(j + 1) % m]
            ex, ey = q.x - p.x, q.y - p.y
            den = dy * ex - dx * ey
            if abs(den) < 1e-12:
                continue
            rx, ry = p.x - bx, p.y - by
            t = (-rx * ey + ex * ry) / den
            s = (dx * ry - dy * rx) / den
            if -1e-9 <= s <= 1 + 1e-9:
                ts.append(t)
        ts.sort()
        for k in range(0, len(ts) - 1, 2):
            segs.append((
                Point(bx + ts[k] * dx, by + ts[k] * dy),
                Point(bx + ts[k + 1] * dx, by + ts[k + 1] * dy),
            ))
    return segs