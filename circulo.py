
import math
from enum import Enum, auto
from typing import Optional
from core import Command, CommandResult, Point, parse_number, parse_point

class CircleState(Enum):
    CENTER = auto()
    RADIUS = auto()
    DIAMETER = auto()


class CircleCommand(Command):
    name = "CIRCULO"
    aliases = ("C", "CIRCLE")

    def __init__(self):
        self.state = CircleState.CENTER
        self.center: Optional[Point] = None

    def start(self, ctx):
        """
        Este método se ejecuta cuando el usuario escribe CIRCULO.
        """
        ctx.prompt("Centro del círculo:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        """
        Este método recibe cada texto que escribe el usuario
        mientras el comando CIRCULO está activo.
        """
        text = text.strip()

        # Enter vacío cancela el comando
        if not text:
            ctx.write("Comando CIRCULO cancelado.")
            return CommandResult.FINISHED

        # ESC también cancela
        if text.upper() == "ESC":
            ctx.write("Comando CIRCULO cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # ESTADO 1: pedir centro
        # ----------------------------------------------------
        if self.state == CircleState.CENTER:
            try:
                self.center = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Centro del círculo:")
                return CommandResult.RUNNING

            self.state = CircleState.RADIUS

            ctx.write(f"Centro: {self.center}")
            ctx.prompt("Radio [D=diámetro / @dx,dy / @dist<ángulo]:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # ESTADO 2: pedir radio
        # ----------------------------------------------------
        if self.state == CircleState.RADIUS:
            option = text.upper()

            # Opción D: pedir diámetro
            if option == "D":
                self.state = CircleState.DIAMETER
                ctx.prompt("Diámetro:")
                return CommandResult.RUNNING

            # ----------------------------------------------------
            # Punto claramente relativo o polar:
            #
            # @50,0
            # @100<45
            # 100<45
            # ----------------------------------------------------
            if text.startswith("@") or "<" in text:
                try:
                    p = parse_point(text, self.center)
                except ValueError as ex:
                    ctx.write(f"Radio no válido: {ex}")
                    ctx.prompt("Radio [D=diámetro / número / punto]:")
                    return CommandResult.RUNNING

                radius = math.hypot(
                    p.x - self.center.x,
                    p.y - self.center.y
                )

                if radius <= 1e-9:
                    ctx.write("El radio debe ser mayor que cero.")
                    ctx.prompt("Radio [D=diámetro / número / punto]:")
                    return CommandResult.RUNNING

                ctx.add_circle(self.center, radius)

                ctx.write(
                    f"Círculo creado: centro={self.center}, radio={radius:.3f}"
                )

                return CommandResult.RUNNING if False else CommandResult.FINISHED

            # ----------------------------------------------------
            # Intentar leer como número.
            #
            # Esto acepta:
            #
            # 50
            # 25.5
            # 25,5
            #
            # Importante:
            # Si el usuario escribe 10,5 se interpreta como radio 10.5
            # ----------------------------------------------------
            try:
                radius = parse_number(text)
            except ValueError:
                radius = None

            if radius is not None:
                if radius <= 0:
                    ctx.write("El radio debe ser mayor que cero.")
                    ctx.prompt("Radio [D=diámetro / número / punto]:")
                    return CommandResult.RUNNING

                ctx.add_circle(self.center, radius)

                ctx.write(
                    f"Círculo creado: centro={self.center}, radio={radius:.3f}"
                )

                return CommandResult.FINISHED

            # ----------------------------------------------------
            # Si no era un número, intentamos leerlo como punto.
            #
            # Por ejemplo, un clic del ratón puede enviar algo como:
            #
            # 120.500000,80.250000
            #
            # parse_number fallará porque hay dos números separados,
            # y entonces parse_point lo leerá como punto.
            # ----------------------------------------------------
            try:
                p = parse_point(text, self.center)
            except ValueError:
                ctx.write("Radio no válido.")
                ctx.prompt("Radio [D=diámetro / número / punto]:")
                return CommandResult.RUNNING

            radius = math.hypot(
                p.x - self.center.x,
                p.y - self.center.y
            )

            if radius <= 1e-9:
                ctx.write("El radio debe ser mayor que cero.")
                ctx.prompt("Radio [D=diámetro / número / punto]:")
                return CommandResult.RUNNING

            ctx.add_circle(self.center, radius)

            ctx.write(
                f"Círculo creado: centro={self.center}, radio={radius:.3f}"
            )

            return CommandResult.FINISHED

        # ----------------------------------------------------
        # ESTADO 3: pedir diámetro
        # ----------------------------------------------------
        if self.state == CircleState.DIAMETER:
            try:
                diameter = parse_number(text)
            except ValueError:
                ctx.write("Diámetro no válido.")
                ctx.prompt("Diámetro:")
                return CommandResult.RUNNING

            if diameter <= 0:
                ctx.write("El diámetro debe ser mayor que cero.")
                ctx.prompt("Diámetro:")
                return CommandResult.RUNNING

            radius = diameter / 2.0

            ctx.add_circle(self.center, radius)

            ctx.write(
                f"Círculo creado: centro={self.center}, diámetro={diameter:.3f}"
            )

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == CircleState.RADIUS:
            options = ["D"]
            return [option for option in options if option.startswith(text)]

        return []

    def expects_point(self) -> bool:
        return self.state == CircleState.CENTER

    def get_point_base(self):
        return None

    def expects_point(self) -> bool:
        return self.state in (
            CircleState.CENTER,
            CircleState.RADIUS,
        )

    def get_point_base(self):
        if self.state == CircleState.RADIUS:
            return self.center

        return None