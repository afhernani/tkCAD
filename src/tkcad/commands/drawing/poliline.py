
import math
from enum import Enum, auto
from typing import Optional, List

from ...core import  Command, CommandResult, Point, parse_point, parse_number
# from ...geometry import
# from .line import


# ============================================================
# Comando POLILINEA
# ============================================================

class PolylineCommand(Command):
    name = "POLILINEA"
    aliases = ("PL", "POLYLINE")

    def __init__(self):
        self.points: List[Point] = []

    def start(self, ctx):
        ctx.prompt("Primer punto:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        # Enter vacío
        if not text:
            return self._finish(ctx)

        # ESC
        if text.upper() == "ESC":
            ctx.write("Comando POLILINEA cancelado.")
            return CommandResult.FINISHED

        # Primer punto
        if not self.points:
            try:
                p = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Primer punto:")
                return CommandResult.RUNNING

            self.points.append(p)
            ctx.show_preview_polyline(self.points)
            ctx.write(f"Primer punto: {p}")
            ctx.prompt("Siguiente punto [Enter=terminar / C=cerrar]:")
            return CommandResult.RUNNING

        # Opción cerrar
        if text.upper() == "C":
            if len(self.points) >= 3:
                self.points.append(self.points[0])
                ctx.write("Polilínea cerrada.")
                return self._finish(ctx)

            ctx.write("Para cerrar se necesitan al menos 3 puntos.")
            ctx.prompt("Siguiente punto [Enter=terminar / C=cerrar]:")
            return CommandResult.RUNNING

        # Siguiente punto
        try:
            p = parse_point(text, self.points[-1])
        except ValueError as ex:
            ctx.write(f"Punto no válido: {ex}")
            ctx.prompt("Siguiente punto [Enter=terminar / C=cerrar]:")
            return CommandResult.RUNNING

        self.points.append(p)
        ctx.show_preview_polyline(self.points)
        ctx.write(f"Punto añadido: {p}")
        ctx.prompt("Siguiente punto [Enter=terminar / C=cerrar]:")

        return CommandResult.RUNNING

    def _finish(self, ctx) -> CommandResult:
        ctx.clear_preview()
        if len(self.points) >= 2:
            ctx.add_polyline(self.points)
            ctx.write(f"Polilínea creada con {len(self.points)} puntos.")
        else:
            ctx.write("Comando POLILINEA cancelado.")

        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return True
        # return self.state in (
        #     PolylineState.FIRST_POINT,
        #     PolylineState.NEXT_POINT,
        # )

    def get_point_base(self):
        if self.points:
            return self.points[-1]

        return None
