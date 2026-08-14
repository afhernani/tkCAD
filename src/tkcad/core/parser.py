

import math
from typing import Optional
from .point import Point

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
