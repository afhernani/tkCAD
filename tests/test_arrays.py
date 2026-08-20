from tkcad.core import Document, Point


def test_array_rectangular_2x2():
    doc = Document()
    line = doc.add_line(Point(0, 0), Point(10, 0))

    ids = doc.array_rectangular([line.id], 2, 2, 20, 10)
    assert len(ids) == 3              # original + 3 copias
    assert len(doc.entities) == 4

    starts = sorted(
        (doc.get_entity_by_id(i).data["start"] for i in ids),
        key=lambda p: (p.y, p.x),
    )
    assert starts[0] == Point(20, 0)
    assert starts[1] == Point(0, 10)
    assert starts[2] == Point(20, 10)


def test_array_polar_4_copias():
    doc = Document()
    line = doc.add_line(Point(10, 0), Point(20, 0))

    ids = doc.array_polar([line.id], Point(0, 0), 4, 360)
    assert len(ids) == 3              # i=1..3 (90°, 180°, 270°)

    starts = sorted(
        (round(doc.get_entity_by_id(i).data["start"].x),
         round(doc.get_entity_by_id(i).data["start"].y))
        for i in ids
    )
    assert (0, 10) in starts          # girado 90°
    assert (-10, 0) in starts         # girado 180°
    assert (0, -10) in starts         # girado 270°


def test_array_polar_arco_mantiene_orientacion():
    doc = Document()
    arc = doc.add_arc(Point(10, 0), 5, 0, 90)

    ids = doc.array_polar([arc.id], Point(0, 0), 2, 360)
    copy = doc.get_entity_by_id(ids[0])
    assert copy.data["start_angle"] == 180   # 0 + 180