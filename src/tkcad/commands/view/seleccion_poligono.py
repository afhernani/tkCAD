from ...core import Command, CommandResult, parse_point


class SeleccionPoligonoCommand(Command):
    name = "SELECCIONARPOLIGONO"
    aliases = ("SPOL", "VPOL", "CPOL")

    def __init__(self):
        self.mode = None
        self.points = []

    def start(self, ctx):
        ctx.prompt("Modo [V=ventana / C=cruce]:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        # --- elegir modo ---
        if self.mode is None:
            if not text:
                ctx.write("Comando cancelado.")
                return CommandResult.FINISHED
            up = text.upper()
            if up in ("V", "VENTANA"):
                self.mode = "window"
            elif up in ("C", "CRUCE"):
                self.mode = "crossing"
            else:
                ctx.write("Opción no válida. Usa V o C.")
                ctx.prompt("Modo [V=ventana / C=cruce]:")
                return CommandResult.RUNNING
            ctx.clear_preview()
            ctx.prompt("Puntos del polígono (Enter termina):")
            return CommandResult.RUNNING

        # --- recoger puntos ---
        if not text:
            return self._finish(ctx)

        try:
            p = parse_point(text, self.points[-1] if self.points else None)
        except ValueError as ex:
            ctx.write(f"Punto no válido: {ex}")
            ctx.prompt("Siguiente punto [Enter=terminar]:")
            return CommandResult.RUNNING

        self.points.append(p)
        if hasattr(ctx, "show_preview_polyline"):
            ctx.show_preview_polyline(self.points)
        ctx.prompt("Siguiente punto [Enter=terminar]:")
        return CommandResult.RUNNING

    def _finish(self, ctx) -> CommandResult:
        ctx.clear_preview()
        if len(self.points) >= 3:
            count = ctx.select_by_polygon(self.points, self.mode, "replace")
            ctx.write(f"{count} entidad(es) seleccionada(s).")
        else:
            ctx.write("Se necesitan al menos 3 puntos.")
        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.mode is not None

    def get_point_base(self):
        return self.points[-1] if self.points else None