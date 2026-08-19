from tkcad.core import Document, Point
from tkcad.core.dimension import (
    aligned_geometry, linear_geometry, measure_dimension, radius_geometry, offset_from_point,
)


def test_measure_linear_h():
    assert measure_dimension("linear_h", Point(0, 0), Point(10, 3)) == 10


def test_measure_linear_v():
    assert measure_dimension("linear_v", Point(0, 0), Point(3, 10)) == 10


def test_measure_aligned():
    assert measure_dimension("aligned", Point(0, 0), Point(3, 4)) == 5


def test_measure_radius():
    assert measure_dimension("radius", center=Point(0, 0), p=Point(3, 4)) == 5


def test_linear_h_geometry():
    g = linear_geometry(Point(0, 0), Point(10, 0), offset=5, horizontal=True)
    assert g["dim_start"].y == 5 and g["dim_end"].y == 5
    assert g["dim_start"].x == 0 and g["dim_end"].x == 10
    assert g["text_point"].x == 5
    assert g["value"] == 10


def test_aligned_geometry_longitud():
    g = aligned_geometry(Point(0, 0), Point(3, 4), offset=5)
    assert g["value"] == 5
    # la línea de cota es paralela y de la misma longitud
    d = math_hypot(g)
    assert abs(d - 5) < 1e-9


def math_hypot(g):
    import math
    return math.hypot(
        g["dim_end"].x - g["dim_start"].x,
        g["dim_end"].y - g["dim_start"].y,
    )


def test_radius_geometry():
    g = radius_geometry(Point(0, 0), Point(3, 4))
    assert g["value"] == 5


def test_add_dimension_y_bbox():
    doc = Document()
    e = doc.add_dimension("linear_h", p1=Point(0, 0), p2=Point(10, 0), offset=5)
    bbox = doc._get_entity_bbox(doc.get_entity_by_id(e.id))
    assert bbox is not None
    min_x, min_y, max_x, max_y = bbox
    assert max_x >= 10 and min_x <= 0
    assert max_y >= 5


def test_mover_dimension():
    doc = Document()
    e = doc.add_dimension("linear_h", p1=Point(0, 0), p2=Point(10, 0))
    doc.select_all()
    doc.move_selected(5, 5)
    d = doc.get_entity_by_id(e.id).data
    assert d["p1"] == Point(5, 5)
    assert d["p2"] == Point(15, 5)


def test_offset_from_point_linear_h():
    data = {"dim_type": "linear_h",
            "p1": Point(0, 0), "p2": Point(10, 0), "offset": 5}
    assert offset_from_point(data, Point(5, 8)) == 8


def test_offset_from_point_linear_v():
    data = {"dim_type": "linear_v",
            "p1": Point(0, 0), "p2": Point(0, 10), "offset": 5}
    assert offset_from_point(data, Point(7, 5)) == 7


def test_offset_from_point_aligned():
    data = {"dim_type": "aligned",
            "p1": Point(0, 0), "p2": Point(10, 0), "offset": 5}
    # perpendicular a p1→p2 es (0,1): el offset es la Y relativa
    assert offset_from_point(data, Point(5, 7)) == 7