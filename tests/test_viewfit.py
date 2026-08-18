import pytest
from tkcad.core import fit_rect_to_view


def _sx(px, scale, pan_x, margin=20):
    return (px - pan_x) * scale + margin


def _sy(py, scale, pan_y, height, margin=20):
    return height - ((py - pan_y) * scale + margin)


def test_fit_rect_centra_el_rectangulo():
    scale, px, py = fit_rect_to_view(0, 0, 100, 100, 800, 600, 20)
    # El centro del rect (50,50) cae en el centro de pantalla (400,300)
    assert _sx(50, scale, px) == pytest.approx(400)
    assert _sy(50, scale, py, 600) == pytest.approx(300)


def test_fit_rect_respeta_margen():
    scale, px, py = fit_rect_to_view(0, 0, 100, 100, 800, 600, 20)
    xs = [_sx(0, scale, px), _sx(100, scale, px)]
    ys = [_sy(0, scale, py, 600), _sy(100, scale, py, 600)]
    assert min(xs) >= 20 - 1e-6
    assert max(xs) <= 800 - 20 + 1e-6
    assert min(ys) >= 20 - 1e-6
    assert max(ys) <= 600 - 20 + 1e-6


def test_fit_rect_escala_limitada_por_altura():
    # Rect cuadrado en pantalla no cuadrada: manda la altura
    scale, px, py = fit_rect_to_view(0, 0, 100, 100, 800, 600, 20)
    assert scale == pytest.approx(560 / 100)


def test_fit_rect_degenerado_no_explota():
    scale, px, py = fit_rect_to_view(5, 5, 5, 5, 800, 600, 20)
    assert scale > 0