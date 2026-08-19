"""Barra de herramientas con iconos generados por Pillow."""

import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from ..core.icons import TOOLBAR_COMMANDS, build_icon


class ToolBar(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._photos = []   # referencias para que Tk no libere las imágenes

        for name, label in TOOLBAR_COMMANDS:
            photo = ImageTk.PhotoImage(build_icon(name))
            self._photos.append(photo)

            btn = ttk.Button(
                self, image=photo,
                command=lambda n=name: self.app.run_command(n),
            )
            btn.pack(side="left", padx=1, pady=2)
            self._bind_tooltip(btn, f"{label}  ({name})")

    def _bind_tooltip(self, widget, text):
        """Tooltip ligero con un Toplevel (sin dependencias)."""
        tip = {"win": None}

        def show(e):
            if tip["win"]:
                return
            x = widget.winfo_rootx() + 4
            y = widget.winfo_rooty() + widget.winfo_height() + 2
            win = tk.Toplevel(self)
            win.wm_overrideredirect(True)
            win.wm_geometry(f"+{x}+{y}")
            ttk.Label(win, text=text, relief="solid", borderwidth=1).pack()
            tip["win"] = win

        def hide(e):
            if tip["win"]:
                tip["win"].destroy()
                tip["win"] = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)