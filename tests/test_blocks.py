from tkcad.core import Document, Point


def test_make_block_seleccion_conjunta():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(10, 0))
    l2 = doc.add_line(Point(20, 0), Point(30, 0))

    doc.make_block([l1.id, l2.id], "B1")
    doc.set_selection_ids([l1.id])

    sel = sorted(e.id for e in doc.get_selected_entities())
    assert sel == sorted([l1.id, l2.id])


def test_mover_bloque_mueve_todo():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(10, 0))
    l2 = doc.add_line(Point(20, 0), Point(30, 0))
    doc.make_block([l1.id, l2.id], "B1")

    doc.set_selection_ids([l1.id])
    doc.move_selected(5, 5)

    assert doc.get_entity_by_id(l2.id).data["start"] == Point(25, 5)


def test_explode_block():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(10, 0))
    l2 = doc.add_line(Point(20, 0), Point(30, 0))
    doc.make_block([l1.id, l2.id], "B1")

    assert doc.explode_block([l1.id]) == 1
    doc.set_selection_ids([l1.id])
    sel = [e.id for e in doc.get_selected_entities()]
    assert sel == [l1.id]