from tkcad.core import CommandResult, Document, Point
from tkcad.commands.modify.bloque import BloqueCommand
from tkcad.commands.modify.descomponer import DescomponerCommand


class FakeCtx:
    def __init__(self, doc):
        self.doc = doc
    def get_selected_entities(self):
        return self.doc.get_selected_entities()
    def make_block(self, *a, **k):
        return self.doc.make_block(*a, **k)
    def explode_block(self, *a, **k):
        return self.doc.explode_block(*a, **k)
    @property
    def block_names(self):
        return self.doc.block_names
    def prompt(self, m): pass
    def write(self, m): pass


def test_bloque_crea_y_agrupa():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(10, 0))
    l2 = doc.add_line(Point(20, 0), Point(30, 0))
    doc.set_selection_ids([l1.id, l2.id])

    cmd = BloqueCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "PARED") == CommandResult.FINISHED

    assert "PARED" in doc.block_names.values()
    bid1 = getattr(doc.get_entity_by_id(l1.id), "block_id", None)
    bid2 = getattr(doc.get_entity_by_id(l2.id), "block_id", None)
    assert bid1 is not None and bid1 == bid2


def test_bloque_nombre_duplicado_reintenta():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(10, 0))
    doc.make_block([l1.id], "PARED")

    l2 = doc.add_line(Point(20, 0), Point(30, 0))
    doc.set_selection_ids([l2.id])
    cmd = BloqueCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "PARED") == CommandResult.RUNNING


def test_descomponer_rompe_el_bloque():
    doc = Document()
    l1 = doc.add_line(Point(0, 0), Point(10, 0))
    l2 = doc.add_line(Point(20, 0), Point(30, 0))
    doc.make_block([l1.id, l2.id], "PARED")
    doc.set_selection_ids([l1.id])

    cmd = DescomponerCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "") == CommandResult.FINISHED

    assert getattr(doc.get_entity_by_id(l1.id), "block_id", None) is None
    assert getattr(doc.get_entity_by_id(l2.id), "block_id", None) is None
    assert doc.block_names == {}