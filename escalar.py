# escalar.py

from enum import Enum, auto

from core import (
    Command,
    CommandResult,
    parse_point,
    parse_number,
    TARGET_ALIASES,
)


class ScaleState(Enum):
    TARGET = auto()
    BASE = auto()
    FACTOR = auto()


SCALE_TARGET_OPTIONS = [
    "TODO",
    "LINEA",
    "POLILINEA",
    "CIRCULO",
    "ARCO",
    "POLIGONO",
]


class ScaleCommand(Command):
    name = "ESCALAR"
    aliases = ("ES", "SCALE", "SC")

    def __init__(self):
        self.state = ScaleState.TARGET
        self.target = None
        self.base = None
        self.use_selection = False

    def start(self, ctx):
        if not ctx.entities:
            ctx.write("No hay entidades para escalar.")
            return CommandResult.FINISHED

        if ctx.has_selection():
            self.use_selection = True
            self.state = ScaleState.BASE

            ctx.write(
                f"Escalando {ctx.selection_count()} entidades seleccionadas."
            )
            ctx.prompt("Punto base:")

        else:
            self.use_selection = False
            self.state = ScaleState.TARGET

            ctx.prompt(
                "No hay selección. Qué escalar "
                "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
            )

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando ESCALAR cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando ESCALAR cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Elegir objetivo si no hay selección
        # ----------------------------------------------------
        if self.state == ScaleState.TARGET and not self.use_selection:
            target = TARGET_ALIASES.get(text.upper())

            if target is None:
                ctx.write("Objetivo no válido.")
                ctx.prompt(
                    "Qué escalar "
                    "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
                )
                return CommandResult.RUNNING

            self.target = target
            self.state = ScaleState.BASE

            ctx.write(f"Escalando: {target}")
            ctx.prompt("Punto base:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Punto base
        # ----------------------------------------------------
        if self.state == ScaleState.BASE:
            try:
                self.base = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Punto base:")
                return CommandResult.RUNNING

            self.state = ScaleState.FACTOR

            ctx.write(f"Punto base: {self.base}")
            ctx.prompt("Factor de escala:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Factor de escala
        # ----------------------------------------------------
        if self.state == ScaleState.FACTOR:
            try:
                factor = parse_number(text)
            except ValueError:
                ctx.write("Factor no válido.")
                ctx.prompt("Factor de escala:")
                return CommandResult.RUNNING

            if factor <= 0:
                ctx.write("El factor debe ser mayor que cero.")
                ctx.prompt("Factor de escala:")
                return CommandResult.RUNNING

            if self.use_selection:
                count = ctx.scale_selected(self.base, factor)
            else:
                count = ctx.scale_entities(self.target, self.base, factor)

            ctx.write(f"Entidades escaladas: {count}")

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == ScaleState.TARGET and not self.use_selection:
            return [
                option
                for option in SCALE_TARGET_OPTIONS
                if option.startswith(text)
            ]

        return []

    def expects_point(self) -> bool:
        return self.state == ScaleState.BASE

    def get_point_base(self):
        return None