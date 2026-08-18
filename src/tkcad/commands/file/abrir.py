# abrir.py

from enum import Enum, auto

from ...core import Command, CommandResult


class OpenState(Enum):
    CONFIRM = auto()
    FILEPATH = auto()


YES_OPTIONS = {
    "S",
    "SI",
    "SÍ",
    "Y",
    "YES",
    "OK",
}


class OpenCommand(Command):
    name = "ABRIR"
    aliases = ("OPEN", "O", "ABR")

    def __init__(self):
        self.state = OpenState.FILEPATH

    def start(self, ctx):
        if ctx.entities:
            self.state = OpenState.CONFIRM

            ctx.write(
                "Atención: abrir un proyecto reemplazará las entidades actuales."
            )
            ctx.prompt("¿Continuar? [S/N]:")

        else:
            self.state = OpenState.FILEPATH

            ctx.prompt(
                "Ruta para abrir "
                "[Enter para abrir diálogo de archivo]:"
            )

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando ABRIR cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Confirmar si hay entidades actuales
        # ----------------------------------------------------
        if self.state == OpenState.CONFIRM:
            if text.upper() in YES_OPTIONS:
                self.state = OpenState.FILEPATH

                ctx.prompt(
                    "Ruta para abrir "
                    "[Enter para abrir diálogo de archivo]:"
                )

                return CommandResult.RUNNING

            ctx.write("Comando ABRIR cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Ruta del archivo
        # ----------------------------------------------------
        if self.state == OpenState.FILEPATH:
            if not text:
                filepath = None
            else:
                filepath = text.strip().strip('"').strip("'")

            ok, message = ctx.load_project(filepath)
            if ok:
                ctx.mark_saved()
            ctx.write(message)

            return CommandResult.FINISHED

        return CommandResult.FINISHED