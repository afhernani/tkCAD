from enum import Enum, auto


# ============================================================
# Modelo básico
# ============================================================
class CommandResult(Enum):
    RUNNING = auto()
    FINISHED = auto()

# ============================================================
# Interfaz base para comandos
# ============================================================
class Command:
    name: str = ""
    aliases = ()

    def start(self, ctx):
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        raise NotImplementedError

    def get_completions(self, ctx, text: str):
        """
        Devuelve una lista de opciones para autocompletar
        cuando el comando está activo.
        """
        return []

    def expects_point(self) -> bool:
        return False

    def expects_entity(self) -> bool:
        """True si el comando acepta elegir entidad con un clic."""
        return False

    def get_point_base(self):
        return None