"""Spline cúbico natural paramétrico (pure Python, sin numpy).

Se parametriza por longitud de cuerda y se ajusta un spline cúbico
natural a X(t) y a Y(t) por separado. Así la curva puede tener
verticales, bucles y cualquier forma.
"""

import math

from . import Point


def chord_params(points):
    """Parámetros t acumulados por distancia entre puntos."""
    ts = [0.0]
    for i in range(1, len(points)):
        ts.append(ts[-1] + math.hypot(
            points[i].x - points[i - 1].x,
            points[i].y - points[i - 1].y,
        ))
    return ts


def _second_derivatives(ts, vs):
    """Resuelve el sistema tridiagonal (Thomas) para los M_i (segundas
    derivadas) con condición natural M_0 = M_n = 0."""
    n = len(ts) - 1
    if n < 2:
        return [0.0] * len(ts)

    a, b, c, d = [], [], [], []
    for i in range(1, n):
        h_prev = ts[i] - ts[i - 1]
        h_next = ts[i + 1] - ts[i]
        a.append(h_prev)
        b.append(2.0 * (h_prev + h_next))
        c.append(h_next)
        d.append(6.0 * ((vs[i + 1] - vs[i]) / h_next
                        - (vs[i] - vs[i - 1]) / h_prev))

    m = len(d)
    cp = [0.0] * m
    dp = [0.0] * m
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, m):
        denom = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / denom
        dp[i] = (d[i] - a[i] * dp[i - 1]) / denom

    sol = [0.0] * m
    sol[m - 1] = dp[m - 1]
    for i in range(m - 2, -1, -1):
        sol[i] = dp[i] - cp[i] * sol[i + 1]

    return [0.0] + sol + [0.0]


def _eval_segment(ts, vs, M, i, t):
    """Evalúa el spline en el segmento i, en el parámetro t."""
    h = ts[i + 1] - ts[i]
    a_ = (ts[i + 1] - t) / h
    b_ = (t - ts[i]) / h
    return (a_ * vs[i] + b_ * vs[i + 1]
            + ((a_ ** 3 - a_) * M[i] + (b_ ** 3 - b_) * M[i + 1])
            * (h * h) / 6.0)


def eval_cubic_spline(points, samples_per_segment=50, closed=False):
    """
    Devuelve la lista de Point de la curva evaluada.
    
    Args:
        points: puntos de control (mínimo 2)
        samples_per_segment: resolución por tramo
        closed: si True, cierra la curva volviendo al primer punto
    """
    pts = list(points)
    if closed and len(pts) >= 3:
        pts = pts + [pts[0]]

    # Elimina duplicados consecutivos (evita h=0)
    clean = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p.x - clean[-1].x, p.y - clean[-1].y) > 1e-9:
            clean.append(p)
    pts = clean

    if len(pts) < 2:
        return list(pts)

    if len(pts) == 2:
        out = []
        for j in range(samples_per_segment + 1):
            t = j / samples_per_segment
            out.append(Point(
                pts[0].x + (pts[1].x - pts[0].x) * t,
                pts[0].y + (pts[1].y - pts[0].y) * t,
            ))
        return out

    ts = chord_params(pts)
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    Mx = _second_derivatives(ts, xs)
    My = _second_derivatives(ts, ys)

    out = []
    for i in range(len(pts) - 1):
        for j in range(samples_per_segment):
            t = ts[i] + (ts[i + 1] - ts[i]) * j / samples_per_segment
            out.append(Point(
                _eval_segment(ts, xs, Mx, i, t),
                _eval_segment(ts, ys, My, i, t),
            ))
    out.append(Point(xs[-1], ys[-1]))
    return out