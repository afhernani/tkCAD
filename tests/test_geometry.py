import math
import pytest

from tkcad.core import Point
from tkcad.geometry import (
    line_line_intersection,
    line_line_intersection_infinite,
    line_circle_intersection,
    circle_circle_intersection,
    line_arc_intersection,
    projection_param,
)


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
    

def test_interseccion_infinita_fuera_de_segmentos():
    """Dos segmentos que NO se cruzan, pero sus rectas sí."""
    a, b = Point(-10, 0), Point(-2, 0)   # Segmento corto
    c, d = Point(0, -5), Point(0, 5)     # Segmento vertical
    resultado = line_line_intersection_infinite(a, b, c, d)
    assert resultado is not None
    p, t, u = resultado
    assert p.x == pytest.approx(0.0)
    assert p.y == pytest.approx(0.0)
    assert t == pytest.approx(1.25)      # Fuera del segmento AB
    assert u == pytest.approx(0.5)       # Dentro del segmento CD


def test_interseccion_infinita_paralelas():
    a, b = Point(0, 0), Point(10, 0)
    c, d = Point(0, 5), Point(10, 5)
    assert line_line_intersection_infinite(a, b, c, d) is None

# ============================================================
# INTERSECCIÓN LÍNEA-CÍRCULO
# ============================================================

def test_linea_cruza_circulo_en_dos_puntos():
    a, b = Point(-10, 0), Point(10, 0)
    center, radius = Point(0, 0), 5.0
    hits = line_circle_intersection(a, b, center, radius)
    assert len(hits) == 2
    # Verificar que los puntos están sobre el círculo
    for p, t in hits:
        dist = math.sqrt((p.x - center.x)**2 + (p.y - center.y)**2)
        assert dist == pytest.approx(radius, abs=1e-9)


def test_linea_tangente_a_circulo():
    a, b = Point(-10, 5), Point(10, 5)
    center, radius = Point(0, 0), 5.0
    hits = line_circle_intersection(a, b, center, radius)
    assert len(hits) == 1
    assert hits[0][0].x == pytest.approx(0.0, abs=1e-9)
    assert hits[0][0].y == pytest.approx(5.0, abs=1e-9)


def test_linea_no_toca_circulo():
    a, b = Point(-10, 10), Point(10, 10)
    center, radius = Point(0, 0), 5.0
    hits = line_circle_intersection(a, b, center, radius)
    assert len(hits) == 0


def test_segmento_corto_no_alcanza_circulo():
    a, b = Point(-10, 0), Point(-6, 0)  # No llega al círculo de radio 5
    center, radius = Point(0, 0), 5.0
    hits = line_circle_intersection(a, b, center, radius)
    assert len(hits) == 0


def test_segmento_dentro_del_circulo():
    a, b = Point(-2, 0), Point(2, 0)  # Completamente dentro
    center, radius = Point(0, 0), 5.0
    hits = line_circle_intersection(a, b, center, radius)
    assert len(hits) == 0  # No cruza el borde


# ============================================================
# INTERSECCIÓN CÍRCULO-CÍRCULO
# ============================================================

def test_dos_circulos_se_cruzan():
    c1, r1 = Point(0, 0), 5.0
    c2, r2 = Point(6, 0), 5.0
    hits = circle_circle_intersection(c1, r1, c2, r2)
    assert len(hits) == 2
    # Verificar simetría
    assert hits[0].x == pytest.approx(3.0, abs=1e-9)
    assert hits[1].x == pytest.approx(3.0, abs=1e-9)
    assert hits[0].y == pytest.approx(-hits[1].y, abs=1e-9)


def test_circulos_tangentes_exteriormente():
    c1, r1 = Point(0, 0), 5.0
    c2, r2 = Point(10, 0), 5.0
    hits = circle_circle_intersection(c1, r1, c2, r2)
    assert len(hits) == 1
    assert hits[0].x == pytest.approx(5.0, abs=1e-9)
    assert hits[0].y == pytest.approx(0.0, abs=1e-9)


def test_circulos_tangentes_interiormente():
    c1, r1 = Point(0, 0), 5.0
    c2, r2 = Point(2, 0), 3.0
    hits = circle_circle_intersection(c1, r1, c2, r2)
    assert len(hits) == 1
    assert hits[0].x == pytest.approx(5.0, abs=1e-9)


def test_circulos_separados():
    c1, r1 = Point(0, 0), 2.0
    c2, r2 = Point(10, 0), 2.0
    hits = circle_circle_intersection(c1, r1, c2, r2)
    assert len(hits) == 0


def test_circulo_dentro_de_otro():
    c1, r1 = Point(0, 0), 10.0
    c2, r2 = Point(1, 0), 2.0
    hits = circle_circle_intersection(c1, r1, c2, r2)
    assert len(hits) == 0


def test_circulos_concentricos():
    c1, r1 = Point(0, 0), 5.0
    c2, r2 = Point(0, 0), 3.0
    hits = circle_circle_intersection(c1, r1, c2, r2)
    assert len(hits) == 0


# ============================================================
# INTERSECCIÓN LÍNEA-ARCO
# ============================================================

def test_linea_cruza_arco():
    a, b = Point(-10, 0), Point(10, 0)
    center, radius = Point(0, 0), 5.0
    # Arco de 0° a 180° (semicírculo superior)
    hits = line_arc_intersection(a, b, center, radius, 0, 180)
    # La línea y=0 toca el arco en (5,0) y (-5,0), ambos en los extremos del arco
    assert len(hits) == 2


def test_linea_cruza_circulo_pero_no_el_arco():
    a, b = Point(-10, 0), Point(10, 0)
    center, radius = Point(0, 0), 5.0
    # Arco de 90° a 270° (semicírculo izquierdo)
    hits = line_arc_intersection(a, b, center, radius, 90, 270)
    # Solo (-5, 0) está en el arco (ángulo 180°)
    assert len(hits) == 1
    assert hits[0][0].x == pytest.approx(-5.0, abs=1e-9)


# ============================================================
# UTILIDAD: ÁNGULO EN ARCO
# ============================================================

def test_angulo_en_arco_normal():
    from tkcad.geometry.intersection import _angle_in_arc
    assert _angle_in_arc(45, 0, 90) is True
    assert _angle_in_arc(100, 0, 90) is False


def test_angulo_en_arco_que_cruza_cero():
    from tkcad.geometry.intersection import _angle_in_arc
    # Arco de 350° a 10°
    assert _angle_in_arc(355, 350, 10) is True
    assert _angle_in_arc(5, 350, 10) is True
    assert _angle_in_arc(180, 350, 10) is False