from enum import Enum, auto

from ...core import Command, CommandResult, parse_point, parse_number


class TextState(Enum):
    POINT = auto()
    HEIGHT = auto()
    CONTENT = auto()


class TextoCommand(Command):
    name = "TEXTO"
    aliases = ("TXT", "TEXT")

    def __init__(self):
        self.state = TextState.POINT
        self.position = None
        self.height = None

    def start(self, ctx):
        ctx.prompt("Punto base del texto:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        if self.state == TextState.POINT:
            if text.upper() == "ESC" or not text:
                ctx.write("Comando TEXTO cancelado.")
                return CommandResult.FINISHED
            try:
                self.position = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                return CommandResult.RUNNING
            self.state = TextState.HEIGHT
            ctx.prompt("Altura <2.5>:")
            return CommandResult.RUNNING

        if self.state == TextState.HEIGHT:
            if text.upper() == "ESC":
                ctx.write("Comando TEXTO cancelado.")
                return CommandResult.FINISHED
            if not text:
                self.height = 2.5
            else:
                try:
                    self.height = parse_number(text)
                except ValueError:
                    ctx.write("Altura no válida.")
                    return CommandResult.RUNNING
            if self.height <= 0:
                ctx.write("La altura debe ser mayor que cero.")
                return CommandResult.RUNNING
            self.state = TextState.CONTENT
            ctx.prompt("Contenido del texto:")
            return CommandResult.RUNNING

        if self.state == TextState.CONTENT:
            if text.upper() == "ESC" or not text:
                ctx.write("Comando TEXTO cancelado.")
                return CommandResult.FINISHED
            content = self._normalize_newlines(text)
            ctx.add_text(self.position, self.height, content)
            ctx.write(f"Texto creado: '{text}'")
            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.state == TextState.POINT

    def get_point_base(self):
        return None

    def _normalize_newlines(self, text: str) -> str:
        """Convierte los escapes \\n escritos por el usuario en saltos reales."""
        return text.replace("\\n", "\n")