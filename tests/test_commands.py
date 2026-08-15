from tkcad.core import CommandLineManager, Point
from tkcad.commands.drawing.line import LineCommand
from tkcad.commands.drawing.poliline import PolylineCommand


class FakeCtx:
    """Espía: registra todo lo que los comandos piden a la app."""

    def __init__(self):
        self.messages = []
        self.lines = []
        self.polylines = []
        self.previews = []
        self.preview_cleared = 0

    def write(self, text):
        self.messages.append(text)

    def prompt(self, text):
        self.messages.append(text)

    def clear_preview(self):
        self.preview_cleared += 1

    def show_preview_polyline(self, points):
        self.previews.append(list(points))

    def add_line(self, start, end):
        self.lines.append((start, end))

    def add_polyline(self, points):
        self.polylines.append(list(points))


def make_manager():
    ctx = FakeCtx()
    manager = CommandLineManager(ctx)
    manager.register(LineCommand)
    manager.register(PolylineCommand)
    return ctx, manager


# --------------------------------------------------------
# LINEA
# --------------------------------------------------------
def test_linea_crea_segmento_y_sigue_encadenada():
    ctx, manager = make_manager()
    manager.process_input("LINEA")
    manager.process_input("0,0")
    manager.process_input("10,0")
    assert len(ctx.lines) == 1
    assert ctx.lines[0] == (Point(0, 0), Point(10, 0))
    assert manager.active is not None  # encadenada: sigue pidiendo puntos


def test_linea_termina_con_enter_y_limpia_preview():
    ctx, manager = make_manager()
    manager.process_input("LINEA")
    manager.process_input("0,0")
    manager.process_input("10,0")
    manager.process_input("")
    assert manager.active is None
    assert ctx.preview_cleared >= 1


def test_linea_punto_relativo():
    ctx, manager = make_manager()
    manager.process_input("LINEA")
    manager.process_input("10,10")
    manager.process_input("@5,-5")
    assert ctx.lines[0] == (Point(10, 10), Point(15, 5))


def test_linea_opciones_longitud_y_angulo():
    ctx, manager = make_manager()
    manager.process_input("LINEA")
    manager.process_input("0,0")
    manager.process_input("L")
    manager.process_input("10")
    manager.process_input("0")  # ángulo 0 grados
    assert ctx.lines[0] == (Point(0, 0), Point(10, 0))


def test_linea_ancla_el_hilo_en_el_primer_punto():
    ctx, manager = make_manager()
    manager.process_input("LINEA")
    manager.process_input("3,4")
    assert ctx.previews[-1] == [Point(3, 4)]


def test_alias_L_arranca_linea():
    ctx, manager = make_manager()
    manager.process_input("L")
    assert isinstance(manager.active, LineCommand)


# --------------------------------------------------------
# POLILINEA
# --------------------------------------------------------
def test_polilinea_crea_con_enter():
    ctx, manager = make_manager()
    manager.process_input("POLILINEA")
    manager.process_input("0,0")
    manager.process_input("10,0")
    manager.process_input("10,10")
    manager.process_input("")
    assert len(ctx.polylines) == 1
    assert ctx.polylines[0] == [Point(0, 0), Point(10, 0), Point(10, 10)]
    assert manager.active is None


def test_polilinea_cierra_con_C():
    ctx, manager = make_manager()
    manager.process_input("PL")
    manager.process_input("0,0")
    manager.process_input("10,0")
    manager.process_input("10,10")
    manager.process_input("C")
    assert len(ctx.polylines) == 1
    puntos = ctx.polylines[0]
    assert puntos[0] == puntos[-1]  # cerrada
    assert len(puntos) == 4


def test_polilinea_C_necesita_tres_puntos():
    ctx, manager = make_manager()
    manager.process_input("PL")
    manager.process_input("0,0")
    manager.process_input("10,0")
    manager.process_input("C")
    assert len(ctx.polylines) == 0
    assert manager.active is not None


def test_polilinea_con_un_punto_cancela():
    ctx, manager = make_manager()
    manager.process_input("PL")
    manager.process_input("0,0")
    manager.process_input("")
    assert len(ctx.polylines) == 0
    assert manager.active is None