# borrar.py

from enum import Enum, auto

from ...core import Command, CommandResult, TARGET_ALIASES
# from ...geometry import


class DeleteState(Enum):
    MODE = auto()
    CONFIRM = auto()


DELETE_TARGET_OPTIONS = [
    "TODO",
    "LINEA",
    "POLILINEA",
    "CIRCULO",
    "ARCO",
    "POLIGONO",
]


YES_OPTIONS = {
    "S",
    "SI",
    "SÍ",
    "Y",
    "YES",
    "OK",
}


class DeleteCommand(Command):
    name = "BORRAR"
    aliases = ("DEL", "ERASE", "D")

    def __init__(self):
        self.state = DeleteState.MODE
        self.mode = None

    def start(self, ctx):
        if not ctx.entities:
            ctx.write("No hay entidades.")
            return CommandResult.FINISHED

        if ctx.has_selection():
            self.mode = "SELECCION"
            self.state = DeleteState.CONFIRM

            ctx.write(
                f"Hay {ctx.selection_count()} entidades seleccionadas."
            )
            ctx.prompt("¿Borrar selección? [S/N]:")

        else:
            self.state = DeleteState.MODE

            ctx.prompt(
                "No hay selección. Qué borrar "
                "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
            )

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando BORRAR cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando BORRAR cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Elegir objetivo si no hay selección
        # ----------------------------------------------------
        if self.state == DeleteState.MODE:
            target = TARGET_ALIASES.get(text.upper())

            if target is None:
                ctx.write("Objetivo no válido.")
                ctx.prompt(
                    "Qué borrar "
                    "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
                )
                return CommandResult.RUNNING

            self.mode = target
            self.state = DeleteState.CONFIRM

            ctx.prompt(f"¿Borrar {target}? [S/N]:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Confirmar borrado
        # ----------------------------------------------------
        if self.state == DeleteState.CONFIRM:
            if text.upper() in YES_OPTIONS:
                if self.mode == "SELECCION":
                    count = ctx.delete_selected()
                    ctx.write(f"Entidades borradas: {count}")

                else:
                    count = ctx.delete_entities(self.mode)
                    ctx.write(f"Entidades borradas: {count}")

            else:
                ctx.write("Comando BORRAR cancelado.")

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == DeleteState.MODE:
            return [
                option
                for option in DELETE_TARGET_OPTIONS
                if option.startswith(text)
            ]

        if self.state == DeleteState.CONFIRM:
            options = ["S", "N"]

            return [
                option
                for option in options
                if option.startswith(text)
            ]

        return []