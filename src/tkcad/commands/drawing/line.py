# line.py

import math
from enum import Enum, auto
from typing import Optional, List

from ...core import  Command, CommandResult, Point, parse_point, parse_number
# from ...geometry import

# ============================================================
# Comando LINEA
# ============================================================

class LineState(Enum):
    FIRST_POINT = auto()
    NEXT_POINT = auto()
    LENGTH = auto()
    ANGLE = auto()


class LineCommand(Command):
    name = "LINEA"
    aliases = ("L", "LINE")

    def __init__(self):
        self.state = LineState.FIRST_POINT
        self.last: Optional[Point] = None
        self.length: Optional[float] = None
        self.angle: Optional[float] = None

    def start(self, ctx):
        ctx.prompt("Primer punto:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        # Enter vacío
        if not text:
            if self.state == LineState.FIRST_POINT:
                ctx.write("Comando LINEA cancelado.")
            else:
                ctx.write("Comando LINEA terminado.")
            return CommandResult.FINISHED

        # ESC
        if text.upper() == "ESC":
            ctx.write("Comando LINEA cancelado.")
            return CommandResult.FINISHED

        # Pedir primer punto
        if self.state == LineState.FIRST_POINT:
            try:
                p = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Primer punto:")
                return CommandResult.RUNNING

            self.last = p
            self.state = LineState.NEXT_POINT

            ctx.write(f"Primer punto: {p}")
            ctx.prompt(
                "Siguiente punto [@dx,dy / @dist<ángulo / L=longitud / A=ángulo / Enter=terminar]:"
            )
            return CommandResult.RUNNING

        # Pedir siguiente punto u opciones
        if self.state == LineState.NEXT_POINT:
            option = text.upper()

            if option == "L":
                self.state = LineState.LENGTH
                ctx.prompt("Longitud:")
                return CommandResult.RUNNING

            if option == "A":
                self.state = LineState.ANGLE
                ctx.prompt("Ángulo:")
                return CommandResult.RUNNING

            try:
                p = parse_point(text, self.last)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt(
                    "Siguiente punto [@dx,dy / @dist<ángulo / L=longitud / A=ángulo / Enter=terminar]:"
                )
                return CommandResult.RUNNING

            self._add_segment(ctx, p)
            return CommandResult.RUNNING

        # Pedir longitud
        if self.state == LineState.LENGTH:
            try:
                self.length = parse_number(text)
            except ValueError:
                ctx.write("Longitud no válida.")
                ctx.prompt("Longitud:")
                return CommandResult.RUNNING

            if self.angle is not None:
                self._add_polar_segment(ctx)
            else:
                self.state = LineState.ANGLE
                ctx.prompt("Ángulo:")

            return CommandResult.RUNNING

        # Pedir ángulo
        if self.state == LineState.ANGLE:
            try:
                self.angle = parse_number(text)
            except ValueError:
                ctx.write("Ángulo no válido.")
                ctx.prompt("Ángulo:")
                return CommandResult.RUNNING

            if self.length is not None:
                self._add_polar_segment(ctx)
            else:
                self.state = LineState.LENGTH
                ctx.prompt("Longitud:")

            return CommandResult.RUNNING

        return CommandResult.FINISHED

    def _add_polar_segment(self, ctx):
        if self.last is None or self.length is None or self.angle is None:
            return

        rad = math.radians(self.angle)

        p = Point(
            self.last.x + self.length * math.cos(rad),
            self.last.y + self.length * math.sin(rad),
        )

        self._add_segment(ctx, p)

        self.length = None
        self.angle = None

    def _add_segment(self, ctx, p: Point):
        if self.last is None:
            return

        ctx.add_line(self.last, p)
        ctx.write(f"Línea creada: {self.last} -> {p}")

        self.last = p
        self.state = LineState.NEXT_POINT

        ctx.prompt(
            "Siguiente punto [@dx,dy / @dist<ángulo / L=longitud / A=ángulo / Enter=terminar]:"
        )

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == LineState.NEXT_POINT:
            options = ["L", "A"]
            return [option for option in options if option.startswith(text)]

        return []

    def expects_point(self) -> bool:
        return self.state in (
            LineState.FIRST_POINT,
            LineState.NEXT_POINT,
        )

    def get_point_base(self):
        if self.state == LineState.NEXT_POINT:
            return self.last

        return None
