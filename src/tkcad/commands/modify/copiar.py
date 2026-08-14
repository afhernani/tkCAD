# copiar.py

from enum import Enum, auto

from ...core import Command, CommandResult, parse_point, TARGET_ALIASES
# from ...geometry import

class CopyState(Enum):
    TARGET = auto()
    BASE = auto()
    DEST = auto()


COPY_TARGET_OPTIONS = [
    "TODO",
    "LINEA",
    "POLILINEA",
    "CIRCULO",
    "ARCO",
    "POLIGONO",
    "ELIPSE",
]


class CopyCommand(Command):
    name = "COPIAR"
    aliases = ("CP", "COPY")

    def __init__(self):
        self.state = CopyState.TARGET
        self.target = None
        self.base = None
        self.use_selection = False

    def start(self, ctx):
        if not ctx.entities:
            ctx.write("No hay entidades para copiar.")
            return CommandResult.FINISHED

        if ctx.has_selection():
            self.use_selection = True
            self.state = CopyState.BASE

            ctx.write(
                f"Copiando {ctx.selection_count()} entidades seleccionadas."
            )
            ctx.prompt("Punto base:")

        else:
            self.use_selection = False
            self.state = CopyState.TARGET

            ctx.prompt(
                "No hay selección. Qué copiar "
                "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
            )

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando COPIAR cancelado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando COPIAR cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Elegir objetivo si no hay selección
        # ----------------------------------------------------
        if self.state == CopyState.TARGET and not self.use_selection:
            target = TARGET_ALIASES.get(text.upper())

            if target is None:
                ctx.write("Objetivo no válido.")
                ctx.prompt(
                    "Qué copiar "
                    "[TODO/LINEA/POLILINEA/CIRCULO/ARCO/POLIGONO]:"
                )
                return CommandResult.RUNNING

            self.target = target
            self.state = CopyState.BASE

            ctx.write(f"Copiando: {target}")
            ctx.prompt("Punto base:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Punto base
        # ----------------------------------------------------
        if self.state == CopyState.BASE:
            try:
                self.base = parse_point(text, None)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Punto base:")
                return CommandResult.RUNNING

            self.state = CopyState.DEST

            ctx.write(f"Punto base: {self.base}")
            ctx.prompt("Segundo punto [@dx,dy / @dist<ángulo / absoluto]:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Punto destino
        # ----------------------------------------------------
        if self.state == CopyState.DEST:
            try:
                dest = parse_point(text, self.base)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                ctx.prompt("Segundo punto [@dx,dy / @dist<ángulo / absoluto]:")
                return CommandResult.RUNNING

            dx = dest.x - self.base.x
            dy = dest.y - self.base.y

            if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                ctx.write("Desplazamiento cero. No se copia nada.")
                return CommandResult.FINISHED

            if self.use_selection:
                new_ids = ctx.copy_selected(dx, dy)
            else:
                new_ids = ctx.copy_entities(self.target, dx, dy)

            ctx.write(f"Entidades copiadas: {len(new_ids)}")

            # Si quieres que las copias nuevas queden seleccionadas,
            # descomenta esta línea:
            ctx.set_selection_ids(new_ids)

            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def get_completions(self, ctx, text: str):
        text = text.upper()

        if self.state == CopyState.TARGET and not self.use_selection:
            return [
                option
                for option in COPY_TARGET_OPTIONS
                if option.startswith(text)
            ]

        return []

    def expects_point(self) -> bool:
        return self.state in (
            CopyState.BASE,
            CopyState.DEST,
        )

    def get_point_base(self):
        if self.state == CopyState.DEST:
            return self.base

        return None