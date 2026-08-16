from tkcad.core import CommandLineManager, Document
from tkcad.commands.view.capa import CapaCommand


class SpyCtx(Document):
    def __init__(self):
        super().__init__()
        self.messages = []

    def write(self, text):
        self.messages.append(text)

    def prompt(self, text):
        self.messages.append(text)

    def clear_preview(self):
        pass


def make_manager():
    ctx = SpyCtx()
    manager = CommandLineManager(ctx)
    manager.register(CapaCommand)
    return ctx, manager


def test_capa_crea_y_cambia_capa_actual():
    ctx, manager = make_manager()
    manager.process_input("CAPA")
    manager.process_input("muros")
    assert "muros" in ctx.layers
    assert ctx.current_layer == "muros"
    manager.process_input("")
    assert manager.active is None


def test_capa_off_y_on():
    ctx, manager = make_manager()
    manager.process_input("CAPA")
    manager.process_input("muros")
    manager.process_input("OFF muros")
    assert ctx.layers["muros"].visible is False
    manager.process_input("ON muros")
    assert ctx.layers["muros"].visible is True


def test_capa_color():
    ctx, manager = make_manager()
    manager.process_input("CAPA")
    manager.process_input("muros")
    manager.process_input("COLOR muros red")
    assert ctx.layers["muros"].color == "red"


def test_capa_bloq_y_desbloq():
    ctx, manager = make_manager()
    manager.process_input("CAPA")
    manager.process_input("muros")
    manager.process_input("BLOQ muros")
    assert ctx.layers["muros"].locked is True
    manager.process_input("DESBLOQ muros")
    assert ctx.layers["muros"].locked is False


def test_capa_del_protegido():
    ctx, manager = make_manager()
    manager.process_input("CAPA")
    manager.process_input("DEL 0")            # la 0 nunca
    assert "0" in ctx.layers
    manager.process_input("muros")           # ahora muros es la actual
    manager.process_input("DEL muros")       # la actual tampoco
    assert "muros" in ctx.layers
    manager.process_input("0")
    manager.process_input("DEL muros")       # vacía y no actual: sí
    assert "muros" not in ctx.layers