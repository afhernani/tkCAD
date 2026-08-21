import pytest

from tkcad.core import Document, Point


def test_angular_asociativa_se_actualiza_al_mover():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(50, 0))
    l2 = doc.add_line(Point(0, 0), Point(0, 50))

    dim = doc.add_entity("dimension", {
        "dim_type": "angular",
        "vertex": Point(0, 0),
        "p1": Point(50, 0),
        "p2": Point(0, 50),
        "radius": 20.0,
        "text_height": 2.5,
        "assoc_entity_id": l1.id,
        "assoc_entity_id2": l2.id,
    })

    doc.set_selection_ids([l2.id])
    doc.move_selected(50, 0)
    doc.update_associative_dimensions()

    d = doc.get_entity_by_id(dim.id).data
    assert d["vertex"] == Point(50, 0)
    assert d["p1"] == Point(0, 0)
    assert d["p2"] == Point(50, 50)


def test_angular_paralelas_no_rompe():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(50, 0))
    l2 = doc.add_line(Point(0, 10), Point(50, 10))

    dim = doc.add_entity("dimension", {
        "dim_type": "angular",
        "vertex": Point(0, 0),
        "p1": Point(50, 0),
        "p2": Point(50, 10),
        "radius": 20.0,
        "text_height": 2.5,
        "assoc_entity_id": l1.id,
        "assoc_entity_id2": l2.id,
    })

    doc.update_associative_dimensions()
    d = doc.get_entity_by_id(dim.id).data
    assert d["vertex"] == Point(0, 0)     # paralelas → sin cambios