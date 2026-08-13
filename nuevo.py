# nuevo.py

from enum import Enum, auto

from core import Command, CommandResult


class NewState(Enum):
    CONFIRM = auto()


YES_OPTIONS = {
    "S",
    "SI",
    "SÍ",
    "Y",
    "YES",
    "OK",
}


class NewCommand(Command):
    name = "NUEVO"
    aliases = ("NEW", "N")

    def __init__(self):
        self.state = NewState.CONFIRM

    def start(self, ctx):
        # Si no hay entidades, creamos proyecto nuevo directamente
        if not ctx.entities:
            ctx.new_project()
            ctx.write("Proyecto nuevo creado.")
            return CommandResult.FINISHED

        # Si hay entidades, pedimos confirmación
        self.state = NewState.CONFIRM

        ctx.write(
            "Atención: esto borrará todas las entidades actuales."
        )

        ctx.prompt("¿Crear un proyecto nuevo? [S/N]:")

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando NUEVO cancelado.")
            return CommandResult.FINISHED

        if self.state == NewState.CONFIRM:
            if text.upper() in YES_OPTIONS:
                ctx.new_project()
                ctx.write("Proyecto nuevo creado.")

            else:
                ctx.write("Comando NUEVO cancelado.")

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == NewState.CONFIRM:
            options = ["S", "N"]

            return [
                option
                for option in options
                if option.startswith(text)
            ]

        return []