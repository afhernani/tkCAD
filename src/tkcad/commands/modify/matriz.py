from enum import Enum, auto

from ...core import Command, CommandResult, parse_point, parse_number


class MatrizState(Enum):
    TYPE = auto()
    ROWS = auto()
    COLS = auto()
    DX = auto()
    DY = auto()
    CENTER = auto()
    COUNT = auto()
    ANGLE = auto()


class MatrizCommand(Command):
    name = "MATRIZ"
    aliases = ("ARRAY", "MAT")

    def __init__(self):
        self.state = MatrizState.TYPE
        self.ids = []
        self.rows = 2
        self.cols = 2
        self.dx = 10.0
        self.dy = 10.0
        self.center = None
        self.count = 4

    def start(self, ctx):
        self.ids = [e.id for e in ctx.get_selected_entities()]
        if not self.ids:
            ctx.write("MATRIZ: selecciona entidades antes de usar el comando.")
            return CommandResult.FINISHED
        ctx.prompt(
            f"Tipo de matriz [R=rectangular / P=polar] "
            f"({len(self.ids)} entidad/es):"
        )
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando MATRIZ cancelado.")
            return CommandResult.FINISHED

        if self.state == MatrizState.TYPE:
            t = text.upper()
            if t == "R":
                self.state = MatrizState.ROWS
                ctx.prompt("Número de filas <2>:")
                return CommandResult.RUNNING
            if t == "P":
                self.state = MatrizState.CENTER
                ctx.prompt("Centro de la matriz:")
                return CommandResult.RUNNING
            ctx.write("Opción no válida. Usa R o P.")
            return CommandResult.RUNNING

        # ---------- Rectangular ----------
        if self.state == MatrizState.ROWS:
            n = self._int(ctx, text, 2)
            if n is None:
                return CommandResult.RUNNING
            self.rows = n
            self.state = MatrizState.COLS
            ctx.prompt("Número de columnas <2>:")
            return CommandResult.RUNNING

        if self.state == MatrizState.COLS:
            n = self._int(ctx, text, 2)
            if n is None:
                return CommandResult.RUNNING
            self.cols = n
            self.state = MatrizState.DX
            ctx.prompt("Distancia entre columnas (X) <10>:")
            return CommandResult.RUNNING

        if self.state == MatrizState.DX:
            v = self._num(ctx, text, 10.0)
            if v is None:
                return CommandResult.RUNNING
            self.dx = v
            self.state = MatrizState.DY
            ctx.prompt("Distancia entre filas (Y) <10>:")
            return CommandResult.RUNNING

        if self.state == MatrizState.DY:
            v = self._num(ctx, text, 10.0)
            if v is None:
                return CommandResult.RUNNING
            self.dy = v
            new = ctx.array_rectangular(
                self.ids, self.rows, self.cols, self.dx, self.dy,
            )
            ctx.write(f"Matriz rectangular creada: {len(new)} copias.")
            return CommandResult.FINISHED

        # ---------- Polar ----------
        if self.state == MatrizState.CENTER:
            try:
                self.center = parse_point(text)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                return CommandResult.RUNNING
            self.state = MatrizState.COUNT
            ctx.prompt("Número de elementos (incluido el original) <4>:")
            return CommandResult.RUNNING

        if self.state == MatrizState.COUNT:
            n = self._int(ctx, text, 4)
            if n is None:
                return CommandResult.RUNNING
            if n < 2:
                ctx.write("Se necesitan al menos 2 elementos.")
                return CommandResult.RUNNING
            self.count = n
            self.state = MatrizState.ANGLE
            ctx.prompt("Ángulo total a rellenar <360>:")
            return CommandResult.RUNNING

        if self.state == MatrizState.ANGLE:
            v = self._num(ctx, text, 360.0)
            if v is None:
                return CommandResult.RUNNING
            new = ctx.array_polar(self.ids, self.center, self.count, v)
            ctx.write(f"Matriz polar creada: {len(new)} copias.")
            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def _int(self, ctx, text, default):
        if not text:
            return default
        try:
            return int(parse_number(text))
        except ValueError:
            ctx.write("Número entero no válido.")
            return None

    def _num(self, ctx, text, default):
        if not text:
            return default
        try:
            return parse_number(text)
        except ValueError:
            ctx.write("Número no válido.")
            return None

    def expects_point(self) -> bool:
        return self.state == MatrizState.CENTER

    def get_completions(self, ctx, text: str):
        if self.state == MatrizState.TYPE:
            t = text.upper()
            return [o for o in ("R", "P") if o.startswith(t)]
        return []