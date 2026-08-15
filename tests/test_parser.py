import pytest

from tkcad.core import Point, parse_number, parse_point


def test_parse_number_con_coma():
    assert parse_number("3,5") == 3.5


def test_parse_number_con_punto():
    assert parse_number("3.5") == 3.5


def test_parse_point_cartesiano_con_coma():
    assert parse_point("10,20") == Point(10.0, 20.0)


def test_parse_point_cartesiano_con_punto_y_coma():
    assert parse_point("10;20") == Point(10.0, 20.0)


def test_parse_point_relativo():
    base = Point(10.0, 10.0)
    assert parse_point("@5,-5", base) == Point(15.0, 5.0)


def test_parse_point_relativo_sin_base_da_error():
    with pytest.raises(ValueError):
        parse_point("@5,5")


def test_parse_point_polar_absoluto():
    p = parse_point("10<90")
    assert p.x == pytest.approx(0.0, abs=1e-9)
    assert p.y == pytest.approx(10.0, abs=1e-9)


def test_parse_point_polar_relativo():
    base = Point(5.0, 5.0)
    p = parse_point("@10<0", base)
    assert p.x == pytest.approx(15.0)
    assert p.y == pytest.approx(5.0)


def test_parse_point_vacio_da_error():
    with pytest.raises(ValueError):
        parse_point("")


def test_parse_point_mal_formado_da_error():
    with pytest.raises(ValueError):
        parse_point("10")