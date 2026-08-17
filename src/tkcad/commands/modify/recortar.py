# recortar.py

from enum import Enum, auto

from ...core import Command, CommandResult, parse_point

# Tipos de entidad válidos como LÍMITE de recorte
VALID_LIMIT_KINDS = {"line", "circle", "arc"}

# Tipos de entidad válidos como TARGET a recortar
VALID_TARGET_KINDS = {"line"}


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

        # ✏️ CAMBIO: mensaje actualizado con los tipos soportados
        ctx.write("RECORTAR soporta límites: LINEA, CIRCULO, ARCO.")
        ctx.write("Entidad a recortar: LINEA.")
        ctx.write("Usa LISTAR para ver los IDs de entidades.")

        ctx.prompt("ID de la entidad límite (o Enter para cancelar):")

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
        # ID entidad límite
        # ----------------------------------------------------
        if self.state == TrimState.LIMIT_ID:
            if not text.isdigit():
                ctx.write("Debes escribir un ID numérico.")
                ctx.prompt("ID de la entidad límite:")
                return CommandResult.RUNNING

            entity_id = int(text)
            entity = ctx.get_entity_by_id(entity_id)

            if entity is None:
                ctx.write(f"No existe la entidad {entity_id}.")
                ctx.prompt("ID de la entidad límite:")
                return CommandResult.RUNNING

            # ✏️ CAMBIO: validar contra el conjunto de tipos válidos
            if entity.kind not in VALID_LIMIT_KINDS:
                kinds_str = ", ".join(k.upper() for k in sorted(VALID_LIMIT_KINDS))
                ctx.write(
                    f"La entidad límite debe ser: {kinds_str}. "
                    f"(La entidad {entity_id} es {entity.kind.upper()}.)"
                )
                ctx.prompt("ID de la entidad límite:")
                return CommandResult.RUNNING

            self.limit_id = entity_id
            self.state = TrimState.TARGET_ID

            # ✏️ CAMBIO: mensaje genérico según el tipo
            ctx.write(f"Límite ({entity.kind.upper()}): {entity_id}")
            ctx.prompt("ID de la entidad a recortar:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # ID entidad a recortar
        # ----------------------------------------------------
        if self.state == TrimState.TARGET_ID:
            if not text.isdigit():
                ctx.write("Debes escribir un ID numérico.")
                ctx.prompt("ID de la entidad a recortar:")
                return CommandResult.RUNNING

            entity_id = int(text)

            if entity_id == self.limit_id:
                ctx.write("La entidad a recortar no puede ser la misma que el límite.")
                ctx.prompt("ID de la entidad a recortar:")
                return CommandResult.RUNNING

            entity = ctx.get_entity_by_id(entity_id)

            if entity is None:
                ctx.write(f"No existe la entidad {entity_id}.")
                ctx.prompt("ID de la entidad a recortar:")
                return CommandResult.RUNNING

            # ✏️ CAMBIO: validar contra el conjunto de targets válidos
            if entity.kind not in VALID_TARGET_KINDS:
                kinds_str = ", ".join(k.upper() for k in sorted(VALID_TARGET_KINDS))
                ctx.write(
                    f"La entidad a recortar debe ser: {kinds_str}. "
                    f"(La entidad {entity_id} es {entity.kind.upper()}.)"
                )
                ctx.prompt("ID de la entidad a recortar:")
                return CommandResult.RUNNING

            self.target_id = entity_id
            self.state = TrimState.KEEP_POINT

            ctx.write(f"Entidad a recortar ({entity.kind.upper()}): {entity_id}")
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

            # ✏️ CAMBIO: usar el dispatcher genérico en vez de trim_line_by_line
            ctx.mark_action()
            ok, message = ctx.trim_by_entity(
                self.limit_id,
                self.target_id,
                keep_point,
            )
            ctx.commit_action()

            ctx.write(message)

            # Si falló, revertir el snapshot vacío
            if not ok:
                ctx.undo()

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.state == TrimState.KEEP_POINT

    def get_point_base(self):
        return None