import pytest

from tkcad.core.img_transform import world_to_pixel


def test_esquinas_caen_en_el_margen():
    bbox = (0, 0, 100, 100)
    # Esquina superior-izquierda del mundo (x=0, y=100)
    px, py = world_to_pixel(0, 100, bbox, 200, 200, 20)
    assert px == pytest.approx(20)
    assert py == pytest.approx(20)
    # Esquina inferior-derecha del mundo (x=100, y=0)
    px, py = world_to_pixel(100, 0, bbox, 200, 200, 20)
    assert px == pytest.approx(180)
    assert py == pytest.approx(180)


def test_centro_del_mundo_al_centro_de_la_imagen():
    bbox = (0, 0, 100, 100)
    px, py = world_to_pixel(50, 50, bbox, 200, 200, 20)
    assert px == pytest.approx(100)
    assert py == pytest.approx(100)


def test_y_invertida():
    bbox = (0, 0, 10, 10)
    _, py_arriba = world_to_pixel(5, 10, bbox, 100, 100, 10)
    _, py_abajo = world_to_pixel(5, 0, bbox, 100, 100, 10)
    assert py_arriba < py_abajo


def test_bbox_rectangular_queda_centrada():
    bbox = (0, 0, 100, 50)
    # escala manda el ancho (1.6); alto usado = 80 → off_y = 60
    px, py = world_to_pixel(0, 50, bbox, 200, 200, 20)
    assert px == pytest.approx(20)
    assert py == pytest.approx(60)