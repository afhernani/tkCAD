from tkcad.core import CommandResult, Document, Point
from tkcad.commands.modify.defbloque import DefBloqueCommand
from tkcad.commands.modify.insertar import InsertarCommand
from tkcad.commands.modify.descomponer import DescomponerCommand


class FakeCtx:
    def __init__(self, doc):
        self.doc = doc
    def get_selected_entities(self):
        return self.doc.get_selected_entities()
    def define_block_def(self, *a, **k):
        return self.doc.define_block_def(*a, **k)
    def insert_block(self, *a, **k):
        return self.doc.insert_block(*a, **k)
    def explode_block(self, *a, **k):
        return self.doc.explode_block(*a, **k)
    def explode_insert(self, *a, **k):
        return self.doc.explode_insert(*a, **k)
    def set_selection_ids(self, ids):
        self.doc.set_selection_ids(ids)
    @property
    def block_defs(self):
        return self.doc.block_defs
    def prompt(self, m): pass
    def write(self, m): pass


def test_defbloque_insertar_flujo():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    doc.set_selection_ids([l.id])

    cmd = DefBloqueCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "PUERTA") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "0,0") == CommandResult.FINISHED
    assert "PUERTA" in doc.block_defs
    assert len(doc.entities) == 0

    ins = InsertarCommand()
    ins.start(ctx)
    assert ins.handle_input(ctx, "PUERTA") == CommandResult.RUNNING
    assert ins.handle_input(ctx, "50,50") == CommandResult.RUNNING
    assert ins.handle_input(ctx, "") == CommandResult.RUNNING     # rot <0>
    assert ins.handle_input(ctx, "") == CommandResult.FINISHED    # escala <1>
    assert len(doc.entities) == 1
    assert doc.entities[0].kind == "insert"


def test_descomponer_insert():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    doc.define_block_def("V1", [l.id], Point(0, 0))
    ins = doc.insert_block("V1", Point(100, 0))
    doc.set_selection_ids([ins.id])

    cmd = DescomponerCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "") == CommandResult.FINISHED

    assert len(doc.entities) == 1
    assert doc.entities[0].kind == "line"
    assert doc.entities[0].data["start"] == Point(100, 0)