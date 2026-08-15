import pytest

from tkcad.core import Point
from tkcad.geometry import line_line_intersection, projection_param


def test_interseccion_de_dos_lineas():
    a, b = Point(0, 0), Point(10, 10)
    c, d = Point(0, 10), Point(10, 0)
    resultado = line_line_intersection(a, b, c, d)
    assert resultado is not None
    p, t, u = resultado
    assert p.x == pytest.approx(5.0)
    assert p.y == pytest.approx(5.0)
    assert t == pytest.approx(0.5)
    assert u == pytest.approx(0.5)


def test_lineas_paralelas_no_se_cortan():
    a, b = Point(0, 0), Point(10, 0)
    c, d = Point(0, 5), Point(10, 5)
    assert line_line_intersection(a, b, c, d) is None


def test_projection_param_en_extremos():
    a, b = Point(0, 0), Point(10, 0)
    assert projection_param(Point(0, 0), a, b) == pytest.approx(0.0)
    assert projection_param(Point(10, 0), a, b) == pytest.approx(1.0)


def test_projection_param_punto_medio():
    a, b = Point(0, 0), Point(10, 0)
    assert projection_param(Point(5, 3), a, b) == pytest.approx(0.5)


def test_projection_param_segmento_degenerado():
    a = Point(1, 1)
    assert projection_param(Point(5, 5), a, a) == 0.0