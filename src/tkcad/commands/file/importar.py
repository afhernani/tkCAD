from ...core import Command, CommandResult


class ImportarCommand(Command):
    name = "IMPORTAR"
    aliases = ("IMPORT", "IMPORTDXF")

    def start(self, ctx):
        ctx.prompt("Ruta del DXF [Enter para abrir diálogo de archivo]:")
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if text.upper() == "ESC":
            ctx.write("IMPORTAR cancelado.")
            return CommandResult.FINISHED
        ok, msg = ctx.import_dxf(text if text else None)
        ctx.write(msg)
        return CommandResult.FINISHED