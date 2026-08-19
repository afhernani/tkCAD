from ...core import Command, CommandResult


class ExportarImgCommand(Command):
    name = "EXPORTARIMG"
    aliases = ("IMG", "EXPORTIMG")

    def start(self, ctx):
        ctx.prompt(
            "Ruta de imagen [Enter para diálogo] "
            "(la extensión decide SVG / PNG):"
        )
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando EXPORTARIMG cancelado.")
            return CommandResult.FINISHED

        filepath = text.strip().strip('"').strip("'") if text else None
        ok, message = ctx.export_image(filepath)
        ctx.write(message)
        return CommandResult.FINISHED