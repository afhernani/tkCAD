# poligono.py

import math
from enum import Enum, auto
from typing import Optional, List

from ...core import  Command, CommandResult, Point, parse_point, parse_number
# from ...geometry import


class PolygonState(Enum):
    SIDES = auto()
    CENTER = auto()
    RADIUS = auto()


class PolygonCommand(Command):
    name = "POLIGONO"
    aliases = ("POL", "PG")

    def __init__(self):
        self.state = PolygonState.SIDES
        self.sides: Optional[int] = None
        self.center: Optional[Point] = None

    def start(self, ctx):
        ctx.prompt("Número de lados:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando POLIGONO cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando POLIGONO cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Pedir número de lados
        # ----------------------------------------------------
        if self.state == PolygonState.SIDES:
            try:
                value = parse_number(text)

                if not value.is_integer():
                    raise ValueError()

                sides = int(value)

                if sides < 3:
                    raise ValueError()

                self.sides = sides

            except ValueError:
                ctx.write("Número de lados no válido. Debe ser un entero mayor o igual que 3.")
                ctx.prompt("Número de lados:")
                return CommandResult.RUNNING

            self.state = PolygonState.CENTER
            ctx.write(f"Número de lados: {self.sides}")
            ctx.prompt("Centro del polígono:")
            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Pedir centro
        # ----------------------------------------------------
        if self.state == PolygonState.CENTER:
            try:
                self.center = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Centro del polígono:")
                return CommandResult.RUNNING

            self.state = PolygonState.RADIUS
            ctx.write(f"Centro: {self.center}")
            ctx.prompt("Radio [número / @dist<ángulo]:")
            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Pedir radio
        # ----------------------------------------------------
        if self.state == PolygonState.RADIUS:
            radius = None
            rotation = 0.0

            # Radio mediante punto relativo:
            # @100<0
            # @50,30
            if text.startswith("@"):
                try:
                    p = parse_point(text, self.center)
                except ValueError as ex:
                    ctx.write(f"Radio no válido: {ex}")
                    ctx.prompt("Radio [número / @dist<ángulo]:")
                    return CommandResult.RUNNING

                radius = math.hypot(
                    p.x - self.center.x,
                    p.y - self.center.y
                )

                if radius <= 1e-9:
                    ctx.write("El radio debe ser mayor que cero.")
                    ctx.prompt("Radio [número / @dist<ángulo]:")
                    return CommandResult.RUNNING

                rotation = math.atan2(
                    p.y - self.center.y,
                    p.x - self.center.x
                )

            # Radio numérico directo
            else:
                try:
                    radius = parse_number(text)
                except ValueError:
                    ctx.write("Radio no válido.")
                    ctx.prompt("Radio [número / @dist<ángulo]:")
                    return CommandResult.RUNNING

                if radius <= 0:
                    ctx.write("El radio debe ser mayor que cero.")
                    ctx.prompt("Radio [número / @dist<ángulo]:")
                    return CommandResult.RUNNING

            if radius is None or self.center is None or self.sides is None:
                ctx.write("Datos del polígono incompletos.")
                return CommandResult.FINISHED

            points: List[Point] = []

            step = 2.0 * math.pi / self.sides

            for i in range(self.sides):
                angle = rotation + i * step

                x = self.center.x + radius * math.cos(angle)
                y = self.center.y + radius * math.sin(angle)

                points.append(Point(x, y))

            ctx.add_polygon(points)

            ctx.write(
                f"Polígono creado: lados={self.sides}, "
                f"centro={self.center}, "
                f"radio={radius:.3f}"
            )

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == PolygonState.RADIUS:
            options = ["L"]
            return [option for option in options if option.startswith(text)]

        return []

    def expects_point(self) -> bool:
        return self.state == PolygonState.CENTER

    def get_point_base(self):
        return None