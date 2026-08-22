from tkcad.core import CommandResult
from tkcad.commands.drawing.sombrea import SombreaCommand
from tkcad.core import Document, Point
from tkcad.core.hatch import hatch_segments


class FakeCtx:
    def __init__(self, doc):
        self.doc = doc
    def get_selected_entities(self):
        return self.doc.get_selected_entities()
    def add_hatch(self, *a, **k):
        return self.doc.add_hatch(*a, **k)
    def prompt(self, m): pass
    def write(self, m): pass

def test_sombrea_manual_solido():
    doc = Document()
    cmd = SombreaCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "S") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "0,0") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "10,0") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "10,10") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "") == CommandResult.FINISHED
    hs = [e for e in doc.entities if e.kind == "hatch"]
    assert len(hs) == 1
    assert hs[0].data["style"] == "solid"
    assert len(hs[0].data["points"]) == 3


def test_sombrea_sobre_poligono_rayado():
    doc = Document()
    poly = doc.add_entity("polygon", {"points": [
        Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]})
    doc.set_selection_ids([poly.id])
    cmd = SombreaCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "R") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "2") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "45") == CommandResult.FINISHED
    hs = [e for e in doc.entities if e.kind == "hatch"]
    assert len(hs) == 1
    assert hs[0].data["style"] == "hatch"
    assert hs[0].data["spacing"] == 2.0
    assert len(hs[0].data["points"]) == 4


def test_hatch_segments_cuadrado():
    pts = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
    segs = hatch_segments(pts, spacing=5.0, angle=0.0)
    assert len(segs) >= 2
    for a, b in segs:
        assert abs(a.y - b.y) < 1e-9          # líneas horizontales
        assert -1e-6 <= a.y <= 10 + 1e-6
        assert 0 <= a.x <= 10 and 0 <= b.x <= 10


def test_hatch_segments_triangulo():
    pts = [Point(0, 0), Point(10, 0), Point(5, 10)]
    segs = hatch_segments(pts, spacing=2.0, angle=90.0)
    assert len(segs) >= 3
    for a, b in segs:
        assert abs(a.x - b.x) < 1e-9          # líneas verticales


def test_add_hatch_y_mover():
    doc = Document()
    h = doc.add_hatch([Point(0, 0), Point(10, 0), Point(10, 10)],
                      style="solid")
    assert h.kind == "hatch"
    doc.set_selection_ids([h.id])
    doc.move_selected(5, 5)
    d = doc.get_entity_by_id(h.id).data
    assert d["points"][0] == Point(5, 5)

def test_roundtrip_hatch_dxf(tmp_path):
    from tkcad.core.dxf_export import export_dxf
    from tkcad.core.dxf_import import import_dxf
    doc = Document()
    doc.add_hatch([Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)],
                  style="solid")
    path = tmp_path / "h.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg
    items, defs = import_dxf(path)
    hs = [d for k, d, l in items if k == "hatch"]
    assert len(hs) == 1
    assert hs[0]["style"] == "solid"
    assert len(hs[0]["points"]) >= 3


def test_export_svg_png_hatch(tmp_path):
    from tkcad.core.svg_export import export_svg
    from tkcad.core.png_export import export_png
    doc = Document()
    doc.add_hatch([Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)],
                  style="hatch", spacing=2.0, angle=45.0)
    ps = tmp_path / "h.svg"
    ok, msg = export_svg(doc.entities, lambda n: "white", ps)
    assert ok, msg
    assert "<line" in ps.read_text(encoding="utf-8")

    pp = tmp_path / "h.png"
    ok, msg = export_png(doc.entities, lambda n: "white", pp)
    assert ok, msg
    assert pp.stat().st_size > 0