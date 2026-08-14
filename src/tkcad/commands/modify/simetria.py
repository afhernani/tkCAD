# simetria.py

from enum import Enum, auto

from ...core import (
    Command,
    CommandResult,
    parse_point,
    TARGET_ALIASES,
)
# from ...geometry import

class MirrorState(Enum):
    TARGET = auto()
    AXIS_1 = auto()
    AXIS_2 = auto()


MIRROR_TARGET_OPTIONS = [
    "TODO",
    "LINEA",
    "POLILINEA",
    "CIRCULO",
    "ARCO",
    "POLIGONO",
]


class MirrorCommand(Command):
    name = "SIMETRIA"
    aliases = ("SIM", "MIRROR", "MI")

    def __init__(self):
        self.state = MirrorState.TARGET
        self.target = None
        self.axis_1 = None
        self.use_selection = False

    def start(self, ctx):
        if not ctx.entities:
            ctx.write("No hay entidades para hacer simetría.")
            return CommandResult.FINISHED

        if ctx.has_selection():
            self.use_selection = True
            self.state = MirrorState.AXIS_1

            ctx.write(
                f"Haciendo simetría de {ctx.selection_count()} entidades seleccionadas."
            )
            ctx.prompt("Primer punto del eje de simetría:")

        else:
            self.use_selection = False
            self.state = MirrorState.TARGET

            ctx.prompt(
                "No hay selección. Qué simetrizar "
                "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
            )

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando SIMETRIA cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando SIMETRIA cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Elegir objetivo si no hay selección
        # ----------------------------------------------------
        if self.state == MirrorState.TARGET and not self.use_selection:
            target = TARGET_ALIASES.get(text.upper())

            if target is None:
                ctx.write("Objetivo no válido.")
                ctx.prompt(
                    "Qué simetrizar "
                    "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
                )
                return CommandResult.RUNNING

            self.target = target
            self.state = MirrorState.AXIS_1

            ctx.write(f"Simetrizando: {target}")
            ctx.prompt("Primer punto del eje de simetría:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Primer punto del eje
        # ----------------------------------------------------
        if self.state == MirrorState.AXIS_1:
            try:
                self.axis_1 = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Primer punto del eje de simetría:")
                return CommandResult.RUNNING

            self.state = MirrorState.AXIS_2

            ctx.write(f"Primer punto del eje: {self.axis_1}")
            ctx.prompt("Segundo punto del eje de simetría:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Segundo punto del eje
        # ----------------------------------------------------
        if self.state == MirrorState.AXIS_2:
            try:
                axis_2 = parse_point(text, self.axis_1)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Segundo punto del eje de simetría:")
                return CommandResult.RUNNING

            if (
                abs(axis_2.x - self.axis_1.x) < 1e-9
                and abs(axis_2.y - self.axis_1.y) < 1e-9
            ):
                ctx.write("El eje de simetría no puede ser un punto.")
                ctx.prompt("Segundo punto del eje de simetría:")
                return CommandResult.RUNNING

            if self.use_selection:
                count = ctx.mirror_selected(self.axis_1, axis_2)
            else:
                count = ctx.mirror_entities(self.target, self.axis_1, axis_2)

            ctx.write(f"Entidades simetrizadas: {count}")

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == MirrorState.TARGET and not self.use_selection:
            return [
                option
                for option in MIRROR_TARGET_OPTIONS
                if option.startswith(text)
            ]

        return []

    def expects_point(self) -> bool:
        return self.state in (
            MirrorState.AXIS_1,
            MirrorState.AXIS_2,
        )

    def get_point_base(self):
        if self.state == MirrorState.AXIS_2:
            return self.axis_1

        return None