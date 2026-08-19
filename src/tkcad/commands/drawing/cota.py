from enum import Enum, auto

from ...core import Command, CommandResult, parse_point, parse_number


class CotaState(Enum):
    TYPE = auto()
    P1 = auto()
    P2 = auto()
    OFFSET = auto()
    CENTER = auto()
    P = auto()


TYPE_MAP = {"H": "linear_h", "V": "linear_v", "A": "aligned", "R": "radius"}


class CotaCommand(Command):
    name = "COTA"
    aliases = ("DIM", "COTAS")

    def __init__(self):
        self.state = CotaState.TYPE
        self.dim_type = None
        self.p1 = None
        self.p2 = None
        self.center = None

    def start(self, ctx):
        ctx.prompt("Tipo de cota [H=horizontal / V=vertical / A=alineada / R=radio]:")
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando COTA cancelado.")
            return CommandResult.FINISHED

        if self.state == CotaState.TYPE:
            t = text.upper()
            if t not in TYPE_MAP:
                ctx.write("Tipo no válido. Usa H, V, A o R.")
                return CommandResult.RUNNING
            self.dim_type = TYPE_MAP[t]
            if self.dim_type == "radius":
                self.state = CotaState.CENTER
                ctx.prompt("Centro del arco/círculo:")
            else:
                self.state = CotaState.P1
                ctx.prompt("Primer punto:")
            return CommandResult.RUNNING

        if self.state == CotaState.P1:
            p = self._parse(ctx, text)
            if p is None:
                return CommandResult.RUNNING
            self.p1 = p
            self.state = CotaState.P2
            ctx.prompt("Segundo punto:")
            return CommandResult.RUNNING

        if self.state == CotaState.P2:
            p = self._parse(ctx, text, self.p1)
            if p is None:
                return CommandResult.RUNNING
            self.p2 = p
            self.state = CotaState.OFFSET
            ctx.prompt("Distancia de la línea de cota <10>:")
            return CommandResult.RUNNING

        if self.state == CotaState.OFFSET:
            if not text:
                offset = 10.0
            else:
                try:
                    offset = parse_number(text)
                except ValueError:
                    ctx.write("Número no válido.")
                    return CommandResult.RUNNING
            ctx.add_dimension(
                self.dim_type, p1=self.p1, p2=self.p2, offset=offset,
            )
            ctx.write("Cota creada.")
            return CommandResult.FINISHED

        if self.state == CotaState.CENTER:
            p = self._parse(ctx, text)
            if p is None:
                return CommandResult.RUNNING
            self.center = p
            self.state = CotaState.P
            ctx.prompt("Punto en el círculo:")
            return CommandResult.RUNNING

        if self.state == CotaState.P:
            p = self._parse(ctx, text, self.center)
            if p is None:
                return CommandResult.RUNNING
            ctx.add_dimension("radius", center=self.center, p=p)
            ctx.write("Cota de radio creada.")
            return CommandResult.FINISHED

        return CommandResult.FINISHED

    def _parse(self, ctx, text, base=None):
        try:
            return parse_point(text, base)
        except ValueError as ex:
            ctx.write(f"Punto no válido: {ex}")
            return None

    def expects_point(self) -> bool:
        return self.state in (
            CotaState.P1, CotaState.P2, CotaState.CENTER, CotaState.P,
        )

    def get_point_base(self):
        if self.state == CotaState.P2:
            return self.p1
        if self.state == CotaState.P:
            return self.center
        return None

    def get_completions(self, ctx, text: str):
        if self.state == CotaState.TYPE:
            t = text.upper()
            return [o for o in ("H", "V", "A", "R") if o.startswith(t)]
        return []