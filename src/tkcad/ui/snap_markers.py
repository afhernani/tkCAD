"""Marcadores visuales de snap (osnap) para tkCAD.

Dibuja un símbolo distintivo en el canvas cuando el SnapEngine
detecta un punto de snap bajo el cursor.
"""

MARKER_SIZE = 6  # tamaño en píxeles (independiente del zoom)

# Color y formas por tipo de snap
SNAP_MARKER_KINDS = {
    "ENDPOINT", "MIDPOINT", "CENTER", "QUADRANT",
    "INTERSECTION", "TANGENT", "PERPENDICULAR", "NEAREST", "POINT",
}

COLORS = {
    "ENDPOINT": "#00ffff",      # cian
    "MIDPOINT": "#00ff00",      # verde
    "CENTER": "#ff00ff",        # magenta
    "QUADRANT": "#ffff00",      # amarillo
    "INTERSECTION": "#ff8800",  # naranja
    "TANGENT": "#ff00ff",
    "PERPENDICULAR": "#00ffff",
    "NEAREST": "#88ff88",
    "POINT": "#ffffff",
}


class SnapMarkerDrawer:
    """Dibuja y limpia marcadores de snap sobre un canvas Tkinter."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.items = []

    def clear(self):
        for item in self.items:
            try:
                self.canvas.delete(item)
            except Exception:
                pass
        self.items = []

    def draw(self, x, y, kind):
        """Dibuja el marcador del tipo de snap en (x, y) de canvas."""
        self.clear()
        color = COLORS.get(kind, "#ffffff")
        s = MARKER_SIZE

        if kind == "ENDPOINT":
            self.items.append(self.canvas.create_rectangle(
                x - s, y - s, x + s, y + s, outline=color, width=1))

        elif kind == "MIDPOINT":
            self.items.append(self.canvas.create_polygon(
                x, y - s, x - s, y + s, x + s, y + s,
                outline=color, fill=""))

        elif kind == "CENTER":
            self.items.append(self.canvas.create_oval(
                x - s, y - s, x + s, y + s, outline=color, width=1))

        elif kind == "QUADRANT":
            self.items.append(self.canvas.create_polygon(
                x, y - s, x + s, y, x, y + s, x - s, y,
                outline=color, fill=""))

        elif kind == "INTERSECTION":
            self.items.append(self.canvas.create_line(
                x - s, y - s, x + s, y + s, fill=color))
            self.items.append(self.canvas.create_line(
                x - s, y + s, x + s, y - s, fill=color))

        elif kind == "TANGENT":
            self.items.append(self.canvas.create_oval(
                x - s, y - s, x + s, y + s, outline=color))
            self.items.append(self.canvas.create_line(
                x - s, y, x + s, y, fill=color))

        elif kind == "PERPENDICULAR":
            self.items.append(self.canvas.create_line(
                x - s, y, x - s, y - s, fill=color))
            self.items.append(self.canvas.create_line(
                x - s, y - s, x, y - s, fill=color))

        elif kind == "NEAREST":
            self.items.append(self.canvas.create_line(
                x, y - s, x, y + s, fill=color))

        else:  # POINT
            self.items.append(self.canvas.create_rectangle(
                x - 2, y - 2, x + 2, y + 2, outline=color))