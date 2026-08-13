# mover.py

from enum import Enum, auto
from typing import Optional

from core import Command, CommandResult, Point, parse_point


class MoveState(Enum):
    TARGET = auto()
    BASE = auto()
    DEST = auto()


MOVE_TARGET_ALIASES = {
    "TODO": "TODO",
    "T": "TODO",
    "ALL": "TODO",

    "LINEA": "LINEA",
    "LINEAS": "LINEA",
    "L": "LINEA",

    "POLILINEA": "POLILINEA",
    "POLILINEAS": "POLILINEA",
    "PL": "POLILINEA",

    "CIRCULO": "CIRCULO",
    "CIRCULOS": "CIRCULO",
    "C": "CIRCULO",

    "ARCO": "ARCO",
    "ARCOS": "ARCO",
    "A": "ARCO",

    "POLIGONO": "POLIGONO",
    "POLIGONOS": "POLIGONO",
    "POL": "POLIGONO",
    "PG": "POLIGONO",

    "ELIPSE": "ELIPSE",
    "ELIPSES": "ELIPSE",
    "ELLIPSE": "ELIPSE",
    "EL": "ELIPSE",
}


class MoveCommand(Command):
    name = "MOVER"
    aliases = ("M", "MOVE", "MV")

    def __init__(self):
        self.state = MoveState.TARGET
        self.target: Optional[str] = None
        self.base: Optional[Point] = None
        self.use_selection = False

    def start(self, ctx):
        if ctx.has_selection():
            self.use_selection = True
            self.state = MoveState.BASE

            ctx.write(
                f"Moviendo {ctx.selection_count()} entidades seleccionadas."
            )
            ctx.prompt("Punto base:")
        else:
            self.use_selection = False
            self.state = MoveState.TARGET

            ctx.prompt(
                "No hay selección. Qué mover "
                "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
            )

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            if self.state == MoveState.TARGET:
                self.target = "TODO"
                self.state = MoveState.BASE

                ctx.write("Moviendo: TODO")
                ctx.prompt("Punto base:")

                return CommandResult.RUNNING

            ctx.write("Comando MOVER cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando MOVER cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Elegir objetivo si no hay selección
        # ----------------------------------------------------
        if self.state == MoveState.TARGET and not self.use_selection:
            key = text.upper()
            target = MOVE_TARGET_ALIASES.get(key)

            if target is None:
                ctx.write("Objetivo no válido.")
                ctx.prompt(
                    "Qué mover "
                    "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
                )
                return CommandResult.RUNNING

            self.target = target
            self.state = MoveState.BASE

            ctx.write(f"Moviendo: {target}")
            ctx.prompt("Punto base:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Punto base
        # ----------------------------------------------------
        if self.state == MoveState.BASE:
            try:
                self.base = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Punto base:")
                return CommandResult.RUNNING

            self.state = MoveState.DEST

            ctx.write(f"Punto base: {self.base}")
            ctx.prompt("Segundo punto [@dx,dy / @dist<ángulo / absoluto]:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Punto destino
        # ----------------------------------------------------
        if self.state == MoveState.DEST:
            try:
                dest = parse_point(text, self.base)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Segundo punto [@dx,dy / @dist<ángulo / absoluto]:")
                return CommandResult.RUNNING

            dx = dest.x - self.base.x
            dy = dest.y - self.base.y

            if self.use_selection:
                ctx.move_selected(dx, dy)
                ctx.write(
                    f"Selección movida: dx={dx:.3f}, dy={dy:.3f}"
                )
            else:
                ctx.move_entities(self.target, dx, dy)
                ctx.write(
                    f"Movido {self.target}: dx={dx:.3f}, dy={dy:.3f}"
                )

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == MoveState.TARGET and not self.use_selection:
            options = [
                "TODO",
                "LINEA",
                "POLILINEA",
                "CIRCULO",
                "ARCO",
                "POLIGONO",
            ]

            return [option for option in options if option.startswith(text)]

        return []

    def expects_point(self) -> bool:
        return self.state in (
            MoveState.BASE,
            MoveState.DEST,
        )

    def get_point_base(self):
        if self.state == MoveState.DEST:
            return self.base

        return None