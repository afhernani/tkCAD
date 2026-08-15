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