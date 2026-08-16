import tkinter as tk
from tkinter.scrolledtext import ScrolledText


# ============================================================
# Widget de consola
# ============================================================

class ConsoleWidget(tk.Frame):
    def __init__(self, parent, on_command=None):
        super().__init__(parent, bg="#1e1e1e")

        self.on_command = on_command
        self.history = []
        self.history_index = 0

        self.output = ScrolledText(
            self,
            height=8,
            bg="#111111",
            fg="#00ff66",
            insertbackground="white",
            font=("Consolas", 10),
            state="disabled",
        )
        self.output.pack(side="top", fill="both", expand=True)

        self.entry = tk.Entry(
            self,
            bg="#222222",
            fg="white",
            insertbackground="white",
            font=("Consolas", 11),
            relief="flat",
        )
        self.entry.pack(side="bottom", fill="x")

        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Up>", self._on_up)
        self.entry.bind("<Down>", self._on_down)
        self.entry.bind("<Escape>", self._on_escape)

        self.completion_callback = None
        self.entry.bind("<Tab>", self._on_tab)

        self.entry.bind("<Control-z>", lambda e: self.app.undo())
        self.entry.bind("<Control-y>", lambda e: self.app.redo())

        self.entry.bind("<F8>", lambda e: self.app.toggle_ortho())

        self.entry.focus_set()

    def write(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _on_enter(self, event=None):
        text = self.entry.get()
        self.entry.delete(0, "end")

        if text.strip():
            self.history.append(text)
            self.history_index = len(self.history)

        if self.on_command:
            self.on_command(text)

        return "break"

    def _on_up(self, event=None):
        if not self.history:
            return "break"

        if self.history_index > 0:
            self.history_index -= 1
            self._show_history()

        return "break"

    def _on_down(self, event=None):
        if not self.history:
            return "break"

        if self.history_index < len(self.history):
            self.history_index += 1

            if self.history_index == len(self.history):
                self.entry.delete(0, "end")
            else:
                self._show_history()

        return "break"

    def _on_escape(self, event=None):
        self.entry.delete(0, "end")

        if self.on_command:
            self.on_command("ESC")

        return "break"

    def _show_history(self):
        self.entry.delete(0, "end")

        if 0 <= self.history_index < len(self.history):
            self.entry.insert(0, self.history[self.history_index])

    def set_completion_callback(self, callback):
        self.completion_callback = callback

    def _on_tab(self, event=None):
        if self.completion_callback is None:
            return "break"

        text = self.entry.get().strip()
        matches = self.completion_callback(text)

        if not matches:
            return "break"

        if len(matches) == 1:
            self._set_entry_text(matches[0])
            return "break"

        common = self._common_prefix(matches)

        if common and common != text:
            self._set_entry_text(common)

        self.write("Coincidencias:")
        self.write("  " + ", ".join(matches))

        return "break"

    def _set_entry_text(self, text: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, text)
        self.entry.icursor("end")

    def _common_prefix(self, strings):
        if not strings:
            return ""

        prefix = strings[0]

        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]

                if not prefix:
                    return ""

        return prefix
