import math, copy
import tkinter as tk
# from typing import Optional, List, Dict, Type
# from enum import Enum, auto
from .core import (ALL_SNAP_MODES, TARGET_KIND_MAP, Command, CommandResult, 
                   Entity, Point, parse_number, parse_point, CommandLineManager,
                   SnapEngine
)
from .commands.registry import register_all
from .geometry import line_line_intersection, projection_param, EPS
from .ui.console import ConsoleWidget
from .ui.canvas import CadCanvas
from .ui.grips import GripManager
import json
from pathlib import Path
from tkinter import filedialog


# ============================================================
# Aplicación principal
# ============================================================

class CadApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Editor con ventana de comandos")
        root.geometry("900x600")
        root.protocol("WM_DELETE_WINDOW", self._close_window)
        
        self.entities = []
        self.next_entity_id = 1
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
    # Añadir y quitar ids de selección
    def add_selection_ids(self, ids):
        ids_set = set(ids)

        for entity in self.entities:
            if entity.id in ids_set:
                entity.selected = True

        self.redraw()

    def remove_selection_ids(self, ids):
        ids_set = set(ids)

        for entity in self.entities:
            if entity.id in ids_set:
                entity.selected = False

        self.redraw()    
    # end añadir y quitar ids de selección

    # --------------------------------------------------------
    # Métodos usados por los comandos
    # --------------------------------------------------------

    def write(self, message: str):
        self.console.write(message)

    def prompt(self, message: str):
        self.console.write(message)

    def get_command_names(self):
        return self.manager.get_available_command_names()

    def get_command_help(self):
        return self.manager.get_available_command_help()

    def add_entity(self, kind: str, data: dict, redraw: bool = True) -> Entity:
        entity = Entity(
            id=self.next_entity_id,
            kind=kind,
            data=data,
            selected=False,
        )

        self.next_entity_id += 1
        self.entities.append(entity)

        if redraw:
            self.redraw()

        return entity

    def add_line(self, start: Point, end: Point):
        self.add_entity(
            "line",
            {
                "start": start,
                "end": end,
            }
        )

    def add_polyline(self, points):
        self.add_entity(
            "polyline",
            {
                "points": list(points),
            }
        )

    def add_circle(self, center: Point, radius: float):
        self.add_entity(
            "circle",
            {
                "center": center,
                "radius": radius,
            }
        )

    def add_arc(self, center: Point, radius: float, start_angle: float, extent: float):
        self.add_entity(
            "arc",
            {
                "center": center,
                "radius": radius,
                "start_angle": start_angle,
                "extent": extent,
            }
        )

    def add_polygon(self, points):
        self.add_entity(
            "polygon",
            {
                "points": list(points),
            }
        )

    def add_ellipse(self, center: Point, radius_x: float, radius_y: float, rotation: float = 0.0):
        """ Agrega una elipse al modelo."""
        self.add_entity(
            "ellipse",
            {
                "center": center,
                "radius_x": float(radius_x),
                "radius_y": float(radius_y),
                "rotation": float(rotation) % 360.0,
            },
        )

    def get_entity_by_id(self, entity_id: int):
        for entity in self.entities:
            if entity.id == entity_id:
                return entity

        return None

    def has_selection(self) -> bool:
        return any(entity.selected for entity in self.entities)

    def selection_count(self) -> int:
        return sum(1 for entity in self.entities if entity.selected)

    def get_selected_entities(self):
        return [entity for entity in self.entities if entity.selected]

    def select_all(self):
        for entity in self.entities:
            entity.selected = True

        self.redraw()

    def clear_selection(self):
        for entity in self.entities:
            entity.selected = False

        self.redraw()

    def select_last(self):
        if self.entities:
            self.entities[-1].selected = True
            self.redraw()

    def select_kind(self, kind: str):
        for entity in self.entities:
            if entity.kind == kind:
                entity.selected = True

        self.redraw()

    def toggle_selection(self, entity_id: int, redraw: bool = True) -> bool:
        entity = self.get_entity_by_id(entity_id)

        if entity is None:
            return False

        entity.selected = not entity.selected

        if redraw:
            self.redraw()

        return True

    def set_selection_ids(self, ids):
        ids_set = set(ids)

        for entity in self.entities:
            entity.selected = entity.id in ids_set

        self.redraw()

    def delete_selected(self):
        selected_count = self.selection_count()

        if selected_count == 0:
            return 0

        self.entities = [
            entity
            for entity in self.entities
            if not entity.selected
        ]

        self.redraw()

        return selected_count

    def delete_entities(self, target: str):
        if target == "TODO":
            count = len(self.entities)
            self.entities = []
            self.redraw()
            return count

        kind = TARGET_KIND_MAP.get(target)

        if kind is None:
            return 0

        count = sum(
            1
            for entity in self.entities
            if entity.kind == kind
        )

        if count > 0:
            self.entities = [
                entity
                for entity in self.entities
                if entity.kind != kind
            ]

            self.redraw()

        return count

    def copy_selected(self, dx: float, dy: float):
        selected = self.get_selected_entities()

        if not selected:
            return []

        new_ids = []

        for entity in selected:
            new_data = copy.deepcopy(entity.data)

            new_entity = self.add_entity(
                entity.kind,
                new_data,
                redraw=False,
            )

            self._move_entity(new_entity, dx, dy)

            new_ids.append(new_entity.id)

        self.redraw()

        return new_ids

    def copy_entities(self, target: str, dx: float, dy: float):
        if target == "TODO":
            source = list(self.entities)
        else:
            kind = TARGET_KIND_MAP.get(target)

            if kind is None:
                return []

            source = [
                entity
                for entity in self.entities
                if entity.kind == kind
            ]

        new_ids = []

        for entity in source:
            new_data = copy.deepcopy(entity.data)

            new_entity = self.add_entity(
                entity.kind,
                new_data,
                redraw=False,
            )

            self._move_entity(new_entity, dx, dy)

            new_ids.append(new_entity.id)

        self.redraw()

        return new_ids
    # ESCALAR
    def _scale_point(self, p: Point, base: Point, factor: float) -> Point:
        return Point(
            base.x + factor * (p.x - base.x),
            base.y + factor * (p.y - base.y),
        )

    def _scale_entity(self, entity, base: Point, factor: float):
        if entity.kind == "line":
            entity.data["start"] = self._scale_point(
                entity.data["start"],
                base,
                factor,
            )

            entity.data["end"] = self._scale_point(
                entity.data["end"],
                base,
                factor,
            )

        elif entity.kind in ("polyline", "polygon"):
            entity.data["points"] = [
                self._scale_point(p, base, factor)
                for p in entity.data["points"]
            ]

        elif entity.kind == "circle":
            entity.data["center"] = self._scale_point(
                entity.data["center"],
                base,
                factor,
            )

            entity.data["radius"] = entity.data["radius"] * factor

        elif entity.kind == "arc":
            entity.data["center"] = self._scale_point(
                entity.data["center"],
                base,
                factor,
            )

            entity.data["radius"] = entity.data["radius"] * factor

        elif entity.kind == "ellipse":
            entity.data["center"] = self._scale_point(
                entity.data["center"],
                base,
                factor,
            )

            entity.data["radius_x"] = float(entity.data["radius_x"]) * factor
            entity.data["radius_y"] = float(entity.data["radius_y"]) * factor

    def scale_selected(self, base: Point, factor: float) -> int:
        if factor <= 0:
            return 0

        selected = self.get_selected_entities()

        for entity in selected:
            self._scale_entity(entity, base, factor)

        self.redraw()

        return len(selected)

    def scale_entities(self, target: str, base: Point, factor: float) -> int:
        if factor <= 0:
            return 0

        if target == "TODO":
            entities = self.entities
        else:
            kind = TARGET_KIND_MAP.get(target)

            if kind is None:
                return 0

            entities = [
                entity
                for entity in self.entities
                if entity.kind == kind
            ]

        for entity in entities:
            self._scale_entity(entity, base, factor)

        self.redraw()

        return len(entities)
    # simetría.
    def _mirror_point(self, p: Point, a: Point, b: Point) -> Point:
        vx = b.x - a.x
        vy = b.y - a.y

        denom = vx * vx + vy * vy

        if denom < EPS:
            return Point(p.x, p.y)

        t = ((p.x - a.x) * vx + (p.y - a.y) * vy) / denom

        proj_x = a.x + t * vx
        proj_y = a.y + t * vy

        return Point(
            2.0 * proj_x - p.x,
            2.0 * proj_y - p.y,
        )

    def _mirror_entity(self, entity, a: Point, b: Point, axis_angle_deg: float):
        if entity.kind == "line":
            entity.data["start"] = self._mirror_point(
                entity.data["start"],
                a,
                b,
            )

            entity.data["end"] = self._mirror_point(
                entity.data["end"],
                a,
                b,
            )

        elif entity.kind in ("polyline", "polygon"):
            entity.data["points"] = [
                self._mirror_point(p, a, b)
                for p in entity.data["points"]
            ]

        elif entity.kind == "circle":
            entity.data["center"] = self._mirror_point(
                entity.data["center"],
                a,
                b,
            )

        elif entity.kind == "arc":
            entity.data["center"] = self._mirror_point(
                entity.data["center"],
                a,
                b,
            )

            start = entity.data["start_angle"]
            extent = entity.data["extent"]

            # Al hacer simetría, el arco queda reflejado.
            # Si el arco original va desde start hasta start+extent,
            # el arco reflejado empieza en:
            #
            # 2*axis_angle - (start + extent)
            #
            # y mantiene el mismo extent.
            entity.data["start_angle"] = (
                2.0 * axis_angle_deg - (start + extent)
            ) % 360.0

        elif entity.kind == "ellipse":
            entity.data["center"] = self._mirror_point(
                entity.data["center"],
                a,
                b,
            )

            rotation = entity.data.get("rotation", 0.0)

            entity.data["rotation"] = (
                2.0 * axis_angle_deg - rotation
            ) % 360.0

    def mirror_selected(self, a: Point, b: Point) -> int:
        if abs(a.x - b.x) < EPS and abs(a.y - b.y) < EPS:
            return 0

        axis_angle_deg = math.degrees(
            math.atan2(b.y - a.y, b.x - a.x)
        )

        selected = self.get_selected_entities()

        for entity in selected:
            self._mirror_entity(entity, a, b, axis_angle_deg)

        self.redraw()

        return len(selected)

    def mirror_entities(self, target: str, a: Point, b: Point) -> int:
        if abs(a.x - b.x) < EPS and abs(a.y - b.y) < EPS:
            return 0

        axis_angle_deg = math.degrees(
            math.atan2(b.y - a.y, b.x - a.x)
        )

        if target == "TODO":
            entities = self.entities
        else:
            kind = TARGET_KIND_MAP.get(target)

            if kind is None:
                return 0

            entities = [
                entity
                for entity in self.entities
                if entity.kind == kind
            ]

        for entity in entities:
            self._mirror_entity(entity, a, b, axis_angle_deg)

        self.redraw()

        return len(entities)
    # recortar linea por linea
    def trim_line_by_line(self, limit_id: int, target_id: int, keep_point: Point):
        limit = self.get_entity_by_id(limit_id)
        target = self.get_entity_by_id(target_id)

        if limit is None or target is None:
            return False, "Entidad no encontrada."

        if limit.kind != "line" or target.kind != "line":
            return False, "Por ahora RECORTAR solo soporta LINEA con límite LINEA."

        if limit_id == target_id:
            return False, "La entidad límite y la entidad a recortar no pueden ser la misma."

        a = limit.data["start"]
        b = limit.data["end"]

        c = target.data["start"]
        d = target.data["end"]

        inter = line_line_intersection(a, b, c, d)

        if inter is None:
            return False, "Las líneas no se cortan."

        p, t_limit, u_target = inter

        # La intersección debe estar dentro del segmento límite.
        if not (-EPS <= t_limit <= 1.0 + EPS):
            return False, "La intersección está fuera de la línea límite."

        # La línea a recortar debe cruzar el límite.
        if not (EPS <= u_target <= 1.0 - EPS):
            return False, "La línea a recortar no cruza el límite correctamente."

        # Decidimos qué parte conservar.
        keep_t = projection_param(keep_point, c, d)

        if abs(keep_t - u_target) < EPS:
            return False, "El punto a conservar está demasiado cerca del punto de corte."

        if keep_t < u_target:
            # Conservamos desde el inicio original hasta el corte.
            target.data["start"] = c
            target.data["end"] = p
        else:
            # Conservamos desde el corte hasta el final original.
            target.data["start"] = p
            target.data["end"] = d

        self.redraw()

        return True, "Entidad recortada correctamente."
    # extender linea por linea
    def extend_line_to_line(self, limit_id: int, target_id: int):
        limit = self.get_entity_by_id(limit_id)
        target = self.get_entity_by_id(target_id)

        if limit is None or target is None:
            return False, "Entidad no encontrada."

        if limit.kind != "line" or target.kind != "line":
            return False, "Por ahora EXTENDER solo soporta LINEA con límite LINEA."

        if limit_id == target_id:
            return False, "La entidad límite y la entidad a extender no pueden ser la misma."

        a = limit.data["start"]
        b = limit.data["end"]

        c = target.data["start"]
        d = target.data["end"]

        inter = line_line_intersection(a, b, c, d)

        if inter is None:
            return False, "Las líneas no se cortan."

        p, t_limit, u_target = inter

        # La intersección debe estar dentro del segmento límite.
        if not (-EPS <= t_limit <= 1.0 + EPS):
            return False, "La intersección está fuera de la línea límite."

        # Si u_target está entre 0 y 1, la línea ya cruza el límite.
        if -EPS <= u_target <= 1.0 + EPS:
            return False, "La línea ya cruza la entidad límite."

        # Si u_target < 0, extendemos el punto inicial.
        if u_target < -EPS:
            target.data["start"] = p

        # Si u_target > 1, extendemos el punto final.
        else:
            target.data["end"] = p

        self.redraw()

        return True, "Entidad extendida correctamente."
    # json encode/decode
    def _encode_value(self, value):
        if isinstance(value, Point):
            return {
                "__type__": "Point",
                "x": value.x,
                "y": value.y,
            }

        if isinstance(value, list):
            return [self._encode_value(item) for item in value]

        return value

    def _decode_value(self, value):
        if isinstance(value, dict):
            if value.get("__type__") == "Point":
                return Point(
                    float(value["x"]),
                    float(value["y"]),
                )

            return value

        if isinstance(value, list):
            return [self._decode_value(item) for item in value]

        return value

    def _entity_to_dict(self, entity):
        return {
            "id": entity.id,
            "kind": entity.kind,
            "data": {
                key: self._encode_value(value)
                for key, value in entity.data.items()
            },
        }

    def _entity_from_dict(self, data):
        entity_id = int(data["id"])
        kind = str(data["kind"])

        raw_data = data.get("data", {})

        decoded_data = {
            key: self._decode_value(value)
            for key, value in raw_data.items()
        }

        return Entity(
            id=entity_id,
            kind=kind,
            data=decoded_data,
            selected=False,
        )
    # end json encode/decode

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
                    path = self.current_file

                # Guardar como / sin archivo actual: diálogo
                else:
                    initialdir = None
                    initialfile = "proyecto.json"

                    if self.current_file is not None:
                        initialdir = str(self.current_file.parent)
                        initialfile = self.current_file.name

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

                if path.suffix == "":
                    path = path.with_suffix(".json")

            # ----------------------------------------------------
            # Preparar datos
            # ----------------------------------------------------
            project_data = {
                "version": 1,
                "next_entity_id": self.next_entity_id,
                "entities": [
                    self._entity_to_dict(entity)
                    for entity in self.entities
                ],
            }

            # Crear carpetas si no existen
            path.parent.mkdir(parents=True, exist_ok=True)

            text = json.dumps(
                project_data,
                indent=2,
                ensure_ascii=False,
            )

            path.write_text(text, encoding="utf-8")

            self.current_file = path

            self.root.title(
                f"Editor - {path.name}"
            )

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

                # Si escribe "plano" y existe "plano.json"
                if not path.exists() and path.suffix == "":
                    alternative = path.with_suffix(".json")

                    if alternative.exists():
                        path = alternative

            if not path.exists():
                return False, f"No existe el archivo: {path}"

            text = path.read_text(encoding="utf-8")
            project_data = json.loads(text)

            entities = []
            max_id = 0

            for entity_data in project_data.get("entities", []):
                entity = self._entity_from_dict(entity_data)
                entities.append(entity)

                if entity.id > max_id:
                    max_id = entity.id

            self.entities = entities

            next_id = project_data.get("next_entity_id")

            if not isinstance(next_id, int) or next_id <= max_id:
                next_id = max_id + 1

            self.next_entity_id = next_id

            self.current_file = path

            self.redraw()

            self.root.title(
                f"Editor - {path.name}"
            )

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
        )

    @property
    def grid_size(self):
        return self.snaps.grid_size

    @grid_size.setter
    def grid_size(self, value):
        self.snaps.grid_size = value

    # --------------------------------------------------------
    # Mover entidades seleccionadas
    # --------------------------------------------------------
    def _move_point(self, p: Point, dx: float, dy: float) -> Point:
        return Point(p.x + dx, p.y + dy)

    def _move_entity(self, entity: Entity, dx: float, dy: float):
        if entity.kind == "line":
            entity.data["start"] = self._move_point(entity.data["start"], dx, dy)
            entity.data["end"] = self._move_point(entity.data["end"], dx, dy)

        elif entity.kind in ("polyline", "polygon"):
            entity.data["points"] = [
                self._move_point(p, dx, dy)
                for p in entity.data["points"]
            ]

        elif entity.kind == "circle":
            entity.data["center"] = self._move_point(entity.data["center"], dx, dy)

        elif entity.kind == "arc":
            entity.data["center"] = self._move_point(entity.data["center"], dx, dy)

        elif entity.kind == "ellipse":
            entity.data["center"] = self._move_point(
                entity.data["center"],
                dx,
                dy,
            )        

    def move_selected(self, dx: float, dy: float):
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            self.write("Desplazamiento cero.")
            return

        for entity in self.get_selected_entities():
            self._move_entity(entity, dx, dy)

        self.redraw()

    def move_entities(self, target: str, dx: float, dy: float):
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            self.write("Desplazamiento cero.")
            return

        if target == "TODO":
            for entity in self.entities:
                self._move_entity(entity, dx, dy)

        else:
            kind = TARGET_KIND_MAP.get(target)

            if kind is None:
                self.write(f"No se puede mover: {target}")
                return

            for entity in self.entities:
                if entity.kind == kind:
                    self._move_entity(entity, dx, dy)

        self.redraw()

    def _rotate_point(self, p: Point, base: Point, angle_deg: float) -> Point:
        rad = math.radians(angle_deg)

        dx = p.x - base.x
        dy = p.y - base.y

        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        x = base.x + dx * cos_r - dy * sin_r
        y = base.y + dx * sin_r + dy * cos_r

        return Point(x, y)

    def _rotate_entity(self, entity, base: Point, angle_deg: float):
        if entity.kind == "line":
            entity.data["start"] = self._rotate_point(
                entity.data["start"],
                base,
                angle_deg,
            )

            entity.data["end"] = self._rotate_point(
                entity.data["end"],
                base,
                angle_deg,
            )

        elif entity.kind in ("polyline", "polygon"):
            entity.data["points"] = [
                self._rotate_point(p, base, angle_deg)
                for p in entity.data["points"]
            ]

        elif entity.kind == "circle":
            entity.data["center"] = self._rotate_point(
                entity.data["center"],
                base,
                angle_deg,
            )

        elif entity.kind == "arc":
            entity.data["center"] = self._rotate_point(
                entity.data["center"],
                base,
                angle_deg,
            )

            entity.data["start_angle"] = (
                entity.data["start_angle"] + angle_deg # cambiar signo a - si aparecen los arcos rodados.
            ) % 360.0

        elif entity.kind == "ellipse":
            entity.data["center"] = self._rotate_point(
                entity.data["center"],
                base,
                angle_deg,
            )

            entity.data["rotation"] = (
                entity.data.get("rotation", 0.0) + angle_deg
            ) % 360.0

    def rotate_selected(self, base: Point, angle_deg: float):
        if abs(angle_deg) < 1e-9:
            return 0

        selected = self.get_selected_entities()

        for entity in selected:
            self._rotate_entity(entity, base, angle_deg)

        self.redraw()

        return len(selected)

    def rotate_entities(self, target: str, base: Point, angle_deg: float):
        if abs(angle_deg) < 1e-9:
            return 0

        if target == "TODO":
            entities = self.entities
        else:
            kind = TARGET_KIND_MAP.get(target)

            if kind is None:
                return 0

            entities = [
                entity
                for entity in self.entities
                if entity.kind == kind
            ]

        for entity in entities:
            self._rotate_entity(entity, base, angle_deg)

        self.redraw()

        return len(entities)
   
# ============================================================
# Ejecución
# ============================================================
    
def main():
    root = tk.Tk()
    app = CadApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()