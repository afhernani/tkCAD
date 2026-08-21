import math
from enum import Enum, auto

from ...core import Command, CommandResult, Point, parse_point, parse_number
from ...core.dimension import lines_intersection   # ← NUEVO


class CotaState(Enum):
    TYPE = auto()
    P1 = auto()
    P2 = auto()
    OFFSET = auto()
    CENTER = auto()
    P = auto()
    PICK = auto()          # clic en entidad (modo asociativo)
    PICK2 = auto()         # ← NUEVO: segunda línea para angular (opcional)
    LIN_TYPE = auto()      # orientación tras elegir línea
    A_OFFSET = auto()      # offset tras elegir línea
    ANG_VERTEX = auto()
    ANG_P1 = auto()
    ANG_P2 = auto()
    ANG_RADIUS = auto()
    ANG_A_RADIUS = auto()  # ← NUEVO: radio de la angular asociativa


TYPE_MAP = {"H": "linear_h", "V": "linear_v", "A": "aligned"}


class CotaCommand(Command):
    name = "COTA"
    aliases = ("DIM", "COTAS")

    def __init__(self):
        self.state = CotaState.TYPE
        self.dim_type = None
        self.p1 = None
        self.p2 = None
        self.center = None
        self.assoc_id = None
        self.assoc_id2 = None   # ← NUEVO
        self.vertex = None

    def start(self, ctx):
        ctx.prompt(
            "Tipo de cota [Horizontal/Vertical/Alineada/Radio/Grados] o E=entidad asociativa:"
        )
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if text.upper() == "ESC":
            ctx.write("Comando COTA cancelado.")
            return CommandResult.FINISHED

        if self.state == CotaState.TYPE:
            t = text.upper()
            if t == "E":
                self.state = CotaState.PICK
                ctx.prompt("Clic en la entidad a acotar (línea o círculo):")
                return CommandResult.RUNNING
            if t == "R":
                self.dim_type = "radius"
                self.state = CotaState.CENTER
                ctx.prompt("Centro del arco/círculo:")
                return CommandResult.RUNNING
            if t == "G":
                self.dim_type = "angular"
                self.state = CotaState.ANG_VERTEX
                ctx.prompt("Vértice del ángulo:")
                return CommandResult.RUNNING
            if t in TYPE_MAP:
                self.dim_type = TYPE_MAP[t]
                self.state = CotaState.P1
                ctx.prompt("Primer punto:")
                return CommandResult.RUNNING
            ctx.write("Tipo no válido. Usa H, V, A, R, G o E.")
            return CommandResult.RUNNING

        # ---------- Modo asociativo ----------
        if self.state == CotaState.PICK:
            p = self._parse(ctx, text)
            if p is None:
                return CommandResult.RUNNING
            ent = ctx.entity_at_point(p)
            if ent is None:
                ctx.write("No hay ninguna entidad ahí.")
                return CommandResult.RUNNING
            if ent.kind == "line":
                self.assoc_id = ent.id
                self.state = CotaState.PICK2                    # ← CAMBIA
                ctx.prompt(
                    "Segunda línea para cota angular [Enter=lineal H/V/A]:"
                )
                return CommandResult.RUNNING
            if ent.kind in ("circle", "arc"):
                c = ent.data["center"]
                ang = math.degrees(math.atan2(p.y - c.y, p.x - c.x))
                r = ent.data["radius"]
                pr = Point(c.x + r * math.cos(math.radians(ang)),
                           c.y + r * math.sin(math.radians(ang)))
                ctx.add_dimension(
                    "radius", center=c, p=pr,
                    assoc_entity_id=ent.id,
                    assoc_kind="radius", assoc_angle=ang,
                )
                ctx.write("Cota de radio asociativa creada.")
                return CommandResult.FINISHED
            ctx.write("Entidad no acotable (usa línea o círculo).")
            return CommandResult.RUNNING

        # ---------- NUEVO: segunda línea para angular (opcional) ----------
        if self.state == CotaState.PICK2:
            if not text:
                # Enter → flujo lineal asociativo de siempre
                self.state = CotaState.LIN_TYPE
                ctx.prompt("Orientación de la cota [H/V/A]:")
                return CommandResult.RUNNING

            p = self._parse(ctx, text)
            if p is None:
                return CommandResult.RUNNING
            ent = ctx.entity_at_point(p)
            if ent is None or ent.kind != "line":
                ctx.write("Clic en una segunda línea, o Enter para lineal.")
                return CommandResult.RUNNING

            line1 = ctx.get_entity_by_id(self.assoc_id)
            if line1 is None:
                ctx.write("La entidad referida ya no existe.")
                return CommandResult.FINISHED

            a1, a2 = line1.data["start"], line1.data["end"]
            b1, b2 = ent.data["start"], ent.data["end"]
            v = lines_intersection(a1, a2, b1, b2)
            if v is None:
                ctx.write("Líneas paralelas: sin angular. "
                          "Clic en otra línea o Enter para lineal.")
                return CommandResult.RUNNING

            self.assoc_id2 = ent.id
            self.vertex = v
            self.p1 = a1 if math.hypot(a1.x - v.x, a1.y - v.y) >= \
                math.hypot(a2.x - v.x, a2.y - v.y) else a2
            self.p2 = b1 if math.hypot(b1.x - v.x, b1.y - v.y) >= \
                math.hypot(b2.x - v.x, b2.y - v.y) else b2
            self.state = CotaState.ANG_A_RADIUS
            ctx.prompt("Radio del arco de cota <15>:")
            return CommandResult.RUNNING

        # ---------- NUEVO: radio de la angular asociativa ----------
        if self.state == CotaState.ANG_A_RADIUS:
            radius = self._parse_offset(ctx, text, default=15.0)
            if radius is None:
                return CommandResult.RUNNING
            ctx.add_dimension(
                "angular", vertex=self.vertex, p1=self.p1, p2=self.p2,
                radius=radius,
                assoc_entity_id=self.assoc_id,
                assoc_entity_id2=self.assoc_id2,
                assoc_kind="angular",
            )
            ctx.write("Cota angular asociativa creada.")
            return CommandResult.FINISHED

        if self.state == CotaState.LIN_TYPE:
            t = text.upper()
            if t not in TYPE_MAP:
                ctx.write("Orientación no válida. Usa H, V o A.")
                return CommandResult.RUNNING
            self.dim_type = TYPE_MAP[t]
            self.state = CotaState.A_OFFSET
            ctx.prompt("Distancia de la línea de cota <10>:")
            return CommandResult.RUNNING

        if self.state == CotaState.A_OFFSET:
            offset = self._parse_offset(ctx, text)
            if offset is None:
                return CommandResult.RUNNING
            line = ctx.get_entity_by_id(self.assoc_id)
            if line is None:
                ctx.write("La entidad referida ya no existe.")
                return CommandResult.FINISHED
            ctx.add_dimension(
                self.dim_type,
                p1=line.data["start"], p2=line.data["end"],
                offset=offset,
                assoc_entity_id=self.assoc_id, assoc_kind="line",
            )
            ctx.write("Cota asociativa creada.")
            return CommandResult.FINISHED

        # ---------- Modo manual (sin cambios) ----------
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
            offset = self._parse_offset(ctx, text)
            if offset is None:
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

        # ---------- Modo angular manual (sin cambios) ----------
        if self.state == CotaState.ANG_VERTEX:
            p = self._parse(ctx, text)
            if p is None:
                return CommandResult.RUNNING
            self.vertex = p
            self.state = CotaState.ANG_P1
            ctx.prompt("Primer punto del rayo:")
            return CommandResult.RUNNING

        if self.state == CotaState.ANG_P1:
            p = self._parse(ctx, text, self.vertex)
            if p is None:
                return CommandResult.RUNNING
            self.p1 = p
            self.state = CotaState.ANG_P2
            ctx.prompt("Segundo punto del rayo:")
            return CommandResult.RUNNING

        if self.state == CotaState.ANG_P2:
            p = self._parse(ctx, text, self.vertex)
            if p is None:
                return CommandResult.RUNNING
            self.p2 = p
            self.state = CotaState.ANG_RADIUS
            ctx.prompt("Radio del arco de cota <15>:")
            return CommandResult.RUNNING

        if self.state == CotaState.ANG_RADIUS:
            radius = self._parse_offset(ctx, text, default=15.0)
            if radius is None:
                return CommandResult.RUNNING
            ctx.add_dimension(
                "angular", vertex=self.vertex, p1=self.p1,
                p2=self.p2, radius=radius,
            )
            ctx.write("Cota angular creada.")
            return CommandResult.FINISHED

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

    def _parse_offset(self, ctx, text, default=10.0):
        if not text:
            return default
        try:
            return parse_number(text)
        except ValueError:
            ctx.write("Número no válido.")
            return None

    def expects_point(self) -> bool:
        return self.state in (
            CotaState.P1, CotaState.P2, CotaState.CENTER,
            CotaState.P, CotaState.PICK, CotaState.PICK2,   # ← PICK2 añadido
            CotaState.ANG_VERTEX, CotaState.ANG_P1, CotaState.ANG_P2,
        )

    def get_point_base(self):
        if self.state == CotaState.P2:
            return self.p1
        if self.state == CotaState.P:
            return self.center
        if self.state in (CotaState.ANG_P1, CotaState.ANG_P2):
            return self.vertex
        return None

    def get_completions(self, ctx, text: str):
        if self.state == CotaState.TYPE:
            t = text.upper()
            return [o for o in ("H", "V", "A", "R", "G", "E") if o.startswith(t)]
        return []