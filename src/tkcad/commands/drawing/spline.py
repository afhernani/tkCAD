from ...core import Command, CommandResult, parse_point
from ...core.spline import eval_cubic_spline


class SplineCommand(Command):
    name = "SPLINE"
    aliases = ("SPL", "CURVA")

    def __init__(self):
        self.points = []

    def start(self, ctx):
        ctx.prompt(
            "Punto de la spline (Enter=terminar / C=cerrar / ESC=cancelar):"
        )
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.clear_preview()
            ctx.write("Comando SPLINE cancelado.")
            return CommandResult.FINISHED

        # Cerrar cíclicamente (mínimo 3 puntos)
        if text.upper() == "C":
            if len(self.points) >= 3:
                ctx.clear_preview()
                ctx.add_spline(self.points, closed=True)
                ctx.write(
                    f"Spline cerrada creada con {len(self.points)} puntos."
                )
                return CommandResult.FINISHED
            ctx.write("Se necesitan al menos 3 puntos para cerrar.")
            return CommandResult.RUNNING

        # Enter: terminar spline abierta
        if not text:
            ctx.clear_preview()
            if len(self.points) >= 2:
                ctx.add_spline(self.points, closed=False)
                ctx.write(f"Spline creada con {len(self.points)} puntos.")
            else:
                ctx.write("SPLINE cancelada: se necesitan al menos 2 puntos.")
            return CommandResult.FINISHED

        # Punto nuevo
        try:
            p = parse_point(
                text, self.points[-1] if self.points else None,
            )
        except ValueError as ex:
            ctx.write(f"Punto no válido: {ex}")
            return CommandResult.RUNNING

        self.points.append(p)
        self._show_curve_preview(ctx)
        ctx.prompt("Siguiente punto (Enter=terminar / C=cerrar / ESC=cancelar):")
        return CommandResult.RUNNING

    def _show_curve_preview(self, ctx):
        """Hilo elástico con la curva real evaluada (no el polígono)."""
        if len(self.points) >= 2:
            ctx.show_preview_polyline(
                eval_cubic_spline(self.points, samples_per_segment=20),
            )

    def expects_point(self) -> bool:
        return True

    def get_point_base(self):
        return self.points[-1] if self.points else None