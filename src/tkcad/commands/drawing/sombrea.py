from enum import Enum, auto

from ...core import Command, CommandResult, parse_point, parse_number


class SombreaState(Enum):
    STYLE = auto()
    POINTS = auto()
    SPACING = auto()
    ANGLE = auto()


class SombreaCommand(Command):
    name = "SOMBREA"
    aliases = ("HATCH", "SOMBREADO")

    def __init__(self):
        self.state = SombreaState.STYLE
        self.style = "solid"
        self.src = None
        self.points = []
        self.spacing = 5.0
        self.angle = 45.0

    def start(self, ctx):
        # Si hay un polígono seleccionado, lo usa como contorno
        for e in ctx.get_selected_entities():
            if e.kind == "polygon" and len(e.data["points"]) >= 3:
                self.src = list(e.data["points"])
                break
        if self.src:
            ctx.prompt("Estilo [Sólido/Rayado] <S> (polígono seleccionado):")
        else:
            ctx.prompt("Estilo [Sólido/Rayado] <S> (o dibuja el contorno):")
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if text.upper() == "ESC":
            ctx.write("SOMBREA cancelado.")
            return CommandResult.FINISHED

        if self.state == SombreaState.STYLE:
            t = text.upper() or "S"
            if t not in ("S", "R"):
                ctx.write("Estilo no válido. Usa S o R.")
                return CommandResult.RUNNING
            self.style = "solid" if t == "S" else "hatch"
            if self.src is not None:
                if self.style == "solid":
                    return self._create(ctx)
                self.state = SombreaState.SPACING
                ctx.prompt("Separación entre líneas <5>:")
                return CommandResult.RUNNING
            self.state = SombreaState.POINTS
            ctx.prompt("Punto del contorno (Enter cierra):")
            return CommandResult.RUNNING

        if self.state == SombreaState.POINTS:
            if not text:
                if len(self.points) >= 3:
                    if self.style == "solid":
                        return self._create(ctx)
                    self.state = SombreaState.SPACING
                    ctx.prompt("Separación entre líneas <5>:")
                    return CommandResult.RUNNING
                ctx.write("Se necesitan al menos 3 puntos.")
                return CommandResult.RUNNING
            try:
                p = parse_point(text)
            except ValueError as ex:
                ctx.write(f"Punto no válido: {ex}")
                return CommandResult.RUNNING
            self.points.append(p)
            ctx.prompt(f"Punto {len(self.points) + 1} (Enter cierra):")
            return CommandResult.RUNNING

        if self.state == SombreaState.SPACING:
            if text:
                try:
                    self.spacing = parse_number(text)
                except ValueError:
                    ctx.write("Número no válido.")
                    return CommandResult.RUNNING
            self.state = SombreaState.ANGLE
            ctx.prompt("Ángulo de las líneas <45>:")
            return CommandResult.RUNNING

        if self.state == SombreaState.ANGLE:
            if text:
                try:
                    self.angle = parse_number(text)
                except ValueError:
                    ctx.write("Número no válido.")
                    return CommandResult.RUNNING
            return self._create(ctx)

        return CommandResult.FINISHED

    def _create(self, ctx):
        pts = self.src if self.src is not None else self.points
        ctx.add_hatch(pts, style=self.style,
                      spacing=self.spacing, angle=self.angle)
        ctx.write("Sombreado creado.")
        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return self.state == SombreaState.POINTS