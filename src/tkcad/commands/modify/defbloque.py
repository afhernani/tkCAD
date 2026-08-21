from enum import Enum, auto

from ...core import Command, CommandResult, parse_point


class DefBloqueState(Enum):
    NAME = auto()
    BASE = auto()


class DefBloqueCommand(Command):
    name = "DEFBLOQUE"
    aliases = ("BDEF",)

    def __init__(self):
        self.state = DefBloqueState.NAME
        self.ids = []
        self.block_name = None

    def start(self, ctx):
        self.ids = [e.id for e in ctx.get_selected_entities()]
        if not self.ids:
            ctx.write("DEFBLOQUE: selecciona entidades antes de definir.")
            return CommandResult.FINISHED
        ctx.prompt("Nombre de la definición:")
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if text.upper() == "ESC":
            ctx.write("DEFBLOQUE cancelado.")
            return CommandResult.FINISHED

        if self.state == DefBloqueState.NAME:
            if not text:
                ctx.write("Escribe un nombre.")
                return CommandResult.RUNNING
            if text in ctx.block_defs:
                ctx.write("Ya existe una definición con ese nombre.")
                return CommandResult.RUNNING
            self.block_name = text
            self.state = DefBloqueState.BASE
            ctx.prompt("Punto base del bloque:")
            return CommandResult.RUNNING

        if self.state == DefBloqueState.BASE:
            try:
                base = parse_point(text)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                return CommandResult.RUNNING
            ctx.define_block_def(self.block_name, self.ids, base)
            ctx.write(
                f"Definición '{self.block_name}' creada "
                f"({len(self.ids)} entidades). Originales eliminados."
            )
            return CommandResult.FINISHED
        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.state == DefBloqueState.BASE