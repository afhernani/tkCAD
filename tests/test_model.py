from tkcad.core import Document, Point


class SpyDocument(Document):
    def __init__(self):
        super().__init__()
        self.changes = 0

    def notify_change(self):
        self.changes += 1


def test_add_line_asigna_ids_secuenciales():
    doc = Document()
    e1 = doc.add_line(Point(0, 0), Point(10, 0))
    e2 = doc.add_line(Point(1, 1), Point(2, 2))
    assert e1.id == 1
    assert e2.id == 2
    assert len(doc.entities) == 2


def test_notify_change_funciona_como_espia():
    doc = SpyDocument()
    doc.add_line(Point(0, 0), Point(1, 1))
    assert doc.changes == 1
    doc.add_entity("line", {"start": Point(0, 0), "end": Point(1, 1)}, notify=False)
    assert doc.changes == 1  # con notify=False no cuenta


def test_seleccion_basica():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.add_circle(Point(5, 5), 2.0)
    assert not doc.has_selection()
    doc.select_all()
    assert doc.selection_count() == 2
    doc.clear_selection()
    assert doc.selection_count() == 0
    doc.toggle_selection(1)
    assert doc.has_selection()
    doc.select_last()
    assert doc.selection_count() == 2


def test_delete_selected_y_delete_entities():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.add_circle(Point(5, 5), 2.0)
    doc.add_circle(Point(9, 9), 1.0)
    doc.toggle_selection(1)
    assert doc.delete_selected() == 1
    assert len(doc.entities) == 2
    assert doc.delete_entities("CIRCULO") == 2
    assert len(doc.entities) == 0


def test_get_entity_by_id():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    assert doc.get_entity_by_id(1) is not None
    assert doc.get_entity_by_id(99) is None