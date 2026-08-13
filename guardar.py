# guardar.py

from enum import Enum, auto

from core import Command, CommandResult


class SaveState(Enum):
    FILEPATH = auto()


class SaveCommand(Command):
    name = "GUARDAR"
    aliases = ("SAVE", "G")

    def __init__(self):
        self.state = SaveState.FILEPATH

    def start(self, ctx):
        current = getattr(ctx, "current_file", None)

        if current is not None:
            ctx.write(f"Archivo actual: {current}")

        ctx.prompt(
            "Ruta para guardar "
            "[Enter para guardar actual / diálogo si no existe]:"
        )

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando GUARDAR cancelado.")
            return CommandResult.FINISHED

        if not text:
            filepath = None
        else:
            filepath = text.strip().strip('"').strip("'")

        ok, message = ctx.save_project(filepath)

        ctx.write(message)

        return CommandResult.FINISHED

class SaveAsCommand(Command):
    name = "GUARDARCOMO"
    aliases = ("SAVEAS", "GCOMO")

    def start(self, ctx):
        current = getattr(ctx, "current_file", None)

        if current is not None:
            ctx.write(f"Archivo actual: {current}")

        ctx.prompt(
            "Ruta para guardar como "
            "[Enter para abrir diálogo de archivo]:"
        )

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando GUARDARCOMO cancelado.")
            return CommandResult.FINISHED

        if not text:
            filepath = None
        else:
            filepath = text.strip().strip('"').strip("'")

        ok, message = ctx.save_project(
            filepath,
            force_dialog=True,
        )

        ctx.write(message)

        return CommandResult.FINISHED