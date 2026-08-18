"""Barra de estado con información en vivo."""

import tkinter as tk
from tkinter import ttk

from ..core.status_format import (
    format_coords, format_flags, format_selection, format_snaps, format_zoom,
)


class StatusBar(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.vars = {}
        self._build()

    def _build(self):
        fields = [
            ("coords", "X: —  Y: —", 20),
            ("layer", "Capa: 0", 12),
            ("snaps", "SNAP: —", 26),
            ("flags", "ORTHO OFF  GRID ON", 22),
            ("sel", "0 entidades", 12),
            ("zoom", "Escala: 1.00", 14),
        ]
        for key, initial, width in fields:
            var = tk.StringVar(value=initial)
            ttk.Label(
                self, textvariable=var, width=width,
                relief="sunken", anchor="w",
            ).pack(side="left", padx=1)
            self.vars[key] = var

    def set_coords(self, x, y):
        try:
            self.vars["coords"].set(format_coords(x, y))
        except tk.TclError:
            pass

    def refresh(self):
        try:
            app = self.app
            modes = set(app.get_snap_modes())
            self.vars["layer"].set(f"Capa: {app.current_layer}")
            self.vars["snaps"].set(format_snaps(modes - {"ORTHO", "GRID"}))
            self.vars["flags"].set(format_flags("ORTHO" in modes, app.show_grid))
            self.vars["sel"].set(format_selection(app.selection_count()))
            self.vars["zoom"].set(format_zoom(app.canvas.scale))
        except tk.TclError:
            pass