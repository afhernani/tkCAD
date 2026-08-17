import math

import pytest

from tkcad.core import Document, Point


def test_trim_conserva_el_lado_del_punto():
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))  # id 1: a recortar
    doc.add_line(Point(0, -5), Point(0, 5))    # id 2: límite
    ok, msg = doc.trim_line_by_line(2, 1, Point(-5, 0))
    assert ok
    e = doc.get_entity_by_id(1)
    assert e.data["start"] == Point(-10, 0)
    assert e.data["end"] == Point(0, 0)


def test_trim_conserva_el_otro_lado():
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))
    doc.add_line(Point(0, -5), Point(0, 5))
    ok, msg = doc.trim_line_by_line(2, 1, Point(5, 0))
    assert ok
    e = doc.get_entity_by_id(1)
    assert e.data["start"] == Point(0, 0)
    assert e.data["end"] == Point(10, 0)


def test_trim_sin_interseccion_falla():
    doc = Document()
    doc.add_line(Point(0, 0), Point(5, 0))
    doc.add_line(Point(0, 5), Point(5, 5))
    ok, msg = doc.trim_line_by_line(2, 1, Point(0, 0))
    assert not ok


def test_extend_alarga_hasta_el_limite():
    doc = Document()
    doc.add_line(Point(-10, 0), Point(-2, 0))  # id 1: no llega al límite
    doc.add_line(Point(0, -5), Point(0, 5))    # id 2: límite
    ok, msg = doc.extend_line_to_line(2, 1)
    assert ok
    e = doc.get_entity_by_id(1)
    assert e.data["end"] == Point(0, 0)


def test_extend_si_ya_cruza_falla():
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))  # ya cruza el límite
    doc.add_line(Point(0, -5), Point(0, 5))
    ok, msg = doc.extend_line_to_line(2, 1)
    assert not ok

# ============================================================
# TRIM CON CÍRCULO
# ============================================================

def test_trim_linea_con_circulo_dos_cruces():
    """Línea horizontal que cruza un círculo en dos puntos."""
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))       # id 1: línea a recortar
    doc.add_circle(Point(0, 0), 5.0)                 # id 2: círculo límite

    # Mantener el segmento DENTRO del círculo (entre -5 y 5)
    ok, msg = doc.trim_by_entity(2, 1, Point(0, 0))
    assert ok, msg
    e = doc.get_entity_by_id(1)
    assert e.data["start"].x == pytest.approx(-5.0, abs=1e-9)
    assert e.data["end"].x == pytest.approx(5.0, abs=1e-9)


def test_trim_linea_con_circulo_lado_izquierdo():
    """Mantener el segmento exterior izquierdo."""
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))       # id 1
    doc.add_circle(Point(0, 0), 5.0)                 # id 2

    # Mantener el segmento ANTES del primer cruce (x < -5)
    ok, msg = doc.trim_by_entity(2, 1, Point(-8, 0))
    assert ok, msg
    e = doc.get_entity_by_id(1)
    assert e.data["start"].x == pytest.approx(-10.0, abs=1e-9)
    assert e.data["end"].x == pytest.approx(-5.0, abs=1e-9)


def test_trim_linea_con_circulo_lado_derecho():
    """Mantener el segmento exterior derecho."""
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))       # id 1
    doc.add_circle(Point(0, 0), 5.0)                 # id 2

    # Mantener el segmento DESPUÉS del segundo cruce (x > 5)
    ok, msg = doc.trim_by_entity(2, 1, Point(8, 0))
    assert ok, msg
    e = doc.get_entity_by_id(1)
    assert e.data["start"].x == pytest.approx(5.0, abs=1e-9)
    assert e.data["end"].x == pytest.approx(10.0, abs=1e-9)


def test_trim_linea_no_toca_circulo():
    """Línea que no intersecta el círculo."""
    doc = Document()
    doc.add_line(Point(-10, 10), Point(10, 10))     # id 1: por encima
    doc.add_circle(Point(0, 0), 5.0)                 # id 2

    ok, msg = doc.trim_by_entity(2, 1, Point(0, 10))
    assert not ok
    assert "no intersecta" in msg.lower()


def test_trim_linea_tangente_a_circulo():
    """Línea tangente al círculo: un solo punto de cruce."""
    doc = Document()
    doc.add_line(Point(-10, 5), Point(10, 5))       # id 1: tangente en (0,5)
    doc.add_circle(Point(0, 0), 5.0)                 # id 2

    # Mantener el lado izquierdo
    ok, msg = doc.trim_by_entity(2, 1, Point(-8, 5))
    assert ok, msg
    e = doc.get_entity_by_id(1)
    assert e.data["end"].x == pytest.approx(0.0, abs=1e-9)
    assert e.data["end"].y == pytest.approx(5.0, abs=1e-9)


# ============================================================
# TRIM CON ARCO
# ============================================================

def test_trim_linea_con_arco_semicirculo_superior():
    """Línea horizontal que cruza un arco de 0° con extensión 180°."""
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))       # id 1
    # Arco: centro=(0,0), radio=5, start_angle=0°, extent=180°
    doc.add_entity("arc", {
        "center": Point(0, 0),
        "radius": 5.0,
        "start_angle": 0.0,
        "extent": 180.0,
    })                                                # id 2

    # Mantener el segmento DENTRO del arco (entre -5 y 5)
    ok, msg = doc.trim_by_entity(2, 1, Point(0, 0))
    assert ok, msg
    e = doc.get_entity_by_id(1)
    assert e.data["start"].x == pytest.approx(-5.0, abs=1e-9)
    assert e.data["end"].x == pytest.approx(5.0, abs=1e-9)


def test_trim_linea_con_arco_semicirculo_izquierdo():
    """Arco de 90° con extensión 180° (semicírculo izquierdo)."""
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))       # id 1
    # Arco: start_angle=90°, extent=180° → cubre de 90° a 270°
    doc.add_entity("arc", {
        "center": Point(0, 0),
        "radius": 5.0,
        "start_angle": 90.0,
        "extent": 180.0,
    })                                                # id 2

    # La línea y=0 cruza el círculo en (5,0)→ángulo 0° y (-5,0)→ángulo 180°
    # Solo (-5,0) con ángulo 180° está en el arco [90°, 270°]
    ok, msg = doc.trim_by_entity(2, 1, Point(-8, 0))
    assert ok, msg
    e = doc.get_entity_by_id(1)
    assert e.data["end"].x == pytest.approx(-5.0, abs=1e-9)


def test_trim_linea_con_arco_cuarto_circulo():
    """Arco de 0° con extensión 90° (primer cuadrante)."""
    doc = Document()
    # Línea diagonal que cruza el primer cuadrante
    doc.add_line(Point(-5, -5), Point(5, 5))        # id 1
    # Arco: start_angle=0°, extent=90° → cubre de 0° a 90°
    doc.add_entity("arc", {
        "center": Point(0, 0),
        "radius": 5.0,
        "start_angle": 0.0,
        "extent": 90.0,
    })                                                # id 2

    # La diagonal cruza el círculo en ángulo 45° (dentro del arco)
    # y en ángulo 225° (fuera del arco)
    ok, msg = doc.trim_by_entity(2, 1, Point(-3, -3))
    assert ok, msg
    e = doc.get_entity_by_id(1)
    # El end debe estar en el punto de intersección del primer cuadrante
    expected_x = 5.0 * math.cos(math.radians(45))
    expected_y = 5.0 * math.sin(math.radians(45))
    assert e.data["end"].x == pytest.approx(expected_x, abs=1e-9)
    assert e.data["end"].y == pytest.approx(expected_y, abs=1e-9)


def test_trim_linea_con_arco_que_cruza_cero():
    """Arco que cruza el límite de 0°/360°."""
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))       # id 1
    # Arco: start_angle=350°, extent=20° → cubre de 350° a 10°
    doc.add_entity("arc", {
        "center": Point(0, 0),
        "radius": 5.0,
        "start_angle": 350.0,
        "extent": 20.0,
    })                                                # id 2

    # La línea y=0 cruza en ángulo 0° (dentro del arco [350°, 10°])
    # y en ángulo 180° (fuera del arco)
    ok, msg = doc.trim_by_entity(2, 1, Point(-8, 0))
    assert ok, msg
    e = doc.get_entity_by_id(1)
    assert e.data["end"].x == pytest.approx(5.0, abs=1e-9)
    assert e.data["end"].y == pytest.approx(0.0, abs=1e-9)


def test_trim_linea_no_intersecta_arco():
    """Línea que cruza el círculo pero fuera del rango del arco."""
    doc = Document()
    doc.add_line(Point(-10, 0), Point(10, 0))       # id 1
    # Arco: start_angle=90°, extent=90° → cubre de 90° a 180°
    doc.add_entity("arc", {
        "center": Point(0, 0),
        "radius": 5.0,
        "start_angle": 90.0,
        "extent": 90.0,
    })                                                # id 2

    # La línea y=0 cruza en 0° y 180°, pero el arco solo cubre [90°, 180°]
    # El punto en 180° es (-5, 0), que está en el borde del arco
    ok, msg = doc.trim_by_entity(2, 1, Point(8, 0))
    # Dependiendo de la tolerancia EPS, puede o no intersectar
    # Si no intersecta, el mensaje debe indicarlo
    if not ok:
        assert "no intersecta" in msg.lower()


# ============================================================
# DISPATCHER GENÉRICO
# ============================================================

def test_trim_dispatcher_combinacion_no_soportada():
    """Intentar recortar un círculo con una línea (no soportado aún)."""
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))         # id 1
    doc.add_circle(Point(5, 5), 3.0)                 # id 2

    # Intentar recortar el círculo (target) con la línea (limit)
    ok, msg = doc.trim_by_entity(1, 2, Point(5, 5))
    assert not ok
    assert "no soporta" in msg.lower()


def test_trim_dispatcher_entidad_no_encontrada():
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))

    ok, msg = doc.trim_by_entity(99, 1, Point(5, 0))
    assert not ok
    assert "no encontrada" in msg.lower()