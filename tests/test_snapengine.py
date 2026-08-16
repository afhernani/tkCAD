import pytest

from tkcad.core import Entity, Point, SnapEngine


def make_line(entity_id, start, end):
    return Entity(
        id=entity_id,
        kind="line",
        data={"start": start, "end": end},
    )


def test_sin_modos_no_hay_snap():
    engine = SnapEngine()
    engine.snap_modes = set()
    p, kind = engine.snap_point([], Point(10.4, 9.6))
    assert p == Point(10.4, 9.6)
    assert kind is None


def test_snap_a_grid():
    engine = SnapEngine()
    engine.snap_modes = {"GRID"}
    engine.grid_size = 10.0
    p, kind = engine.snap_point([], Point(10.4, 9.6))
    assert p == Point(10.0, 10.0)
    assert kind == "GRID"


def test_snap_a_endpoint():
    engine = SnapEngine()
    engine.snap_modes = {"ENDPOINT"}
    entities = [make_line(1, Point(0, 0), Point(50, 50))]
    p, kind = engine.snap_point(entities, Point(50.5, 50.4))
    assert p == Point(50.0, 50.0)
    assert kind == "ENDPOINT"


def test_snap_a_midpoint():
    engine = SnapEngine()
    engine.snap_modes = {"MIDPOINT"}
    entities = [make_line(1, Point(0, 0), Point(10, 0))]
    p, kind = engine.snap_point(entities, Point(5.2, 0.3))
    assert p == Point(5.0, 0.0)
    assert kind == "MIDPOINT"


def test_snap_a_intersection():
    engine = SnapEngine()
    engine.snap_modes = {"INTERSECTION"}
    entities = [
        make_line(1, Point(0, 0), Point(10, 10)),
        make_line(2, Point(0, 10), Point(10, 0)),
    ]
    p, kind = engine.snap_point(entities, Point(5.3, 4.8))
    assert p == Point(5.0, 5.0)
    assert kind == "INTERSECTION"


def test_ortho_horizontal_y_vertical():
    engine = SnapEngine()
    engine.snap_modes = {"ORTHO"}
    base = Point(10.0, 10.0)
    p, kind = engine.snap_point([], Point(15.0, 12.0), base_point=base)
    assert p == Point(15.0, 10.0)
    assert kind == "ORTHO"
    p, kind = engine.snap_point([], Point(12.0, 15.0), base_point=base)
    assert p == Point(10.0, 15.0)
    assert kind == "ORTHO"


def test_endpoint_prioriza_sobre_grid():
    engine = SnapEngine()
    engine.snap_modes = {"ENDPOINT", "GRID"}
    engine.grid_size = 10.0
    entities = [make_line(1, Point(0, 0), Point(53, 53))]
    p, kind = engine.snap_point(entities, Point(53.2, 53.2))
    assert p == Point(53.0, 53.0)
    assert kind == "ENDPOINT"


def test_toggle_y_configuracion_de_modos():
    engine = SnapEngine()
    engine.snap_modes = set()
    assert engine.toggle_snap_mode("ORTHO") is True
    assert "ORTHO" in engine.snap_modes
    assert engine.toggle_snap_mode("ORTHO") is False
    assert "ORTHO" not in engine.snap_modes
    engine.set_all_snap_modes()
    assert "GRID" in engine.snap_modes
    assert "ENDPOINT" in engine.snap_modes
    engine.clear_snap_modes()
    assert engine.snap_modes == set()

def test_tolerancia_de_snap_se_ajusta_con_el_zoom():
    engine = SnapEngine()
    engine.snap_modes = {"ENDPOINT"}
    engine.snap_tolerance_pixels = 8
    entities = [make_line(1, Point(0, 0), Point(50, 50))]
    # A 2.5 unidades del extremo: con zoom x4 (8 px = 2 uds) NO imanta...
    p, kind = engine.snap_point(entities, Point(52.5, 50), scale=4.0)
    assert kind is None
    # ...pero con zoom 1 sí.
    p, kind = engine.snap_point(entities, Point(52.5, 50))
    assert kind == "ENDPOINT"