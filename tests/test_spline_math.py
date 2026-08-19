import pytest

from tkcad.core import Point
from tkcad.core.spline import eval_cubic_spline


def test_pasa_por_los_puntos_de_control():
    pts = [Point(0, 0), Point(10, 5), Point(20, 0), Point(30, 5)]
    curve = eval_cubic_spline(pts, samples_per_segment=10)
    for i, p in enumerate(pts):
        q = curve[i * 10]
        assert q.x == pytest.approx(p.x)
        assert q.y == pytest.approx(p.y)


def test_dos_puntos_es_una_recta():
    curve = eval_cubic_spline([Point(0, 0), Point(10, 0)], 10)
    for q in curve:
        assert q.y == pytest.approx(0)


def test_puntos_colineales_dan_recta():
    pts = [Point(0, 0), Point(5, 5), Point(10, 10)]
    curve = eval_cubic_spline(pts, 10)
    for q in curve:
        assert q.y == pytest.approx(q.x)


def test_cerrada_vuelve_al_inicio():
    pts = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
    curve = eval_cubic_spline(pts, 10, closed=True)
    assert curve[0].x == pytest.approx(curve[-1].x)
    assert curve[0].y == pytest.approx(curve[-1].y)


def test_duplicados_consecutivos_no_explotan():
    pts = [Point(0, 0), Point(0, 0), Point(10, 5)]
    curve = eval_cubic_spline(pts, 10)
    assert len(curve) >= 2