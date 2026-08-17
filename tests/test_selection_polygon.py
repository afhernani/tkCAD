from tkcad.core import Document, Point
from tkcad.geometry import point_in_polygon


def test_punto_dentro_de_poligono():
    square = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
    assert point_in_polygon(Point(5, 5), square)
    assert not point_in_polygon(Point(15, 5), square)


def test_window_poligono_solo_dentro():
    doc = Document()
    doc.add_line(Point(2, 2), Point(4, 4))     # dentro
    doc.add_line(Point(5, 5), Point(15, 15))   # sale
    poly = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
    count = doc.select_by_polygon(poly, mode="window", action="replace")
    assert count == 1
    assert doc.get_entity_by_id(1).selected
    assert not doc.get_entity_by_id(2).selected


def test_crossing_poligono_toca():
    doc = Document()
    doc.add_line(Point(2, 2), Point(4, 4))
    doc.add_line(Point(5, 5), Point(15, 15))
    poly = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
    count = doc.select_by_polygon(poly, mode="crossing", action="replace")
    assert count == 2