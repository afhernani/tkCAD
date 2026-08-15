from typing import Optional, Dict, Type

from .command import Command, CommandResult
from .point import Point


# ============================================================
# Gestor de comandos
# ============================================================

class CommandLineManager:
    def __init__(self, ctx):
        self.ctx = ctx
        self.active: Optional[Command] = None
        self.factories: Dict[str, Type[Command]] = {}

    def register(self, command_class: Type[Command]):
        cmd = command_class()

        self.factories[cmd.name.upper()] = command_class

        for alias in cmd.aliases:
            self.factories[alias.upper()] = command_class

    def get_available_command_names(self):
        names = {
            command_class.name.upper()
            for command_class in self.factories.values()
        }

        return sorted(names)

    def get_available_command_help(self):
        help_items = {}

        for alias, command_class in self.factories.items():
            name = command_class.name.upper()

            if name not in help_items:
                help_items[name] = set()

            alias_upper = alias.upper()

            if alias_upper != name:
                help_items[name].add(alias_upper)

        return sorted(
            (name, sorted(aliases))
            for name, aliases in help_items.items()
        )

    def get_completions(self, text: str):
        text = text.strip().upper()

        # Si hay un comando activo, preguntamos al comando
        # si tiene autocompletado contextual.
        if self.active is not None:
            if hasattr(self.active, "get_completions"):
                return self.active.get_completions(self.ctx, text)

            return []

        # Si no hay comando activo y el texto está vacío,
        # mostramos todos los comandos.
        if not text:
            return self.get_available_command_names()

        matches = set()

        for alias, command_class in self.factories.items():
            alias_upper = alias.upper()
            name_upper = command_class.name.upper()

            if alias_upper.startswith(text) or name_upper.startswith(text):
                matches.add(name_upper)

        return sorted(matches)

    def process_input(self, text: str, echo: bool = True):
        text = text.strip()

        # Enter vacío: sirve para terminar o cancelar el comando activo.
        if not text:
            if self.active is not None:
                result = self.active.handle_input(self.ctx, "")
                if result == CommandResult.FINISHED:
                    self.active = None
                    self.ctx.clear_preview()
                    self.ctx.prompt("Comando:")
            return

        if echo:
            self.ctx.write(f"> {text}")

        # ESC cancela el comando activo
        if text.upper() == "ESC":
            if self.active is not None:
                self.ctx.write("Comando cancelado.")
                self.ctx.clear_preview()
                self.active = None
                self.ctx.prompt("Comando:")
            return

        # Si no hay comando activo, intentamos iniciar uno.
        if self.active is None:
            command_class = self.factories.get(text.upper())

            if command_class:
                self.active = command_class()
                self.active.start(self.ctx)
            else:
                self.ctx.write(f"Comando no reconocido: {text}")
                self.ctx.write("Comandos disponibles: " + ", ".join(self.get_available_command_names()))
                self.ctx.prompt("Comando:")

            return

        # Si hay comando activo, le pasamos la entrada.
        result = self.active.handle_input(self.ctx, text)

        if result == CommandResult.FINISHED:
            self.active = None
            self.ctx.clear_preview()
            self.ctx.prompt("Comando:")

    def is_waiting_for_point(self) -> bool:
        if self.active is None:
            return False

        if hasattr(self.active, "expects_point"):
            return bool(self.active.expects_point())

        return False

    def get_point_base(self):
        if self.active is None:
            return None

        if hasattr(self.active, "get_point_base"):
            return self.active.get_point_base()

        return None

    def send_point(self, p: Point, echo: bool = False):
        if self.active is None:
            return

        text = f"{p.x:.6f};{p.y:.6f}"

        self.process_input(text, echo=echo)

