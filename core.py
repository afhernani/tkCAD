# core.py

import math
from dataclasses import dataclass
from typing import Any, Dict
from enum import Enum, auto
from typing import Optional

ALL_SNAP_MODES = [
    "GRID",
    "POINT",
    "ENDPOINT",
    "MIDPOINT",
    "INTERSECTION",
    "ORTHO",
]

TARGET_ALIASES = {
    "TODO": "TODO",
    "T": "TODO",
    "ALL": "TODO",

    "LINEA": "LINEA",
    "LINEAS": "LINEA",
    "L": "LINEA",

    "POLILINEA": "POLILINEA",
    "POLILINEAS": "POLILINEA",
    "PL": "POLILINEA",

    "CIRCULO": "CIRCULO",
    "CIRCULOS": "CIRCULO",
    "C": "CIRCULO",

    "ARCO": "ARCO",
    "ARCOS": "ARCO",
    "A": "ARCO",

    "POLIGONO": "POLIGONO",
    "POLIGONOS": "POLIGONO",
    "POL": "POLIGONO",
    "PG": "POLIGONO",

    "ELIPSE": "ELIPSE",
    "ELIPSES": "ELIPSE",
    "ELLIPSE": "ELIPSE",
    "EL": "ELIPSE",
}

TARGET_KIND_MAP = {
    "LINEA": "line",
    "POLILINEA": "polyline",
    "CIRCULO": "circle",
    "ARCO": "arc",
    "POLIGONO": "polygon",
    "ELIPSE": "ellipse",
}

def parse_target(text: str):
    return TARGET_ALIASES.get(text.strip().upper())


def parse_kind(text: str):
    target = parse_target(text)

    if target is None:
        return None

    if target == "TODO":
        return None

    return TARGET_KIND_MAP.get(target)

# ============================================================
# Modelo básico
# ============================================================
class CommandResult(Enum):
    RUNNING = auto()
    FINISHED = auto()


@dataclass
class Point:
    x: float
    y: float

    def __str__(self):
        return f"{self.x:.3f},{self.y:.3f}"

@dataclass
class Entity:
    id: int
    kind: str
    data: Dict[str, Any]
    selected: bool = False

# ============================================================
# Parser de puntos
# ============================================================
def parse_number(text: str) -> float:
    return float(text.strip().replace(",", "."))


def parse_point(text: str, base: Optional[Point] = None) -> Point:
    text = text.strip()

    if not text:
        raise ValueError("Texto vacío.")

    relative = text.startswith("@")

    if relative:
        text = text[1:]

    # Formato polar: distancia<ángulo
    if "<" in text:
        distance_text, angle_text = text.split("<", 1)

        distance = parse_number(distance_text)
        angle_deg = parse_number(angle_text)

        if relative and base is None:
            raise ValueError("No hay punto base para una coordenada relativa.")

        origin = base if relative else Point(0.0, 0.0)
        angle_rad = math.radians(angle_deg)

        return Point(
            origin.x + distance * math.cos(angle_rad),
            origin.y + distance * math.sin(angle_rad),
        )

    # Formato cartesiano: X,Y o X;Y
    separator = ";" if ";" in text else ","
    parts = [part.strip() for part in text.split(separator) if part.strip()]

    if len(parts) != 2:
        raise ValueError("Formato de punto no válido. Usa por ejemplo 10,20 o 10;20.")

    x = parse_number(parts[0])
    y = parse_number(parts[1])

    if relative:
        if base is None:
            raise ValueError("No hay punto base para una coordenada relativa.")
        return Point(base.x + x, base.y + y)

    return Point(x, y)

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

    def get_point_base(self):
        return None