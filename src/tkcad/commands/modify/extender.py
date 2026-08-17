# extender.py

from enum import Enum, auto

from ...core import  Command, CommandResult
# from ...geometry import
# from ..view.snap import 
# from ..view.seleccion import

class ExtendState(Enum):
    LIMIT_ID = auto()
    TARGET_ID = auto()


class ExtendCommand(Command):
    name = "EXTENDER"
    aliases = ("EX", "EXTEND")

    def __init__(self):
        self.state = ExtendState.LIMIT_ID
        self.limit_id = None

    def start(self, ctx):
        if not ctx.entities:
            ctx.write("No hay entidades para extender.")
            return CommandResult.FINISHED

        ctx.write("Por ahora EXTENDER funciona con LINEA y límite LINEA.")
        ctx.write("Usa LISTAR para ver los IDs de entidades.")

        ctx.prompt("ID de la línea límite:")

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando EXTENDER cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando EXTENDER cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # ID línea límite
        # ----------------------------------------------------
        if self.state == ExtendState.LIMIT_ID:
            if not text.isdigit():
                ctx.write("Debes escribir un ID numérico.")
                ctx.prompt("ID de la línea límite:")
                return CommandResult.RUNNING

            entity_id = int(text)
            entity = ctx.get_entity_by_id(entity_id)

            if entity is None:
                ctx.write(f"No existe la entidad {entity_id}.")
                ctx.prompt("ID de la línea límite:")
                return CommandResult.RUNNING

            if entity.kind != "line":
                ctx.write("Por ahora la entidad límite debe ser una LINEA.")
                ctx.prompt("ID de la línea límite:")
                return CommandResult.RUNNING

            self.limit_id = entity_id
            self.state = ExtendState.TARGET_ID

            ctx.write(f"Línea límite: {entity_id}")
            ctx.prompt("ID de la línea a extender:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # ID línea a extender
        # ----------------------------------------------------
        if self.state == ExtendState.TARGET_ID:
            if not text.isdigit():
                ctx.write("Debes escribir un ID numérico.")
                ctx.prompt("ID de la línea a extender:")
                return CommandResult.RUNNING

            entity_id = int(text)

            if entity_id == self.limit_id:
                ctx.write("La entidad a extender no puede ser la misma que el límite.")
                ctx.prompt("ID de la línea a extender:")
                return CommandResult.RUNNING

            entity = ctx.get_entity_by_id(entity_id)

            if entity is None:
                ctx.write(f"No existe la entidad {entity_id}.")
                ctx.prompt("ID de la línea a extender:")
                return CommandResult.RUNNING

            if entity.kind != "line":
                ctx.write("Por ahora la entidad a extender debe ser una LINEA.")
                ctx.prompt("ID de la línea a extender:")
                return CommandResult.RUNNING

            ok, message = ctx.extend_line_to_line(
                self.limit_id,
                entity_id,
            )

            ctx.write(message)

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def expects_entity(self) -> bool:
        return self.state in (ExtendState.LIMIT_ID, ExtendState.TARGET_ID)  # ajusta a tu Enum