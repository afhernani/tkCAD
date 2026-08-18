import pytest
from tkcad.core import Document, Point


def make_polyline(doc):
    """Helper: crea una polilínea de 3 puntos y devuelve su ID."""
    entity = doc.add_entity("polyline", {
        "points": [Point(0, 0), Point(10, 0), Point(10, 10)]
    })
    return entity.id   # ← el ID, no el objeto


def make_polygon(doc):
    """Helper: crea un triángulo y devuelve su ID."""
    entity = doc.add_entity("polygon", {
        "points": [Point(0, 0), Point(10, 0), Point(5, 10)]
    })
    return entity.id   # ← el ID, no el objeto


# ============================================================
# ADD VERTEX
# ============================================================

def test_add_vertex_en_primer_segmento():
    doc = Document()
    eid = make_polyline(doc)
    ok, msg = doc.add_vertex(eid, 0, Point(5, 2))
    assert ok, msg
    pts = doc.get_entity_by_id(eid).data["points"]
    assert len(pts) == 4
    assert pts[0] == Point(0, 0)
    assert pts[1] == Point(5, 2)
    assert pts[2] == Point(10, 0)
    assert pts[3] == Point(10, 10)


def test_add_vertex_en_segundo_segmento():
    doc = Document()
    eid = make_polyline(doc)
    ok, msg = doc.add_vertex(eid, 1, Point(10, 5))
    assert ok, msg
    pts = doc.get_entity_by_id(eid).data["points"]
    assert len(pts) == 4
    assert pts[1] == Point(10, 0)
    assert pts[2] == Point(10, 5)
    assert pts[3] == Point(10, 10)


def test_add_vertex_solo_polilinea_o_poligono():
    doc = Document()
    linea = doc.add_line(Point(0, 0), Point(5, 5))
    ok, msg = doc.add_vertex(linea.id, 0, Point(2, 2))
    assert not ok


def test_add_vertex_indice_fuera_de_rango():
    doc = Document()
    eid = make_polyline(doc)
    ok, msg = doc.add_vertex(eid, 99, Point(0, 0))
    assert not ok


def test_add_vertex_entidad_no_existe():
    doc = Document()
    ok, msg = doc.add_vertex(999, 0, Point(0, 0))
    assert not ok
    assert "no encontrada" in msg.lower()


# ============================================================
# REMOVE VERTEX
# ============================================================

def test_remove_vertex_polilinea():
    doc = Document()
    eid = make_polyline(doc)
    ok, msg = doc.remove_vertex(eid, 1)
    assert ok, msg
    pts = doc.get_entity_by_id(eid).data["points"]
    assert len(pts) == 2
    assert pts[0] == Point(0, 0)
    assert pts[1] == Point(10, 10)


def test_remove_vertex_poligono_minimo():
    doc = Document()
    eid = make_polygon(doc)   # 3 puntos
    ok, msg = doc.remove_vertex(eid, 1)
    assert not ok   # un polígono necesita al menos 3


def test_remove_vertex_poligono_con_4_puntos():
    doc = Document()
    entity = doc.add_entity("polygon", {
        "points": [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
    })
    eid = entity.id
    ok, msg = doc.remove_vertex(eid, 1)
    assert ok, msg
    pts = doc.get_entity_by_id(eid).data["points"]
    assert len(pts) == 3


def test_remove_vertex_minimo_polilinea():
    doc = Document()
    entity = doc.add_entity("polyline", {
        "points": [Point(0, 0), Point(5, 5)]
    })
    eid = entity.id
    ok, msg = doc.remove_vertex(eid, 0)
    assert not ok
    assert "mínimo" in msg.lower() or "al menos" in msg.lower()


def test_remove_vertex_indice_fuera_de_rango():
    doc = Document()
    eid = make_polyline(doc)
    ok, msg = doc.remove_vertex(eid, 99)
    assert not ok


def test_remove_vertex_entidad_no_existe():
    doc = Document()
    ok, msg = doc.remove_vertex(999, 0)
    assert not ok
    assert "no encontrada" in msg.lower()


# ============================================================
# COMBINACIONES
# ============================================================

def test_add_y_remove_preservan_datos():
    doc = Document()
    eid = make_polyline(doc)

    ok, _ = doc.add_vertex(eid, 0, Point(5, 5))
    assert ok

    ok, _ = doc.remove_vertex(eid, 1)
    assert ok

    pts = doc.get_entity_by_id(eid).data["points"]
    assert len(pts) == 3
    assert pts[0] == Point(0, 0)
    assert pts[1] == Point(10, 0)
    assert pts[2] == Point(10, 10)