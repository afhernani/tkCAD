from tkcad.core import CommandResult, Document, Point
from tkcad.commands.modify.redefinir import RedefinirCommand


class FakeCtx:
    def __init__(self, doc):
        self.doc = doc
    def get_selected_entities(self):
        return self.doc.get_selected_entities()
    def redefine_block_def(self, *a, **k):
        return self.doc.redefine_block_def(*a, **k)
    def set_selection_ids(self, ids):
        self.doc.set_selection_ids(ids)
    @property
    def block_defs(self):
        return self.doc.block_defs
    def prompt(self, m): pass
    def write(self, m): pass


def test_redef_actualiza_todos_los_inserts():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    doc.define_block_def("V1", [l.id], Point(0, 0))
    ins1 = doc.insert_block("V1", Point(100, 0))
    ins2 = doc.insert_block("V1", Point(200, 0), rotation=90)

    # Nueva geometría: un círculo
    c = doc.add_circle(Point(0, 0), 5)
    doc.set_selection_ids([c.id])

    cmd = RedefinirCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "V1") == CommandResult.RUNNING
    assert cmd.handle_input(ctx, "0,0") == CommandResult.FINISHED

    # Ambos inserts ven ahora el círculo
    for ins, px in ((ins1, 100), (ins2, 200)):
        world = doc.insert_world_entities(doc.get_entity_by_id(ins.id))
        assert len(world) == 1
        kind, data, layer = world[0]
        assert kind == "circle"
        assert data["radius"] == 5
    w1 = doc.insert_world_entities(doc.get_entity_by_id(ins1.id))[0][1]
    assert w1["center"] == Point(100, 0)


def test_redef_nombre_inexistente_reintenta():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    doc.set_selection_ids([l.id])
    cmd = RedefinirCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, "NOPE") == CommandResult.RUNNING