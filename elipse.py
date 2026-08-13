# elipse.py

import math
from enum import Enum, auto

from core import (
    Command,
    CommandResult,
    Point,
    parse_point,
    parse_number,
)


class EllipseState(Enum):
    CENTER = auto()
    AXIS_1 = auto()
    AXIS_2 = auto()


class ElipseCommand(Command):
    name = "ELIPSE"
    aliases = ("EL", "ELLIPSE")

    def __init__(self):
        self.state = EllipseState.CENTER
        self.center = None
        self.radius_x = None
        self.rotation = 0.0

    def start(self, ctx):
        ctx.prompt("Centro de elipse:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando ELIPSE cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando ELIPSE cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # CENTRO
        # ----------------------------------------------------
        if self.state == EllipseState.CENTER:
            try:
                self.center = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Centro de elipse:")
                return CommandResult.RUNNING

            self.state = EllipseState.AXIS_1

            ctx.write(f"Centro: {self.center}")
            ctx.prompt(
                "Extremo del primer eje "
                "[punto / @dist<ángulo / número]:"
            )

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # PRIMER EJE
        # ----------------------------------------------------
        if self.state == EllipseState.AXIS_1:

            # Primero intentamos leer un número: radio directo
            try:
                radius_x = parse_number(text)
            except ValueError:
                radius_x = None

            if radius_x is not None:
                if radius_x <= 0:
                    ctx.write("El radio del eje debe ser mayor que cero.")
                    ctx.prompt("Extremo del primer eje:")
                    return CommandResult.RUNNING

                self.radius_x = radius_x
                self.rotation = 0.0

                self.state = EllipseState.AXIS_2

                ctx.write(f"Radio del primer eje: {self.radius_x}")
                ctx.prompt(
                    "Extremo del segundo eje "
                    "[punto / @dist<ángulo / número]:"
                )

                return CommandResult.RUNNING

            # Si no era número, lo tratamos como punto
            try:
                p = parse_point(text, self.center)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Extremo del primer eje:")
                return CommandResult.RUNNING

            dx = p.x - self.center.x
            dy = p.y - self.center.y

            radius_x = math.hypot(dx, dy)

            if radius_x <= 1e-9:
                ctx.write("El extremo del eje no puede coincidir con el centro.")
                ctx.prompt("Extremo del primer eje:")
                return CommandResult.RUNNING

            self.radius_x = radius_x
            self.rotation = math.degrees(math.atan2(dy, dx)) % 360.0

            self.state = EllipseState.AXIS_2

            ctx.write(
                f"Primer eje: radio={self.radius_x:.3f}, "
                f"rotación={self.rotation:.2f}°"
            )

            ctx.prompt(
                "Extremo del segundo eje "
                "[punto / @dist<ángulo / número]:"
            )

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # SEGUNDO EJE
        # ----------------------------------------------------
        if self.state == EllipseState.AXIS_2:

            # Primero intentamos leer un número: radio directo
            try:
                radius_y = parse_number(text)
            except ValueError:
                radius_y = None

            if radius_y is not None:
                if radius_y <= 0:
                    ctx.write("El radio del segundo eje debe ser mayor que cero.")
                    ctx.prompt("Extremo del segundo eje:")
                    return CommandResult.RUNNING

                ctx.add_ellipse(
                    self.center,
                    self.radius_x,
                    radius_y,
                    self.rotation,
                )

                ctx.write(
                    f"Elipse creada: centro={self.center}, "
                    f"rx={self.radius_x:.3f}, ry={radius_y:.3f}, "
                    f"rotación={self.rotation:.2f}°"
                )

                return CommandResult.FINISHED

            # Si no era número, lo tratamos como punto
            try:
                p = parse_point(text, self.center)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Extremo del segundo eje:")
                return CommandResult.RUNNING

            dx = p.x - self.center.x
            dy = p.y - self.center.y

            radius_y = math.hypot(dx, dy)

            if radius_y <= 1e-9:
                ctx.write("El extremo del eje no puede coincidir con el centro.")
                ctx.prompt("Extremo del segundo eje:")
                return CommandResult.RUNNING

            ctx.add_ellipse(
                self.center,
                self.radius_x,
                radius_y,
                self.rotation,
            )

            ctx.write(
                f"Elipse creada: centro={self.center}, "
                f"rx={self.radius_x:.3f}, ry={radius_y:.3f}, "
                f"rotación={self.rotation:.2f}°"
            )

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.state in (
            EllipseState.CENTER,
            EllipseState.AXIS_1,
            EllipseState.AXIS_2,
        )

    def get_point_base(self):
        if self.state in (
            EllipseState.AXIS_1,
            EllipseState.AXIS_2,
        ):
            return self.center

        return None