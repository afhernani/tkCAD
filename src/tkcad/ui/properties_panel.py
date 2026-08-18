"""Panel lateral de propiedades de la entidad seleccionada."""

import tkinter as tk
from tkinter import ttk, simpledialog


class PropertiesPanel(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self):
        ttk.Label(self, text="Propiedades").pack(pady=(4, 2))

        self.tree = ttk.Treeview(
            self, columns=("prop", "value"), show="headings",
            height=12, selectmode="browse",
        )
        self.tree.heading("prop", text="Propiedad")
        self.tree.heading("value", text="Valor")
        self.tree.column("prop", width=80)
        self.tree.column("value", width=110)
        self.tree.pack(fill="both", expand=True)

        ttk.Label(self, text="Doble clic para editar",
                  foreground="gray").pack(pady=2)
        self.tree.bind("<Double-1>", self.on_double)

    def refresh(self):
        try:
            self.tree.delete(*self.tree.get_children())
            sel = self.app.get_selected_entities()

            if len(sel) == 0:
                self.tree.insert("", "end", values=("—", "Sin selección"))
                return
            if len(sel) > 1:
                self.tree.insert("", "end", values=("—", f"{len(sel)} entidades"))
                return

            for field, value in self.app.get_entity_properties(sel[0].id):
                self.tree.insert("", "end", iid=field, values=(field, value))
        except tk.TclError:
            pass

    def on_double(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        sel = self.app.get_selected_entities()
        if len(sel) != 1:
            return

        new = simpledialog.askstring(
            "Editar", f"Nuevo valor para '{row}':", parent=self,
        )
        if new is None:
            return

        ok, msg = self.app.set_entity_property(sel[0].id, row, new)
        if not ok:
            self.app.write(msg)
        self.app.redraw()
        self.refresh()