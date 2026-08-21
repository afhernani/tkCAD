import pytest

from tkcad.core import Document, Point, CommandResult
from tkcad.commands.drawing.cota import CotaCommand
from tkcad.core.dimension import (detach_assoc, dimension_text_height,
                                  dimension_text_position, resolve_assoc)



class FakeCtx:
    def __init__(self, doc, entity_at):
        self.doc = doc
        self._entity_at = entity_at
    def prompt(self, m): pass
    def write(self, m): pass
    def clear_preview(self): pass
    def entity_at_point(self, p, radius=3): return self._entity_at(p)
    def get_entity_by_id(self, eid): return self.doc.get_entity_by_id(eid)
    def add_dimension(self, *a, **k): return self.doc.add_dimension(*a, **k)


def test_cota_modo_entidad_linea_asociativa():
    doc = Document()
    line = doc.add_line(Point(0, 0), Point(10, 0))
    cmd = CotaCommand()
    ctx = FakeCtx(doc, lambda p: line)

    cmd.start(ctx)
    assert cmd.handle_input(ctx, "E") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "5,0") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "") == CommandResult.RUNNING   # ← NUEVO: Enter = lineal
    assert cmd.handle_input(ctx, "H") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "5") == CommandResult.FINISHED


def test_cota_modo_entidad_circulo_radio():
    doc = Document()
    circ = doc.add_circle(Point(0, 0), 5.0)
    cmd = CotaCommand()
    ctx = FakeCtx(doc, lambda p: circ)

    cmd.start(ctx)
    cmd.handle_input(ctx, "E")
    assert cmd.handle_input(ctx, "5,0") == CommandResult.FINISHED

    dims = [e for e in doc.entities if e.kind == "dimension"]
    assert dims[0].data["assoc_kind"] == "radius"
    assert dims[0].data["assoc_entity_id"] == circ.id


def test_resolve_assoc_line():
    doc = Document()
    line = doc.add_line(Point(0, 0), Point(10, 0))

    res = resolve_assoc({"assoc_kind": "line"}, line)
    assert res["p1"] == Point(0, 0)
    assert res["p2"] == Point(10, 0)


def test_resolve_assoc_radio_angulo_90():
    doc = Document()
    circ = doc.add_circle(Point(0, 0), 5.0)

    res = resolve_assoc({"assoc_kind": "radius", "assoc_angle": 90.0}, circ)
    assert res["center"] == Point(0, 0)
    assert res["p"].x == pytest.approx(0, abs=1e-9)
    assert res["p"].y == pytest.approx(5)


def test_resolve_assoc_radio_angulo_0():
    doc = Document()
    circ = doc.add_circle(Point(2, 2), 3.0)

    res = resolve_assoc({"assoc_kind": "radius", "assoc_angle": 0.0}, circ)
    assert res["p"].x == pytest.approx(5)
    assert res["p"].y == pytest.approx(2)


def test_resolve_assoc_tipo_no_coincide():
    doc = Document()
    circ = doc.add_circle(Point(0, 0), 5.0)

    assert resolve_assoc({"assoc_kind": "line"}, circ) is None


def test_resolve_assoc_sin_kind():
    doc = Document()
    line = doc.add_line(Point(0, 0), Point(1, 0))

    assert resolve_assoc({}, line) is None

def test_cota_lineal_asociativa_se_actualiza_al_mover():
    doc = Document()
    line = doc.add_line(Point(0, 0), Point(10, 0))
    dim = doc.add_dimension(
        "linear_h", p1=Point(0, 0), p2=Point(10, 0), offset=5,
        assoc_entity_id=line.id, assoc_kind="line",
    )

    doc.set_selection_ids([line.id])
    doc.move_selected(5, 5)

    d = doc.get_entity_by_id(dim.id).data
    assert d["p1"] == Point(5, 5)
    assert d["p2"] == Point(15, 5)


def test_cota_radio_asociativa_se_actualiza_al_cambiar_radio():
    doc = Document()
    circ = doc.add_circle(Point(0, 0), 5.0)
    dim = doc.add_dimension(
        "radius", center=Point(0, 0), p=Point(5, 0),
        assoc_entity_id=circ.id, assoc_kind="radius", assoc_angle=0.0,
    )

    doc.set_entity_property(circ.id, "radius", "10")

    d = doc.get_entity_by_id(dim.id).data
    assert d["p"].x == pytest.approx(10)
    assert d["center"] == Point(0, 0)


def test_borrar_entidad_desasocia_conservando_puntos():
    doc = Document()
    line = doc.add_line(Point(0, 0), Point(10, 0))
    dim = doc.add_dimension(
        "linear_h", p1=Point(0, 0), p2=Point(10, 0),
        assoc_entity_id=line.id, assoc_kind="line",
    )

    doc.set_selection_ids([line.id])
    doc.delete_selected()

    d = doc.get_entity_by_id(dim.id).data
    assert d.get("assoc_entity_id") is None
    assert d["p2"] == Point(10, 0)   # conserva la geometría

def test_text_position_con_offset():
    data = {"dim_type": "linear_h", "p1": Point(0, 0), "p2": Point(10, 0),
            "offset": 5, "text_offset": Point(2, 3)}
    tp = dimension_text_position(data)
    assert tp.x == pytest.approx(7)
    assert tp.y == pytest.approx(8)


def test_text_height_por_defecto():
    data = {"dim_type": "linear_h", "p1": Point(0, 0), "p2": Point(10, 0)}
    assert dimension_text_height(data) == 2.5


def test_text_height_personalizada():
    data = {"dim_type": "linear_h", "p1": Point(0, 0), "p2": Point(10, 0),
            "text_height": 5.0}
    assert dimension_text_height(data) == 5.0


def test_detach_assoc_elimina_referencia():
    data = {"assoc_entity_id": 1, "assoc_kind": "line", "p1": Point(0, 0)}
    detach_assoc(data)
    assert "assoc_entity_id" not in data
    assert "assoc_kind" not in data
    assert "p1" in data   # conserva geometría