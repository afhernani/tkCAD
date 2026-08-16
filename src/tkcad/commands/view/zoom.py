from ...core import Command, CommandResult, parse_number


class ZoomCommand(Command):
    name = "ZOOM"
    aliases = ("Z",)

    def start(self, ctx):
        ctx.prompt("Zoom [+ / - / TODO / factor / Enter=salir]:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if not text:
            return CommandResult.FINISHED
        option = text.upper()
        if option == "+":
            ctx.zoom_center(1.25)
        elif option == "-":
            ctx.zoom_center(0.8)
        elif option in ("TODO", "T", "EXT"):
            ctx.zoom_extents()
        else:
            try:
                factor = parse_number(text)
            except ValueError:
                ctx.write("Opción de zoom no válida.")
                ctx.prompt("Zoom [+ / - / TODO / factor / Enter=salir]:")
                return CommandResult.RUNNING
            if factor <= 0:
                ctx.write("El factor debe ser positivo.")
            else:
                ctx.zoom_center(factor)
        ctx.prompt("Zoom [+ / - / TODO / factor / Enter=salir]:")
        return CommandResult.RUNNING