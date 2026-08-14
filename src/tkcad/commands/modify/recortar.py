# recortar.py

from enum import Enum, auto

from ...core import Command, CommandResult, parse_point
# from ...geometry import
# from ..view.snap import 
# from ..view.seleccion import

class TrimState(Enum):
    LIMIT_ID = auto()
    TARGET_ID = auto()
    KEEP_POINT = auto()


class TrimCommand(Command):
    name = "RECORTAR"
    aliases = ("TR", "TRIM", "RT")

    def __init__(self):
        self.state = TrimState.LIMIT_ID
        self.limit_id = None
        self.target_id = None

    def start(self, ctx):
        if not ctx.entities:
            ctx.write("No hay entidades para recortar.")
            return CommandResult.FINISHED

        ctx.write("Por ahora RECORTAR funciona con LINEA y límite LINEA.")
        ctx.write("Usa LISTAR para ver los IDs de entidades.")

        ctx.prompt("ID de la línea límite:")

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando RECORTAR cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando RECORTAR cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # ID línea límite
        # ----------------------------------------------------
        if self.state == TrimState.LIMIT_ID:
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
            self.state = TrimState.TARGET_ID

            ctx.write(f"Línea límite: {entity_id}")
            ctx.prompt("ID de la línea a recortar:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # ID línea a recortar
        # ----------------------------------------------------
        if self.state == TrimState.TARGET_ID:
            if not text.isdigit():
                ctx.write("Debes escribir un ID numérico.")
                ctx.prompt("ID de la línea a recortar:")
                return CommandResult.RUNNING

            entity_id = int(text)

            if entity_id == self.limit_id:
                ctx.write("La entidad a recortar no puede ser la misma que el límite.")
                ctx.prompt("ID de la línea a recortar:")
                return CommandResult.RUNNING

            entity = ctx.get_entity_by_id(entity_id)

            if entity is None:
                ctx.write(f"No existe la entidad {entity_id}.")
                ctx.prompt("ID de la línea a recortar:")
                return CommandResult.RUNNING

            if entity.kind != "line":
                ctx.write("Por ahora la entidad a recortar debe ser una LINEA.")
                ctx.prompt("ID de la línea a recortar:")
                return CommandResult.RUNNING

            self.target_id = entity_id
            self.state = TrimState.KEEP_POINT

            ctx.write(f"Línea a recortar: {entity_id}")
            ctx.prompt("Punto a conservar:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Punto a conservar
        # ----------------------------------------------------
        if self.state == TrimState.KEEP_POINT:
            try:
                keep_point = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Punto a conservar:")
                return CommandResult.RUNNING

            ok, message = ctx.trim_line_by_line(
                self.limit_id,
                self.target_id,
                keep_point,
            )

            ctx.write(message)

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.state == TrimState.KEEP_POINT

    def get_point_base(self):
        return None