"""Panel lateral de gestión de capas (GUI)."""

import tkinter as tk
from tkinter import ttk, colorchooser


class LayerPanel(ttk.Frame):
    """Lista interactiva de capas conectada al modelo (app)."""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._build()

    # --------------------------------------------------------
    # Construcción
    # --------------------------------------------------------
    def _build(self):
        cols = ("name", "visible", "locked", "color")

        self.tree = ttk.Treeview(
            self, columns=cols, show="headings",
            height=10, selectmode="browse",
        )
        headings = {"name": "Capa", "visible": "Vis", "locked": "Bloq", "color": "Color"}
        widths = {"name": 90, "visible": 40, "locked": 40, "color": 50}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="center")
        self.tree.column("name", anchor="w")
        self.tree.pack(fill="both", expand=True)

        btn = ttk.Frame(self)
        btn.pack(fill="x", pady=4)
        ttk.Button(btn, text="Nueva", command=self.on_new).pack(side="left", expand=True)
        ttk.Button(btn, text="Borrar", command=self.on_delete).pack(side="left", expand=True)

        self.tree.bind("<Button-1>", self.on_click)

    # --------------------------------------------------------
    # Refresco (lo llama la app tras cada cambio)
    # --------------------------------------------------------
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        current = getattr(self.app, "current_layer", None)

        for layer in self.app.layers.values():
            prefix = "* " if layer.name == current else "  "
            self.tree.insert(
                "", "end", iid=layer.name,
                values=(
                    prefix + layer.name,
                    "ON" if layer.visible else "OFF",
                    "SI" if layer.locked else "no",
                    layer.color or "-",
                ),
            )

    # --------------------------------------------------------
    # Interacción
    # --------------------------------------------------------
    def on_click(self, event):
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row:
            return
        name = row  # iid = nombre de la capa

        if col == "#1":                      # nombre → capa actual
            self.app.set_current_layer(name)
        elif col == "#2":                    # visible → on/off
            self.app.toggle_layer_visible(name)
        elif col == "#3":                    # bloqueo
            self.app.toggle_layer_locked(name)
        elif col == "#4":                    # color → diálogo
            self.on_color(name)

        self.app.redraw()
        self.refresh()

    def on_color(self, name):
        layer = self.app.get_layer(name)
        if layer is None:
            return
        result = colorchooser.askcolor(
            parent=self,
            title=f"Color de la capa {name}",
            initialcolor=layer.color or "#ffffff",
        )
        if result and result[1]:
            self.app.set_layer_color(name, result[1])
            self.app.redraw()
            self.refresh()

    def on_new(self):
        dlg = tk.simpledialog if hasattr(tk, "simpledialog") else None
        from tkinter import simpledialog
        name = simpledialog.askstring("Nueva capa", "Nombre de la capa:", parent=self)
        if name:
            self.app.add_layer(name.strip())
            self.refresh()

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        self.app.delete_layer(sel[0])
        self.refresh()