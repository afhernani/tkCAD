from enum import Enum, auto

from ...core import Command, CommandResult, parse_point, parse_number


class InsertarState(Enum):
    NAME = auto()
    POS = auto()
    ROT = auto()
    SCALE = auto()


class InsertarCommand(Command):
    name = "INSERTAR"
    aliases = ("INSERT", "INS")

    def __init__(self):
        self.state = InsertarState.NAME
        self.block_name = None
        self.pos = None
        self.rot = 0.0
        self.scale = 1.0

    def start(self, ctx):
        if not ctx.block_defs:
            ctx.write("INSERTAR: no hay definiciones. Usa DEFBLOQUE primero.")
            return CommandResult.FINISHED
        nombres = ", ".join(sorted(ctx.block_defs))
        ctx.prompt(f"Nombre del bloque [{nombres}]:")
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if text.upper() == "ESC":
            ctx.write("INSERTAR cancelado.")
            return CommandResult.FINISHED

        if self.state == InsertarState.NAME:
            if text not in ctx.block_defs:
                ctx.write("Definición no encontrada.")
                return CommandResult.RUNNING
            self.block_name = text
            self.state = InsertarState.POS
            ctx.prompt("Punto de inserción:")
            return CommandResult.RUNNING

        if self.state == InsertarState.POS:
            try:
                self.pos = parse_point(text)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                return CommandResult.RUNNING
            self.state = InsertarState.ROT
            ctx.prompt("Rotación <0>:")
            return CommandResult.RUNNING

        if self.state == InsertarState.ROT:
            if text:
                try:
                    self.rot = parse_number(text)
                except ValueError:
                    ctx.write("Ángulo no válido.")
                    return CommandResult.RUNNING
            self.state = InsertarState.SCALE
            ctx.prompt("Escala <1>:")
            return CommandResult.RUNNING

        if self.state == InsertarState.SCALE:
            if text:
                try:
                    v = parse_number(text)
                except ValueError:
                    ctx.write("Escala no válida.")
                    return CommandResult.RUNNING
                if v <= 0:
                    ctx.write("La escala debe ser positiva.")
                    return CommandResult.RUNNING
                self.scale = v
            ins = ctx.insert_block(self.block_name, self.pos,
                                   self.rot, self.scale)
            if ins is not None:
                ctx.set_selection_ids([ins.id])
                ctx.write(f"Insertado '{self.block_name}'.")
            return CommandResult.FINISHED
        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.state == InsertarState.POS

    def get_completions(self, ctx, text: str):
        if self.state == InsertarState.NAME:
            t = text.upper()
            return [n for n in sorted(ctx.block_defs)
                    if n.upper().startswith(t)]
        return []