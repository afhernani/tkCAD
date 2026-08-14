

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
