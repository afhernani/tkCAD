import math

from tkcad.core import CommandResult, Document, Point
from tkcad.commands.drawing.cota import CotaCommand


def _dist_seg(p, a, b):
    abx, aby = b.x - a.x, b.y - a.y
    apx, apy = p.x - a.x, p.y - a.y
    L = abx * abx + aby * aby
    t = 0.0 if L == 0 else max(0.0, min(1.0, (apx * abx + apy * aby) / L))
    return math.hypot(p.x - (a.x + t * abx), p.y - (a.y + t * aby))


class FakeCtx:
    def __init__(self, doc):
        self.doc = doc
        self.last = None

    def entity_at_point(self, p):
        best, best_d = None, 5.0
        for e in self.doc.entities:
            if e.kind != "line":
                continue
            d = _dist_seg(p, e.data["start"], e.data["end"])
            if d <= best_d:
                best_d, best = d, e
        return best

    def get_entity_by_id(self, i):
        return self.doc.get_entity_by_id(i)

    def add_dimension(self, dim_type, **kw):
        data = {"dim_type": dim_type, "text_height": 2.5}
        data.update(kw)
        self.last = self.doc.add_entity("dimension", data)
        return self.last

    def prompt(self, m): pass
    def write(self, m): pass


def test_cota_e_dos_lineas_angular_asociativa():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(50, 0))
    l2 = doc.add_line(Point(0, 0), Point(0, 50))

    cmd = CotaCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "E") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "25,0") == CommandResult.RUNNING   # línea 1
    assert cmd.handle_input(ctx, "0,25") == CommandResult.RUNNING   # línea 2
    assert cmd.handle_input(ctx, "") == CommandResult.FINISHED      # radio <15>

    d = ctx.last.data
    assert d["dim_type"] == "angular"
    assert d["assoc_entity_id"] == l1.id
    assert d["assoc_entity_id2"] == l2.id
    assert d["vertex"] == Point(0, 0)

    # asociatividad: mover l2 → el vértice sigue a la nueva intersección
    doc.set_selection_ids([l2.id])
    doc.move_selected(50, 0)
    doc.update_associative_dimensions()
    d = doc.get_entity_by_id(ctx.last.id).data
    assert d["vertex"] == Point(50, 0)
    assert d["p1"] == Point(0, 0)
    assert d["p2"] == Point(50, 50)


def test_cota_e_enter_sigue_lineal():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(50, 0))

    cmd = CotaCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    cmd.handle_input(ctx, "E")
    cmd.handle_input(ctx, "25,0")   # línea 1
    cmd.handle_input(ctx, "")       # Enter → lineal
    cmd.handle_input(ctx, "H")
    assert cmd.handle_input(ctx, "") == CommandResult.FINISHED

    assert ctx.last.data["dim_type"] == "linear_h"
    assert ctx.last.data["assoc_entity_id"] == l1.id