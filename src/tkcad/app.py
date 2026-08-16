
import tkinter as tk
from .core import (ALL_SNAP_MODES, TARGET_KIND_MAP, Command, CommandResult, 
                   Entity, Point, parse_number, parse_point, CommandLineManager,
                   SnapEngine, ProjectIO, Document,
)
from .commands.registry import register_all
from .ui.console import ConsoleWidget
from .ui.canvas import CadCanvas
from .ui.grips import GripManager
from pathlib import Path
from tkinter import filedialog


# ============================================================
# Aplicación principal
# ============================================================

class CadApp(Document):
    def __init__(self, root: tk.Tk):
        super().__init__()
        self.root = root
        root.title("Editor con ventana de comandos")
        root.geometry("900x600")
        root.protocol("WM_DELETE_WINDOW", self._close_window)
        
        # self.entities = []
        # self.next_entity_id = 1
        self.current_file = None

        self.preview_line = None
        self.preview_points = None

        # self.snap_modes = {
        #     "GRID",
        #     "ENDPOINT",
        #     "MIDPOINT",
        # }

        # self.grid_size = 10.0
        # self.snap_tolerance_pixels = 8
        self.snaps = SnapEngine()

        self.show_grid = True

        # Canvas
        self.canvas = CadCanvas(root)
        self.grip_manager = GripManager(self.canvas, self)
        self.canvas.grip_manager = self.grip_manager
        self.canvas.app = self
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.canvas.redraw())

        # Consola
        self.console = ConsoleWidget(root, on_command=self._process_command)
        self.console.pack(fill="x")

        # Gestor de comandos
        self.manager = CommandLineManager(self)
        self.console.set_completion_callback(self.manager.get_completions)
        # self.manager.register(LineCommand) asi para todos o como sigue a continuacion
        register_all(self.manager)

        self.project_io = ProjectIO()

        self.write("Editor iniciado.")
        self.write("Escribe AYUDA o pulsa Tab para ver los comandos disponibles.")
        self.prompt("Comando:")

    def _process_command(self, text: str):
        self.manager.process_input(text)

        if hasattr(self, "console"):
            self.console.entry.focus_set()

        self._update_command_cursor()

    # metodos auxiliares pulsacion de raton
    def _command_waiting_for_point(self) -> bool:
        return (
            hasattr(self, "manager")
            and self.manager.is_waiting_for_point()
        )

    def _update_command_cursor(self):
        if self._command_waiting_for_point():
            self.canvas.config(cursor="crosshair")
        else:
            self.canvas.config(cursor="arrow")

    # Seleccionar entidades por ventana de selección
    def _select_by_window(self, x0, y0, x1, y1, action="replace"):
        rect = (
            min(x0, x1),
            min(y0, y1),
            max(x0, x1),
            max(y0, y1),
        )

        mode = "window" if x1 >= x0 else "crossing"

        selected_ids = []

        for item_id, entity_id in self.canvas.item_to_entity.items():
            bbox = self.canvas.bbox(item_id)

            if bbox is None:
                continue

            if mode == "window":
                if self._bbox_inside(bbox, rect):
                    selected_ids.append(entity_id)

            else:
                if self._bbox_intersects(bbox, rect):
                    selected_ids.append(entity_id)

        # Quitar duplicados manteniendo orden
        selected_ids = list(dict.fromkeys(selected_ids))

        if action == "add":
            self.add_selection_ids(selected_ids)

        elif action == "remove":
            self.remove_selection_ids(selected_ids)

        else:
            self.set_selection_ids(selected_ids)

        self.write(
            f"Seleccionadas: {self.selection_count()}"
        )

    def _bbox_inside(self, bbox, rect):
        return (
            bbox[0] >= rect[0]
            and bbox[1] >= rect[1]
            and bbox[2] <= rect[2]
            and bbox[3] <= rect[3]
        )

    def _bbox_intersects(self, bbox, rect):
        return not (
            bbox[2] < rect[0]
            or bbox[0] > rect[2]
            or bbox[3] < rect[1]
            or bbox[1] > rect[3]
        )    
    # end seleccion por ventana

    # --------------------------------------------------------
    # Métodos usados por los comandos
    # --------------------------------------------------------

    def write(self, message: str):
        self.console.write(message)

    def log(self, message: str):
        self.write(message)

    def prompt(self, message: str):
        self.console.write(message)

    def get_command_names(self):
        return self.manager.get_available_command_names()

    def get_command_help(self):
        return self.manager.get_available_command_help()

    def show_preview_polyline(self, points: list):
        self.preview_points = list(points)
        self.redraw()

    def show_preview_line(self, start: Point, end: Point):
        self.preview_line = (start, end)
        self.redraw()

    def clear_preview(self):
        self.preview_line = None
        self.preview_points = None
        self.redraw()
    # exit app
    def exit_app(self):
        self.root.after(100, self._close_window)

    def _close_window(self):
        # Aquí podrías guardar cambios, cerrar archivos, etc.
        self.root.destroy()
    # end exit app
    def save_project(self, filepath=None, force_dialog: bool = False):
        try:
            # ----------------------------------------------------
            # Decidir ruta
            # ----------------------------------------------------
            if filepath is None:
                # Guardar normal: si hay archivo actual, usarlo
                if self.current_file is not None and not force_dialog:
                    path = Path(self.current_file)

                # Guardar como / sin archivo actual: diálogo
                else:
                    initialdir = None
                    initialfile = "proyecto.json"

                    if self.current_file is not None:
                        initialdir = str(Path(self.current_file).parent)
                        initialfile = Path(self.current_file).name

                    selected = filedialog.asksaveasfilename(
                        parent=self.root,
                        title="Guardar proyecto",
                        defaultextension=".json",
                        filetypes=[
                            ("Proyecto JSON", "*.json"),
                            ("Todos los archivos", "*.*"),
                        ],
                        initialdir=initialdir,
                        initialfile=initialfile,
                    )

                    if not selected:
                        return False, "Guardado cancelado."

                    path = Path(selected).expanduser()

            else:
                path = Path(filepath).expanduser()

            # Guardar de verdad (ProjectIO)
            path = self.project_io.save(
                path, self.entities, self.next_entity_id,
                layers=self.layers,
                current_layer=self.current_layer,
            )
            self.current_file = path
            self.root.title(f"Editor - {path.name}")
            return True, f"Proyecto guardado en: {path}"
        except Exception as ex:
            return False, f"Error al guardar: {ex}"

    def load_project(self, filepath=None):
        try:
            if filepath is None:
                selected = filedialog.askopenfilename(
                    parent=self.root,
                    title="Abrir proyecto",
                    filetypes=[
                        ("Proyecto JSON", "*.json"),
                        ("Todos los archivos", "*.*"),
                    ],
                )

                if not selected:
                    return False, "Apertura cancelada."

                path = Path(selected).expanduser()

            else:
                path = Path(filepath).expanduser()

            entities, next_id, layers, current_layer, path = self.project_io.load(path)
            self.entities = entities
            self.next_entity_id = next_id
            self.layers = layers                     # ← NUEVO
            self.current_layer = current_layer
            self.current_file = path
            self.redraw()
            self.root.title(f"Editor - {path.name}")
            return True, f"Proyecto abierto: {path}"
        except Exception as ex:
            return False, f"Error al abrir: {ex}"

    def new_project(self):
        self.entities = []
        self.next_entity_id = 1
        self.current_file = None
        self.canvas.item_to_entity = {}

        if hasattr(self, "preview_line"):
            self.preview_line = None

        if hasattr(self, "preview_points"):
            self.preview_points = None

        self.redraw()

        self.root.title("Editor - Nuevo proyecto")

    # --------------------------------------------------------
    # Dibujo
    # --------------------------------------------------------

    def redraw(self):
        self.canvas.redraw()

    def notify_change(self):
        self.redraw()

    def toggle_show_grid(self):
        self.show_grid = not self.show_grid
        self.redraw()
        return self.show_grid

    # métodos para configurar los snaps
    def get_snap_modes(self):
        return sorted(self.snap_modes)

    def toggle_snap_mode(self, mode: str):
        if mode in self.snap_modes:
            self.snap_modes.remove(mode)
            active = False
        else:
            self.snap_modes.add(mode)
            active = True

        self.redraw()

        return active

    def set_all_snap_modes(self):
        self.snap_modes = set(ALL_SNAP_MODES)
        self.redraw()

    def clear_snap_modes(self):
        self.snap_modes = set()
        self.redraw()

    def set_grid_size(self, size: float):
        if size > 1e-9:
            self.grid_size = float(size)
            self.redraw()    
    # end métodos para configurar los snaps

    # --------------------------------------------------------
    # Snaps (delegan en self.snaps)
    # --------------------------------------------------------
    def get_snap_modes(self):
        return self.snaps.get_snap_modes()

    def toggle_snap_mode(self, mode: str):
        active = self.snaps.toggle_snap_mode(mode)
        self.redraw()
        return active

    def set_all_snap_modes(self):
        self.snaps.set_all_snap_modes()
        self.redraw()

    def clear_snap_modes(self):
        self.snaps.clear_snap_modes()
        self.redraw()

    def set_grid_size(self, size: float):
        self.snaps.set_grid_size(size)
        self.redraw()

    def snap_point(self, p: Point, base_point: Point = None, ignore_entity_id=None):
        return self.snaps.snap_point(
            self.entities, p,
            base_point=base_point,
            ignore_entity_id=ignore_entity_id,
            scale = self.canvas.scale,
        )

    @property
    def grid_size(self):
        return self.snaps.grid_size

    @grid_size.setter
    def grid_size(self, value):
        self.snaps.grid_size = value

  
# ============================================================
# Ejecución
# ============================================================
    
def main():
    root = tk.Tk()
    app = CadApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()