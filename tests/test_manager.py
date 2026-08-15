from tkcad.core import (
    Command,
    CommandLineManager,
    CommandResult,
    Point,
)


class FakeCtx:
    def __init__(self):
        self.messages = []

    def write(self, text):
        self.messages.append(text)

    def prompt(self, text):
        self.messages.append(text)

    def clear_preview(self):
        pass


class DummyCommand(Command):
    name = "DUMMY"
    aliases = ("D",)

    def __init__(self):
        self.received = []

    def start(self, ctx):
        ctx.prompt("Punto:")

    def handle_input(self, ctx, text):
        self.received.append(text)
        if text == "FIN":
            return CommandResult.FINISHED
        return CommandResult.RUNNING


def test_register_incluye_nombre_y_alias():
    manager = CommandLineManager(FakeCtx())
    manager.register(DummyCommand)
    assert "DUMMY" in manager.get_available_command_names()
    manager.process_input("d")
    assert isinstance(manager.active, DummyCommand)


def test_comando_desconocido_no_activa_nada():
    ctx = FakeCtx()
    manager = CommandLineManager(ctx)
    manager.register(DummyCommand)
    manager.process_input("NOP")
    assert manager.active is None
    assert any("no reconocido" in m for m in ctx.messages)


def test_autocompletado_por_prefijo():
    manager = CommandLineManager(FakeCtx())
    manager.register(DummyCommand)
    assert manager.get_completions("DU") == ["DUMMY"]
    assert manager.get_completions("") == ["DUMMY"]


def test_ciclo_de_vida_del_comando():
    manager = CommandLineManager(FakeCtx())
    manager.register(DummyCommand)
    manager.process_input("DUMMY")
    assert manager.active is not None
    manager.process_input("algo")
    assert manager.active is not None
    manager.process_input("FIN")
    assert manager.active is None


def test_esc_cancela_el_comando():
    manager = CommandLineManager(FakeCtx())
    manager.register(DummyCommand)
    manager.process_input("DUMMY")
    manager.process_input("ESC")
    assert manager.active is None


def test_send_point_envia_coordenadas():
    manager = CommandLineManager(FakeCtx())
    manager.register(DummyCommand)
    manager.process_input("DUMMY")
    manager.send_point(Point(1.5, 2.5))
    assert manager.active.received[-1] == "1.500000;2.500000"