import math

import pytest

from tkcad.core import Point, Document, CommandResult
from tkcad.commands.drawing.cota import CotaCommand
from tkcad.core.dimension import angular_geometry, angular_measure


class FakeCtx:
    def __init__(self, doc):
        self.doc = doc
    def prompt(self, m): pass
    def write(self, m): pass
    def clear_preview(self): pass
    def get_entity_by_id(self, eid): return self.doc.get_entity_by_id(eid)
    def add_dimension(self, *a, **k): return self.doc.add_dimension(*a, **k)


def test_cota_angular_flujo_completo():
    doc = Document()
    cmd = CotaCommand()
    ctx = FakeCtx(doc)

    cmd.start(ctx)
    assert cmd.handle_input(ctx, "G") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "0,0") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "10,0") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "0,10") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "5") == CommandResult.FINISHED

    dims = [e for e in doc.entities if e.kind == "dimension"]
    assert len(dims) == 1
    d = dims[0].data
    assert d["dim_type"] == "angular"
    assert d["vertex"] == Point(0, 0)
    assert d["radius"] == 5


def test_angular_measure_90():
    v = Point(0, 0)
    assert angular_measure(v, Point(10, 0), Point(0, 10)) == pytest.approx(90)


def test_angular_measure_180():
    v = Point(0, 0)
    assert angular_measure(v, Point(10, 0), Point(-10, 0)) == pytest.approx(180)


def test_angular_measure_sentido_antihorario():
    v = Point(0, 0)
    # del rayo 90° al rayo 0° en sentido antihorario son 270°
    assert angular_measure(v, Point(0, 10), Point(10, 0)) == pytest.approx(270)


def test_angular_geometry_valor_y_extremos():
    data = {"dim_type": "angular", "vertex": Point(0, 0),
            "p1": Point(10, 0), "p2": Point(0, 10), "radius": 5}
    g = angular_geometry(data)

    assert g["value"] == pytest.approx(90)
    assert g["arc_start"].x == pytest.approx(5)
    assert g["arc_start"].y == pytest.approx(0, abs=1e-9)
    assert g["arc_end"].x == pytest.approx(0, abs=1e-9)
    assert g["arc_end"].y == pytest.approx(5)


def test_angular_geometry_texto_en_el_punto_medio():
    data = {"dim_type": "angular", "vertex": Point(0, 0),
            "p1": Point(10, 0), "p2": Point(0, 10), "radius": 5}
    g = angular_geometry(data)

    esperado = 5 * math.cos(math.radians(45))
    assert g["text_point"].x == pytest.approx(esperado)
    assert g["text_point"].y == pytest.approx(esperado)

from tkcad.core import Document


def test_add_dimension_angular():
    doc = Document()
    e = doc.add_dimension(
        "angular", vertex=Point(0, 0), p1=Point(10, 0),
        p2=Point(0, 10), radius=8,
    )
    ent = doc.get_entity_by_id(e.id)
    assert ent.kind == "dimension"
    assert ent.data["dim_type"] == "angular"
    assert ent.data["vertex"] == Point(0, 0)
    assert ent.data["radius"] == 8


def test_angular_tiene_bbox():
    doc = Document()
    e = doc.add_dimension(
        "angular", vertex=Point(0, 0), p1=Point(10, 0),
        p2=Point(0, 10), radius=5,
    )
    bbox = doc._get_entity_bbox(doc.get_entity_by_id(e.id))
    assert bbox is not None
    min_x, min_y, max_x, max_y = bbox
    assert max_x >= 5 and max_y >= 5


def test_mover_cota_angular():
    doc = Document()
    e = doc.add_dimension(
        "angular", vertex=Point(0, 0), p1=Point(10, 0), p2=Point(0, 10),
    )
    doc.set_selection_ids([e.id])
    doc.move_selected(5, 5)
    d = doc.get_entity_by_id(e.id).data
    assert d["vertex"] == Point(5, 5)
    assert d["p1"] == Point(15, 5)
    assert d["p2"] == Point(5, 15)


def test_export_svg_angular(tmp_path):
    from tkcad.core.svg_export import export_svg
    doc = Document()
    doc.add_dimension("angular", vertex=Point(0, 0),
                      p1=Point(10, 0), p2=Point(0, 10), radius=5)
    path = tmp_path / "ang.svg"
    ok, msg = export_svg(doc.entities, lambda n: "white", path)
    assert ok, msg
    c = path.read_text(encoding="utf-8")
    assert "<polyline" in c and "°" in c


def test_export_png_angular(tmp_path):
    from tkcad.core.png_export import export_png
    doc = Document()
    doc.add_dimension("angular", vertex=Point(0, 0),
                      p1=Point(10, 0), p2=Point(0, 10), radius=5)
    path = tmp_path / "ang.png"
    ok, msg = export_png(doc.entities, lambda n: "white", path)
    assert ok, msg


def test_export_dxf_angular(tmp_path):
    from tkcad.core.dxf_export import export_dxf
    doc = Document()
    doc.add_dimension("angular", vertex=Point(0, 0),
                      p1=Point(10, 0), p2=Point(0, 10), radius=5)
    path = tmp_path / "ang.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg

