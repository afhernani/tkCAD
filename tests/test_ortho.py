from tkcad.core import CommandLineManager, Point, SnapEngine
from tkcad.commands.drawing.line import LineCommand
from tkcad.commands.view.ortho import OrthoCommand


class FakeApp:
    def __init__(self):
        self.snaps = SnapEngine()
        self.entities = []
        self.lines = []
        self.messages = []

    # interfaz que usan los comandos
    def write(self, text):
        self.messages.append(text)

    def prompt(self, text):
        self.messages.append(text)

    def clear_preview(self):
        pass

    def show_preview_polyline(self, points):
        pass

    def add_line(self, start, end):
        self.lines.append((start, end))

    # interfaz de app
    def toggle_ortho(self):
        activo = self.snaps.toggle_snap_mode("ORTHO")
        self.write(f"ORTHO {'activado' if activo else 'desactivado'}.")
        return activo

    def snap_point(self, p, base_point=None, ignore_entity_id=None):
        return self.snaps.snap_point(
            self.entities, p,
            base_point=base_point,
            ignore_entity_id=ignore_entity_id,
        )

    def mark_action(self):
        pass

    def commit_action(self):
        pass


def test_ortho_activa_desactiva_y_termina_solo():
    ctx = FakeApp()
    manager = CommandLineManager(ctx)
    manager.register(OrthoCommand)
    manager.process_input("ORTHO")
    assert "ORTHO" in ctx.snaps.snap_modes
    assert manager.active is None          # comando instantáneo
    manager.process_input("ORTHO")
    assert "ORTHO" not in ctx.snaps.snap_modes


def test_linea_con_ortho_queda_axial():
    ctx = FakeApp()
    ctx.toggle_ortho()
    manager = CommandLineManager(ctx)
    manager.register(LineCommand)
    manager.process_input("LINEA")
    manager.process_input("0,0")
    # Un clic en (30,12) se fuerza al eje horizontal: (30,0)
    p, kind = ctx.snap_point(Point(30, 12), base_point=Point(0, 0))
    assert kind == "ORTHO"
    manager.send_point(p)
    assert ctx.lines[0] == (Point(0, 0), Point(30, 0))