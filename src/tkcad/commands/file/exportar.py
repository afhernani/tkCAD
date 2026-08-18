from ...core import Command, CommandResult


class ExportCommand(Command):
    name = "EXPORTAR"
    aliases = ("EXPORT", "DXF")

    def start(self, ctx):
        ctx.prompt("Ruta del archivo DXF [Enter para diálogo]:")
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando EXPORTAR cancelado.")
            return CommandResult.FINISHED

        filepath = text.strip().strip('"').strip("'") if text else None
        ok, message = ctx.export_dxf(filepath)
        ctx.write(message)
        return CommandResult.FINISHED