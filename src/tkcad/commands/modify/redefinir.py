from enum import Enum, auto

from ...core import Command, CommandResult, parse_point


class RedefState(Enum):
    NAME = auto()
    BASE = auto()


class RedefinirCommand(Command):
    name = "REDEF"
    aliases = ("REDEFINE",)

    def __init__(self):
        self.state = RedefState.NAME
        self.ids = []
        self.block_name = None

    def start(self, ctx):
        self.ids = [e.id for e in ctx.get_selected_entities()]
        if not self.ids:
            ctx.write("REDEF: selecciona las entidades nuevas del bloque.")
            return CommandResult.FINISHED
        if not ctx.block_defs:
            ctx.write("REDEF: no hay definiciones que redefinir.")
            return CommandResult.FINISHED
        nombres = ", ".join(sorted(ctx.block_defs))
        ctx.prompt(f"Definición a actualizar [{nombres}]:")
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if text.upper() == "ESC":
            ctx.write("REDEF cancelado.")
            return CommandResult.FINISHED

        if self.state == RedefState.NAME:
            if text not in ctx.block_defs:
                ctx.write("Definición no encontrada.")
                return CommandResult.RUNNING
            self.block_name = text
            self.state = RedefState.BASE
            ctx.prompt("Nuevo punto base:")
            return CommandResult.RUNNING

        if self.state == RedefState.BASE:
            try:
                base = parse_point(text)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                return CommandResult.RUNNING
            ctx.redefine_block_def(self.block_name, self.ids, base)
            ctx.write(
                f"Definición '{self.block_name}' actualizada "
                f"({len(self.ids)} entidades). Todos los inserts cambian."
            )
            return CommandResult.FINISHED
        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.state == RedefState.BASE

    def get_completions(self, ctx, text: str):
        if self.state == RedefState.NAME:
            t = text.upper()
            return [n for n in sorted(ctx.block_defs)
                    if n.upper().startswith(t)]
        return []