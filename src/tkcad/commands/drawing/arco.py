# arco.py

import math
from enum import Enum, auto
from typing import Optional

from ...core import  Command, CommandResult, Point, parse_point, parse_number
# from ...geometry import


class ArcState(Enum):
    CENTER = auto()
    START = auto()
    END = auto()
    EXTENT = auto()


class ArcCommand(Command):
    name = "ARCO"
    aliases = ("A", "ARC")

    def __init__(self):
        self.state = ArcState.CENTER
        self.center: Optional[Point] = None
        self.start_point: Optional[Point] = None
        self.radius: Optional[float] = None
        self.start_angle: Optional[float] = None

    def start(self, ctx):
        ctx.prompt("Centro del arco:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando ARCO cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando ARCO cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Pedir centro
        # ----------------------------------------------------
        if self.state == ArcState.CENTER:
            try:
                self.center = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Centro del arco:")
                return CommandResult.RUNNING

            self.state = ArcState.START
            ctx.write(f"Centro: {self.center}")
            ctx.prompt("Punto inicial [@dist<ángulo / punto absoluto]:")
            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Pedir punto inicial
        # ----------------------------------------------------
        if self.state == ArcState.START:
            try:
                p = parse_point(text, self.center)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Punto inicial [@dist<ángulo / punto absoluto]:")
                return CommandResult.RUNNING

            radius = math.hypot(
                p.x - self.center.x,
                p.y - self.center.y
            )

            if radius <= 1e-9:
                ctx.write("El punto inicial no puede coincidir con el centro.")
                ctx.prompt("Punto inicial [@dist<ángulo / punto absoluto]:")
                return CommandResult.RUNNING

            self.start_point = p
            self.radius = radius
            self.start_angle = math.degrees(
                math.atan2(
                    p.y - self.center.y,
                    p.x - self.center.x
                )
            )

            self.state = ArcState.END
            ctx.write(f"Punto inicial: {p}")
            ctx.prompt("Punto final [A=ángulo incluido]:")
            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Pedir punto final o ángulo incluido
        # ----------------------------------------------------
        if self.state == ArcState.END:
            option = text.upper()

            if option == "A":
                self.state = ArcState.EXTENT
                ctx.prompt("Ángulo incluido (grados):")
                return CommandResult.RUNNING

            try:
                p = parse_point(text, self.center)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Punto final [A=ángulo incluido]:")
                return CommandResult.RUNNING

            end_radius = math.hypot(
                p.x - self.center.x,
                p.y - self.center.y
            )

            if end_radius <= 1e-9:
                ctx.write("El punto final no puede coincidir con el centro.")
                ctx.prompt("Punto final [A=ángulo incluido]:")
                return CommandResult.RUNNING

            end_angle = math.degrees(
                math.atan2(
                    p.y - self.center.y,
                    p.x - self.center.x
                )
            )

            extent = (end_angle - self.start_angle) % 360.0

            if extent <= 1e-6:
                ctx.write("El punto final está en el mismo ángulo que el punto inicial.")
                ctx.prompt("Punto final [A=ángulo incluido]:")
                return CommandResult.RUNNING

            ctx.add_arc(
                self.center,
                self.radius,
                self.start_angle,
                extent
            )

            ctx.write(
                f"Arco creado: centro={self.center}, "
                f"radio={self.radius:.3f}, "
                f"inicio={self.start_angle:.2f}°, "
                f"extensión={extent:.2f}°"
            )

            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Pedir ángulo incluido
        # ----------------------------------------------------
        if self.state == ArcState.EXTENT:
            try:
                angle = parse_number(text)
            except ValueError:
                ctx.write("Ángulo no válido.")
                ctx.prompt("Ángulo incluido (grados):")
                return CommandResult.RUNNING

            if angle <= 0:
                ctx.write("El ángulo debe ser mayor que cero.")
                ctx.prompt("Ángulo incluido (grados):")
                return CommandResult.RUNNING

            if angle > 360:
                angle = 360

            ctx.add_arc(
                self.center,
                self.radius,
                self.start_angle,
                angle
            )

            ctx.write(
                f"Arco creado: centro={self.center}, "
                f"radio={self.radius:.3f}, "
                f"inicio={self.start_angle:.2f}°, "
                f"extensión={angle:.2f}°"
            )

            return CommandResult.FINISHED

        return CommandResult.FINISHED


    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == ArcState.END:
            options = ["A"]
            return [option for option in options if option.startswith(text)]

        return []

    def expects_point(self) -> bool:
        return self.state in (
            ArcState.CENTER,
            ArcState.START,
            ArcState.END,
        )

    def get_point_base(self):
        if self.state in (ArcState.START, ArcState.END):
            return self.center

        return None