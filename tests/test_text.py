from tkcad.core import Document, Point


def test_add_text_crea_entidad():
    doc = Document()
    entity = doc.add_text(Point(10, 20), 2.5, "HOLA")
    e = doc.get_entity_by_id(entity.id)
    assert e.kind == "text"
    assert e.data["content"] == "HOLA"
    assert e.data["height"] == 2.5
    assert e.data["position"] == Point(10, 20)


def test_text_tiene_bbox():
    doc = Document()
    entity = doc.add_text(Point(0, 0), 2.0, "ABCD")
    bbox = doc._get_entity_bbox(doc.get_entity_by_id(entity.id))
    assert bbox is not None
    min_x, min_y, max_x, max_y = bbox
    assert max_x > min_x
    assert max_y > min_y


def test_mover_texto():
    doc = Document()
    entity = doc.add_text(Point(0, 0), 2.0, "X")
    doc.select_all()
    doc.move_selected(5, 5)
    e = doc.get_entity_by_id(entity.id)
    assert e.data["position"] == Point(5, 5)


def test_text_se_puede_seleccionar_y_borrar():
    doc = Document()
    entity = doc.add_text(Point(0, 0), 2.0, "ADIOS")
    doc.select_all()
    doc.delete_selected()
    assert doc.get_entity_by_id(entity.id) is None