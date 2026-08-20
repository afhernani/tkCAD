from tkcad.core import CommandResult, Document, Point
from tkcad.commands.modify.matriz import MatrizCommand


class FakeCtx:
    def __init__(self, doc, sel):
        self.doc = doc
        self._sel = sel
    def get_selected_entities(self):
        return [self.doc.get_entity_by_id(i) for i in self._sel]
    def array_rectangular(self, *a, **k):
        return self.doc.array_rectangular(*a, **k)
    def array_polar(self, *a, **k):
        return self.doc.array_polar(*a, **k)
    def prompt(self, m): pass
    def write(self, m): pass


def test_matriz_sin_seleccion_termina():
    doc = Document()
    cmd = MatrizCommand()
    assert cmd.start(FakeCtx(doc, [])) == CommandResult.FINISHED


def test_matriz_rectangular_flujo():
    doc = Document()
    line = doc.add_line(Point(0, 0), Point(10, 0))
    cmd = MatrizCommand()
    ctx = FakeCtx(doc, [line.id])

    cmd.start(ctx)
    assert cmd.handle_input(ctx, "R") == CommandResult.RUNNING
    cmd.handle_input(ctx, "2")     # filas
    cmd.handle_input(ctx, "3")     # columnas
    cmd.handle_input(ctx, "20")    # dx
    assert cmd.handle_input(ctx, "10") == CommandResult.FINISHED

    assert len(doc.entities) == 6   # 2x3 = 6 posiciones


def test_matriz_polar_flujo():
    doc = Document()
    circ = doc.add_circle(Point(20, 0), 5)
    cmd = MatrizCommand()
    ctx = FakeCtx(doc, [circ.id])

    cmd.start(ctx)
    cmd.handle_input(ctx, "P")
    cmd.handle_input(ctx, "0,0")   # centro
    cmd.handle_input(ctx, "4")     # elementos
    assert cmd.handle_input(ctx, "360") == CommandResult.FINISHED

    assert len(doc.entities) == 4   # original + 3 copias