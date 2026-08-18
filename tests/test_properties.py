from tkcad.core import Document, Point


def test_get_properties_line():
    doc = Document()
    e = doc.add_line(Point(0, 0), Point(10, 0))
    props = dict(doc.get_entity_properties(e.id))
    assert props["tipo"] == "line"
    assert "start" in props and "end" in props


def test_set_property_numero():
    doc = Document()
    e = doc.add_circle(Point(0, 0), 5.0)
    ok, msg = doc.set_entity_property(e.id, "radius", "8")
    assert ok, msg
    assert doc.get_entity_by_id(e.id).data["radius"] == 8.0


def test_set_property_punto():
    doc = Document()
    e = doc.add_line(Point(0, 0), Point(10, 0))
    ok, msg = doc.set_entity_property(e.id, "end", "20,5")
    assert ok, msg
    assert doc.get_entity_by_id(e.id).data["end"] == Point(20, 5)


def test_set_property_radio_invalido():
    doc = Document()
    e = doc.add_circle(Point(0, 0), 5.0)
    ok, msg = doc.set_entity_property(e.id, "radius", "-3")
    assert not ok


def test_set_property_capa():
    doc = Document()
    doc.add_layer("muros")
    e = doc.add_line(Point(0, 0), Point(1, 0))
    ok, msg = doc.set_entity_property(e.id, "capa", "muros")
    assert ok, msg
    assert doc.get_entity_by_id(e.id).layer == "muros"


def test_set_property_capa_inexistente():
    doc = Document()
    e = doc.add_line(Point(0, 0), Point(1, 0))
    ok, msg = doc.set_entity_property(e.id, "capa", "nope")
    assert not ok


def test_set_property_campo_no_editable():
    doc = Document()
    e = doc.add_line(Point(0, 0), Point(1, 0))
    ok, msg = doc.set_entity_property(e.id, "tipo", "circle")
    assert not ok