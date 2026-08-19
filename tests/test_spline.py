from tkcad.core import Document, Point


def test_add_spline_crea_entidad():
    doc = Document()
    e = doc.add_spline([Point(0, 0), Point(10, 5), Point(20, 0)])
    ent = doc.get_entity_by_id(e.id)
    assert ent.kind == "spline"
    assert len(ent.data["points"]) == 3
    assert ent.data["closed"] is False


def test_spline_cerrada():
    doc = Document()
    e = doc.add_spline(
        [Point(0, 0), Point(10, 0), Point(10, 10)], closed=True,
    )
    assert doc.get_entity_by_id(e.id).data["closed"] is True


def test_spline_tiene_bbox():
    doc = Document()
    e = doc.add_spline([Point(0, 0), Point(10, 10), Point(20, 0)])
    bbox = doc._get_entity_bbox(doc.get_entity_by_id(e.id))
    assert bbox is not None
    min_x, min_y, max_x, max_y = bbox
    assert min_x <= 0 and max_x >= 20


def test_mover_spline():
    doc = Document()
    e = doc.add_spline([Point(0, 0), Point(10, 5)])
    doc.select_all()
    doc.move_selected(5, 5)
    d = doc.get_entity_by_id(e.id).data
    assert d["points"][0] == Point(5, 5)
    assert d["points"][1] == Point(15, 10)


def test_spline_seleccion_y_borrado():
    doc = Document()
    e = doc.add_spline([Point(0, 0), Point(5, 5), Point(10, 0)])
    doc.select_all()
    doc.delete_selected()
    assert doc.get_entity_by_id(e.id) is None