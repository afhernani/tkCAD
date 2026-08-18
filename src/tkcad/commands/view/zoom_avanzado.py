from ...core import Command, CommandResult, parse_point


class ZoomVentanaCommand(Command):
    name = "ZOOMVENTANA"
    aliases = ("ZV", "ZOOMV")

    def __init__(self):
        self.p1 = None

    def start(self, ctx):
        ctx.prompt("Primera esquina de la ventana:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if not text or text.upper() == "ESC":
            ctx.write("ZOOM VENTANA cancelado.")
            return CommandResult.FINISHED

        try:
            p = parse_point(text, self.p1)
        except ValueError as ex:
            ctx.write(f"Punto no válido: {ex}")
            return CommandResult.RUNNING

        if self.p1 is None:
            self.p1 = p
            ctx.prompt("Segunda esquina:")
            return CommandResult.RUNNING

        min_x, max_x = min(self.p1.x, p.x), max(self.p1.x, p.x)
        min_y, max_y = min(self.p1.y, p.y), max(self.p1.y, p.y)

        if max_x - min_x < 1e-9 or max_y - min_y < 1e-9:
            ctx.write("La ventana es demasiado pequeña.")
            return CommandResult.FINISHED

        ctx.zoom_to_world_rect(min_x, min_y, max_x, max_y)
        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return True

    def get_point_base(self):
        return self.p1


class ZoomPrevioCommand(Command):
    name = "ZOOMPREVIO"
    aliases = ("ZP", "ANT")

    def start(self, ctx):
        if ctx.zoom_previous():
            ctx.write("Vista anterior.")
        else:
            ctx.write("No hay vistas anteriores.")
        return CommandResult.FINISHED


class ZoomSiguienteCommand(Command):
    name = "ZOOMSIGUIENTE"
    aliases = ("ZS", "SIG")

    def start(self, ctx):
        if ctx.zoom_next():
            ctx.write("Vista siguiente.")
        else:
            ctx.write("No hay vistas siguientes.")
        return CommandResult.FINISHED