# rotar.py

from enum import Enum, auto

from ...core import (
    Command,
    CommandResult,
    parse_point,
    parse_number,
    TARGET_ALIASES,
)
# from ...geometry import

class RotateState(Enum):
    TARGET = auto()
    BASE = auto()
    ANGLE = auto()


ROTATE_TARGET_OPTIONS = [
    "TODO",
    "LINEA",
    "POLILINEA",
    "CIRCULO",
    "ARCO",
    "POLIGONO",
    "ELIPSE",
]


class RotateCommand(Command):
    name = "ROTAR"
    aliases = ("R", "ROTATE", "RO")

    def __init__(self):
        self.state = RotateState.TARGET
        self.target = None
        self.base = None
        self.use_selection = False

    def start(self, ctx):
        if not ctx.entities:
            ctx.write("No hay entidades para rotar.")
            return CommandResult.FINISHED

        if ctx.has_selection():
            self.use_selection = True
            self.state = RotateState.BASE

            ctx.write(
                f"Rotando {ctx.selection_count()} entidades seleccionadas."
            )
            ctx.prompt("Punto base:")

        else:
            self.use_selection = False
            self.state = RotateState.TARGET

            ctx.prompt(
                "No hay selección. Qué rotar "
                "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
            )

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando ROTAR cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando ROTAR cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Elegir objetivo si no hay selección
        # ----------------------------------------------------
        if self.state == RotateState.TARGET and not self.use_selection:
            target = TARGET_ALIASES.get(text.upper())

            if target is None:
                ctx.write("Objetivo no válido.")
                ctx.prompt(
                    "Qué rotar "
                    "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
                )
                return CommandResult.RUNNING

            self.target = target
            self.state = RotateState.BASE

            ctx.write(f"Rotando: {target}")
            ctx.prompt("Punto base:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Punto base
        # ----------------------------------------------------
        if self.state == RotateState.BASE:
            try:
                self.base = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Punto base:")
                return CommandResult.RUNNING

            self.state = RotateState.ANGLE

            ctx.write(f"Punto base: {self.base}")
            ctx.prompt("Ángulo (grados):")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Ángulo
        # ----------------------------------------------------
        if self.state == RotateState.ANGLE:
            try:
                angle = parse_number(text)
            except ValueError:
                ctx.write("Ángulo no válido.")
                ctx.prompt("Ángulo (grados):")
                return CommandResult.RUNNING

            if abs(angle) < 1e-9:
                ctx.write("Ángulo cero. No se rota nada.")
                return CommandResult.FINISHED

            if self.use_selection:
                count = ctx.rotate_selected(self.base, angle)
            else:
                count = ctx.rotate_entities(self.target, self.base, angle)

            ctx.write(f"Entidades rotadas: {count}")

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == RotateState.TARGET and not self.use_selection:
            return [
                option
                for option in ROTATE_TARGET_OPTIONS
                if option.startswith(text)
            ]

        return []

    def expects_point(self) -> bool:
        return self.state == RotateState.BASE

    def get_point_base(self):
        return None