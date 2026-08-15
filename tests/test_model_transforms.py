import pytest

from tkcad.core import Document, Point


def test_move_selected():
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.select_all()
    doc.move_selected(5, 5)
    e = doc.entities[0]
    assert e.data["start"] == Point(5, 5)
    assert e.data["end"] == Point(15, 5)


def test_move_cero_avisa_por_log():
    class Spy(Document):
        def __init__(self):
            super().__init__()
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    doc = Spy()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.select_all()
    doc.move_selected(0, 0)
    assert doc.logs == ["Desplazamiento cero."]


def test_copy_selected_no_toca_el_original():
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.select_all()
    new_ids = doc.copy_selected(0, 5)
    assert len(new_ids) == 1
    assert len(doc.entities) == 2
    assert doc.entities[0].data["start"] == Point(0, 0)
    assert doc.entities[1].data["start"] == Point(0, 5)


def test_scale_selected():
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.add_circle(Point(5, 5), 2.0)
    doc.select_all()
    doc.scale_selected(Point(0, 0), 2.0)
    assert doc.entities[0].data["end"] == Point(20, 0)
    assert doc.entities[1].data["center"] == Point(10, 10)
    assert doc.entities[1].data["radius"] == 4.0


def test_rotate_selected_90_grados():
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.select_all()
    doc.rotate_selected(Point(0, 0), 90)
    e = doc.entities[0]
    assert e.data["end"].x == pytest.approx(0)
    assert e.data["end"].y == pytest.approx(10)


def test_mirror_selected_eje_vertical():
    doc = Document()
    doc.add_line(Point(2, 1), Point(4, 1))
    doc.select_all()
    doc.mirror_selected(Point(0, 0), Point(0, 1))
    e = doc.entities[0]
    assert e.data["start"] == Point(-2, 1)
    assert e.data["end"] == Point(-4, 1)