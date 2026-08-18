"""Formateo de los campos de la barra de estado (lógica pura, testeable)."""

SNAP_SHORT = {
    "ENDPOINT": "END",
    "MIDPOINT": "MID",
    "CENTER": "CEN",
    "QUADRANT": "QUA",
    "INTERSECTION": "INT",
    "TANGENT": "TAN",
    "PERPENDICULAR": "PER",
    "NEAREST": "NEA",
    "POINT": "PNT",
}


def format_coords(x: float, y: float) -> str:
    return f"X: {x:.1f}  Y: {y:.1f}"


def format_snaps(modes) -> str:
    shorts = [SNAP_SHORT.get(m, m[:3]) for m in sorted(modes)]
    return "SNAP: " + " ".join(shorts) if shorts else "SNAP: —"


def format_flags(ortho_on: bool, grid_on: bool) -> str:
    return f"ORTHO {'ON' if ortho_on else 'OFF'}  GRID {'ON' if grid_on else 'OFF'}"


def format_selection(count: int) -> str:
    return f"{count} entidades"


def format_zoom(scale: float) -> str:
    return f"Escala: {scale:.2f}"