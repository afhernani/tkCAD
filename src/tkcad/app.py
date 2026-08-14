import math, copy
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from typing import Optional, List, Dict, Type
from enum import Enum, auto

from .core import ALL_SNAP_MODES, TARGET_KIND_MAP, Command, CommandResult, Entity, Point, parse_number, parse_point
from .commands.registry import register_all
from .geometry import line_line_intersection, projection_param, EPS

import json
from pathlib import Path
from tkinter import filedialog



# ============================================================
# Gestor de comandos
# ============================================================

class CommandLineManager:
    def __init__(self, ctx):
        self.ctx = ctx
        self.active: Optional[Command] = None
        self.factories: Dict[str, Type[Command]] = {}

    def register(self, command_class: Type[Command]):
        cmd = command_class()

        self.factories[cmd.name.upper()] = command_class

        for alias in cmd.aliases:
            self.factories[alias.upper()] = command_class

    def get_available_command_names(self):
        names = {
            command_class.name.upper()
            for command_class in self.factories.values()
        }

        return sorted(names)

    def get_available_command_help(self):
        help_items = {}

        for alias, command_class in self.factories.items():
            name = command_class.name.upper()

            if name not in help_items:
                help_items[name] = set()

            alias_upper = alias.upper()

            if alias_upper != name:
                help_items[name].add(alias_upper)

        return sorted(
            (name, sorted(aliases))
            for name, aliases in help_items.items()
        )

    def get_completions(self, text: str):
        text = text.strip().upper()

        # Si hay un comando activo, preguntamos al comando
        # si tiene autocompletado contextual.
        if self.active is not None:
            if hasattr(self.active, "get_completions"):
                return self.active.get_completions(self.ctx, text)

            return []

        # Si no hay comando activo y el texto está vacío,
        # mostramos todos los comandos.
        if not text:
            return self.get_available_command_names()

        matches = set()

        for alias, command_class in self.factories.items():
            alias_upper = alias.upper()
            name_upper = command_class.name.upper()

            if alias_upper.startswith(text) or name_upper.startswith(text):
                matches.add(name_upper)

        return sorted(matches)

    def process_input(self, text: str, echo: bool = True):
        text = text.strip()

        # Enter vacío: sirve para terminar o cancelar el comando activo.
        if not text:
            if self.active is not None:
                result = self.active.handle_input(self.ctx, "")
                if result == CommandResult.FINISHED:
                    self.active = None
                    self.ctx.prompt("Comando:")
            return

        if echo:
            self.ctx.write(f"> {text}")

        # ESC cancela el comando activo
        if text.upper() == "ESC":
            if self.active is not None:
                self.ctx.write("Comando cancelado.")
                self.ctx.clear_preview()
                self.active = None
                self.ctx.prompt("Comando:")
            return

        # Si no hay comando activo, intentamos iniciar uno.
        if self.active is None:
            command_class = self.factories.get(text.upper())

            if command_class:
                self.active = command_class()
                self.active.start(self.ctx)
            else:
                self.ctx.write(f"Comando no reconocido: {text}")
                self.ctx.write("Comandos disponibles: " + ", ".join(self.get_available_command_names()))
                self.ctx.prompt("Comando:")

            return

        # Si hay comando activo, le pasamos la entrada.
        result = self.active.handle_input(self.ctx, text)

        if result == CommandResult.FINISHED:
            self.active = None
            self.ctx.prompt("Comando:")

    def is_waiting_for_point(self) -> bool:
        if self.active is None:
            return False

        if hasattr(self.active, "expects_point"):
            return bool(self.active.expects_point())

        return False

    def get_point_base(self):
        if self.active is None:
            return None

        if hasattr(self.active, "get_point_base"):
            return self.active.get_point_base()

        return None

    def send_point(self, p: Point, echo: bool = False):
        if self.active is None:
            return

        text = f"{p.x:.6f};{p.y:.6f}"

        self.process_input(text, echo=echo)

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

# ============================================================
# Aplicación principal
# ============================================================

class CadApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Editor con ventana de comandos")
        root.geometry("900x600")
        root.protocol("WM_DELETE_WINDOW", self._close_window)

        # Modelo simple
        # self.lines = []
        # self.polylines = []
        # self.circles = []
        # self.arcs = []
        self.entities = []
        self.next_entity_id = 1
        self.item_to_entity = {}
        self.current_file = None

        self.preview_line = None

        self.select_press_point = None
        self.select_rect_item = None
        self.select_rect_mode = None
        self.select_dragging = False
        self.drag_threshold = 5

        self.margin = 20

        self.snap_modes = {
            "GRID",
            "ENDPOINT",
            "MIDPOINT",
        }

        self.grid_size = 10.0
        self.snap_tolerance_pixels = 8

        self.show_grid = True
        
        self.grips = []
        self.grip_size = 8
        self.grip_dragging = False
        self.active_grip = None

        # Canvas
        self.canvas = tk.Canvas(
            root,
            bg="#000000",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        # self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<ButtonPress-1>", self._on_select_press)
        self.canvas.bind("<B1-Motion>", self._on_select_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_select_release)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

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

    def _handle_point_click(self, event):
        raw_p = self.canvas_to_world(event.x, event.y)

        base_point = self.manager.get_point_base()

        p, snap_type = self.snap_point(
            raw_p,
            base_point=base_point,
        )

        self.manager.send_point(p, echo=False)

        if hasattr(self, "console"):
            self.console.entry.focus_set()

        self._update_command_cursor()
    # end metodos auxiliares pulsacion de raton
    # métodos usado por los bins.
    def _on_canvas_right_click(self, event):
        if hasattr(self, "manager") and self.manager.active is not None:
            self.manager.process_input("", echo=False)

            if hasattr(self, "console"):
                self.console.entry.focus_set()

            self._update_command_cursor()

    def _on_select_press(self, event):
        # Si un comando está esperando punto, el clic introduce un punto.
        if self._command_waiting_for_point():
            self._handle_point_click(event)
            return
        # si no comprobamos grips.
        grip = self._get_grip_at(event.x, event.y)

        if grip is not None:
            self.grip_dragging = True
            self.active_grip = grip

            self.select_press_point = None
            self.select_dragging = False

            self._delete_selection_rect()

            return
        
        self.select_press_point = (event.x, event.y)
        self.select_dragging = False

    def _on_select_motion(self, event):
        # Si estamos arrastrando un grip, editamos la entidad.
        if self.grip_dragging and self.active_grip is not None:
            self._drag_grip(event.x, event.y)
            return
        # Si no, seguimos con selección por ventana.
        if self.select_press_point is None:
            return

        x0, y0 = self.select_press_point
        x1, y1 = event.x, event.y

        if not self.select_dragging:
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)

            if dx > self.drag_threshold or dy > self.drag_threshold:
                self.select_dragging = True
            else:
                return

        mode = "window" if x1 >= x0 else "crossing"

        self._draw_selection_rect(x0, y0, x1, y1, mode)

    def _on_select_release(self, event):
        # Si estábamos arrastrando un grip, terminamos la edición.
        if self.grip_dragging:
            self.grip_dragging = False
            self.active_grip = None

            self.redraw()

            if hasattr(self, "console"):
                self.console.entry.focus_set()

            return
        
        if self.select_press_point is None:
            return

        x0, y0 = self.select_press_point
        x1, y1 = event.x, event.y

        if self.select_dragging:
            self._delete_selection_rect()

            action = "replace"

            # Ctrl: quitar de la selección
            if event.state & 0x0004:
                action = "remove"

            # Shift: añadir a la selección
            elif event.state & 0x0001:
                action = "add"

            self._select_by_window(x0, y0, x1, y1, action)

        else:
            # Si no hubo arrastre, tratamos como clic simple.
            self._on_canvas_click(event)

        self.select_press_point = None
        self.select_dragging = False

        if hasattr(self, "console"):
            self.console.entry.focus_set()
    # end métodos usados por los bins.
    # Rectangulos de seleccion
    def _draw_selection_rect(self, x0, y0, x1, y1, mode):
        # Si el rectángulo anterior fue borrado por algún redraw,
        # volvemos a crearlo.
        if (
            self.select_rect_item is not None
            and self.canvas.type(self.select_rect_item) is None
        ):
            self.select_rect_item = None
            self.select_rect_mode = None

        if (
            self.select_rect_item is None
            or self.select_rect_mode != mode
        ):
            self._delete_selection_rect()

            if mode == "window":
                # Ventana normal: izquierda -> derecha
                self.select_rect_item = self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline="#4da6ff",
                    width=1,
                )
            else:
                # Ventana de cruce: derecha -> izquierda
                self.select_rect_item = self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline="#66ff66",
                    width=1,
                    dash=(4, 4),
                )

            self.select_rect_mode = mode

        else:
            self.canvas.coords(
                self.select_rect_item,
                x0, y0, x1, y1,
            )

    def _delete_selection_rect(self):
        if self.select_rect_item is not None:
            self.canvas.delete(self.select_rect_item)

        self.select_rect_item = None
        self.select_rect_mode = None
    # end rectangulos de seleccion
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

        for item_id, entity_id in self.item_to_entity.items():
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

    def _ellipse_points(self, entity, samples: int = 64):
        """Genera una lista de puntos que representan la elipse."""
        center = entity.data["center"]
        rx = float(entity.data["radius_x"])
        ry = float(entity.data["radius_y"])
        rot = math.radians(entity.data.get("rotation", 0.0))

        cos_r = math.cos(rot)
        sin_r = math.sin(rot)

        points = []

        for i in range(samples):
            t = 2.0 * math.pi * i / samples

            x = rx * math.cos(t)
            y = ry * math.sin(t)

            xr = center.x + x * cos_r - y * sin_r
            yr = center.y + x * sin_r + y * cos_r

            points.append(Point(xr, yr))

        return points

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
    def show_preview_line(self, start: Point, end: Point):
        self.preview_line = (start, end)
        self.redraw()

    def clear_preview(self):
        self.preview_line = None
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
        self.item_to_entity = {}

        if hasattr(self, "preview_line"):
            self.preview_line = None

        self.redraw()

        self.root.title("Editor - Nuevo proyecto")

    # --------------------------------------------------------
    # Dibujo
    # --------------------------------------------------------

    def world_to_canvas(self, p: Point):
        """
        Convierte coordenadas del mundo a coordenadas del canvas.

        Aquí estoy poniendo el origen abajo a la izquierda,
        con el eje Y apuntando hacia arriba.
        """
        h = self.canvas.winfo_height()

        if h <= 1:
            h = 400

        # margin = 20

        x = p.x + self.margin
        y = h - self.margin - p.y

        return x, y

    def canvas_to_world(self, x: float, y: float) -> Point:
        h = self.canvas.winfo_height()

        if h <= 1:
            h = 400

        return Point(x - self.margin, h - self.margin - y)

    def redraw(self):
        self.canvas.delete("all")
        self.item_to_entity = {}
        # dibujar malla de fondo
        self._draw_grid()

        normal_colors = {
            "line": "white",
            "polyline": "white",
            "circle": "cyan",
            "arc": "orange",
            "polygon": "magenta",
            "ellipse": "#ff99ff",
        }

        for entity in self.entities:
            if entity.selected:
                color = "yellow"
            else:
                color = normal_colors.get(entity.kind, "white")

            tag = f"entity_{entity.id}"

            # ----------------------------------------------------
            # Línea
            # ----------------------------------------------------
            if entity.kind == "line":
                start = entity.data["start"]
                end = entity.data["end"]

                x1, y1 = self.world_to_canvas(start)
                x2, y2 = self.world_to_canvas(end)

                item = self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=2,
                    tags=tag,
                )

                self.item_to_entity[item] = entity.id

            # ----------------------------------------------------
            # Polilínea
            # ----------------------------------------------------
            elif entity.kind == "polyline":
                coords = []

                for p in entity.data["points"]:
                    coords.extend(self.world_to_canvas(p))

                if len(coords) >= 4:
                    item = self.canvas.create_line(
                        *coords,
                        fill=color,
                        width=2,
                        tags=tag,
                    )

                    self.item_to_entity[item] = entity.id

            # ----------------------------------------------------
            # Círculo
            # ----------------------------------------------------
            elif entity.kind == "circle":
                center = entity.data["center"]
                radius = entity.data["radius"]

                cx, cy = self.world_to_canvas(center)

                item = self.canvas.create_oval(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    outline=color,
                    width=2,
                    tags=tag,
                )

                self.item_to_entity[item] = entity.id

            # ----------------------------------------------------
            # Arco
            # ----------------------------------------------------
            elif entity.kind == "arc":
                center = entity.data["center"]
                radius = entity.data["radius"]
                start_angle = entity.data["start_angle"]
                extent = entity.data["extent"]

                cx, cy = self.world_to_canvas(center)

                item = self.canvas.create_arc(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    start=start_angle,
                    extent=extent,
                    style="arc",
                    outline=color,
                    width=2,
                    tags=tag,
                )

                self.item_to_entity[item] = entity.id

            # ----------------------------------------------------
            # Polígono
            # ----------------------------------------------------
            elif entity.kind == "polygon":
                points = entity.data["points"]

                if len(points) >= 3:
                    coords = []

                    for p in points:
                        coords.extend(self.world_to_canvas(p))

                    coords.extend(self.world_to_canvas(points[0]))

                    item = self.canvas.create_line(
                        *coords,
                        fill=color,
                        width=2,
                        tags=tag,
                    )

                    self.item_to_entity[item] = entity.id

            # ----------------------------------------------------
            # Elipse
            # ----------------------------------------------------
            elif entity.kind == "ellipse":
                points = self._ellipse_points(entity)

                coords = []

                for p in points:
                    coords.extend(self.world_to_canvas(p))

                if len(coords) >= 6:
                    item = self.canvas.create_polygon(
                        *coords,
                        outline=color,
                        fill="",
                        smooth=True,
                        width=2,
                        tags=tag,
                    )

                    self.item_to_entity[item] = entity.id

        # ----------------------------------------------------
        # Vista previa opcional
        # ----------------------------------------------------
        if getattr(self, "preview_line", None) is not None:
            start, end = self.preview_line

            x1, y1 = self.world_to_canvas(start)
            x2, y2 = self.world_to_canvas(end)

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill="yellow",
                width=1,
                dash=(4, 4),
            )
        # Grips
        self._draw_grips()

    def _draw_grid(self):
        """Método para dibujar la malla de fondo en el canvas."""
        if not self.show_grid:
            return

        if self.grid_size <= 0:
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w <= 1 or h <= 1:
            return

        top_left = self.canvas_to_world(0, 0)
        bottom_right = self.canvas_to_world(w, h)

        min_x = min(top_left.x, bottom_right.x)
        max_x = max(top_left.x, bottom_right.x)

        min_y = min(top_left.y, bottom_right.y)
        max_y = max(top_left.y, bottom_right.y)

        g = self.grid_size

        # Protección contra mallas demasiado densas
        if (max_x - min_x) / g > 1000:
            return

        if (max_y - min_y) / g > 1000:
            return

        x = math.floor(min_x / g) * g

        while x <= max_x:
            cx = x + self.margin

            self.canvas.create_line(
                cx, 0, cx, h,
                fill="#222222",
            )

            x += g

        y = math.floor(min_y / g) * g

        while y <= max_y:
            _, cy = self.world_to_canvas(Point(0.0, y))

            self.canvas.create_line(
                0, cy, w, cy,
                fill="#222222",
            )

            y += g

    # grips

    def toggle_show_grid(self):
        self.show_grid = not self.show_grid
        self.redraw()
        return self.show_grid

    def _draw_grips(self):
        self.grips = []

        # Mientras se arrastra un grip, no dibujamos todos los grips
        # para evitar parpadeos y conflictos.
        if self.grip_dragging:
            return

        selected = self.get_selected_entities()

        for entity in selected:

            # ----------------------------------------------------
            # Línea: grip en inicio y fin
            # ----------------------------------------------------
            if entity.kind == "line":
                start = entity.data["start"]
                end = entity.data["end"]

                x1, y1 = self.world_to_canvas(start)
                x2, y2 = self.world_to_canvas(end)

                self._create_grip(x1, y1, entity.id, "start")
                self._create_grip(x2, y2, entity.id, "end")

            # ----------------------------------------------------
            # Polilínea / polígono: grip en cada vértice
            # ----------------------------------------------------
            elif entity.kind in ("polyline", "polygon"):
                points = entity.data["points"]

                for index, point in enumerate(points):
                    x, y = self.world_to_canvas(point)
                    self._create_grip(
                        x,
                        y,
                        entity.id,
                        "vertex",
                        index=index,
                    )

            # ----------------------------------------------------
            # Círculo: grip de centro y grip de radio
            # ----------------------------------------------------
            elif entity.kind == "circle":
                center = entity.data["center"]
                radius = entity.data["radius"]

                cx, cy = self.world_to_canvas(center)

                self._create_grip(cx, cy, entity.id, "center")

                radius_point = Point(center.x + radius, center.y)
                rx, ry = self.world_to_canvas(radius_point)

                self._create_grip(rx, ry, entity.id, "radius")

            # ----------------------------------------------------
            # Arco: grip de centro, inicio y fin
            # ----------------------------------------------------
            elif entity.kind == "arc":
                center = entity.data["center"]
                radius = entity.data["radius"]
                start_angle = entity.data["start_angle"]
                extent = entity.data["extent"]

                cx, cy = self.world_to_canvas(center)

                self._create_grip(cx, cy, entity.id, "center")

                start_rad = math.radians(start_angle)
                end_rad = math.radians(start_angle + extent)

                start_point = Point(
                    center.x + radius * math.cos(start_rad),
                    center.y + radius * math.sin(start_rad),
                )

                end_point = Point(
                    center.x + radius * math.cos(end_rad),
                    center.y + radius * math.sin(end_rad),
                )

                sx, sy = self.world_to_canvas(start_point)
                ex, ey = self.world_to_canvas(end_point)

                self._create_grip(sx, sy, entity.id, "arc_start")
                self._create_grip(ex, ey, entity.id, "arc_end")

            #----------------------------------------------------
            # Elipse: grip de centro y grip de radio
            #----------------------------------------------------
            elif entity.kind == "ellipse":
                center = entity.data["center"]
                rx = float(entity.data["radius_x"])
                ry = float(entity.data["radius_y"])
                rot = math.radians(entity.data.get("rotation", 0.0))

                cx, cy = self.world_to_canvas(center)

                self._create_grip(cx, cy, entity.id, "center")

                x_point = Point(
                    center.x + rx * math.cos(rot),
                    center.y + ry * math.sin(rot),
                )

                y_rot = rot + math.pi / 2.0

                y_point = Point(
                    center.x + ry * math.cos(y_rot),
                    center.y + ry * math.sin(y_rot),
                )

                x_canvas = self.world_to_canvas(x_point)
                y_canvas = self.world_to_canvas(y_point)

                self._create_grip(
                    x_canvas[0],
                    x_canvas[1],
                    entity.id,
                    "ellipse_x",
                )

                self._create_grip(
                    y_canvas[0],
                    y_canvas[1],
                    entity.id,
                    "ellipse_y",
                )

    def _create_grip(self, x: float, y: float, entity_id: int, grip_type: str, index=None):
        s = self.grip_size

        item = self.canvas.create_rectangle(
            x - s / 2,
            y - s / 2,
            x + s / 2,
            y + s / 2,
            fill="#4da6ff",
            outline="#003366",
        )

        self.grips.append(
            {
                "item": item,
                "entity_id": entity_id,
                "type": grip_type,
                "index": index,
                "x": x,
                "y": y,
            }
        )

    def _get_grip_at(self, x: float, y: float):
        tolerance = self.grip_size + 4
        best_grip = None
        best_distance = tolerance

        for grip in self.grips:
            distance = math.hypot(
                x - grip["x"],
                y - grip["y"],
            )

            if distance < best_distance:
                best_grip = grip
                best_distance = distance

        return best_grip

    def _drag_grip(self, x: float, y: float):
        """modificamos la entidad asociada al grip activo según la posición del mouse"""
        grip = self.active_grip

        if grip is None:
            return

        entity = self.get_entity_by_id(grip["entity_id"])

        if entity is None:
            self.grip_dragging = False
            self.active_grip = None
            return

        raw_p = self.canvas_to_world(x, y)

        base_point = self._get_grip_base(entity, grip)

        p, snap_type = self.snap_point(
            raw_p,
            base_point=base_point,
            ignore_entity_id=entity.id,
        )

        # ----------------------------------------------------
        # Línea
        # ----------------------------------------------------
        if entity.kind == "line":
            if grip["type"] == "start":
                entity.data["start"] = p

            elif grip["type"] == "end":
                entity.data["end"] = p

        # ----------------------------------------------------
        # Polilínea / polígono
        # ----------------------------------------------------
        elif entity.kind in ("polyline", "polygon"):
            index = grip.get("index")

            if index is not None:
                points = entity.data["points"]

                if 0 <= index < len(points):
                    points[index] = p

        # ----------------------------------------------------
        # Círculo
        # ----------------------------------------------------
        elif entity.kind == "circle":
            if grip["type"] == "center":
                entity.data["center"] = p

            elif grip["type"] == "radius":
                center = entity.data["center"]

                radius = math.hypot(
                    p.x - center.x,
                    p.y - center.y,
                )

                if radius > 0.01:
                    entity.data["radius"] = radius

        # ----------------------------------------------------
        # Arco
        # ----------------------------------------------------
        elif entity.kind == "arc":
            if grip["type"] == "center":
                entity.data["center"] = p

            elif grip["type"] in ("arc_start", "arc_end"):
                center = entity.data["center"]

                dx = p.x - center.x
                dy = p.y - center.y

                distance = math.hypot(dx, dy)

                if distance < 1e-9:
                    return

                angle = math.degrees(
                    math.atan2(dy, dx)
                )

                start_angle = entity.data["start_angle"]
                extent = entity.data["extent"]

                if grip["type"] == "arc_start":
                    old_end = (start_angle + extent) % 360.0

                    new_start = angle
                    new_extent = (old_end - new_start) % 360.0

                    if new_extent < 0.01:
                        new_extent = 0.01

                    entity.data["start_angle"] = new_start
                    entity.data["extent"] = new_extent

                elif grip["type"] == "arc_end":
                    new_extent = (angle - start_angle) % 360.0

                    if new_extent < 0.01:
                        new_extent = 0.01

                    entity.data["extent"] = new_extent

        # ----------------------------------------------------
        # Elipse
        # ----------------------------------------------------
        elif entity.kind == "ellipse":
            center = entity.data["center"]

            if grip["type"] == "center":
                entity.data["center"] = p

            elif grip["type"] == "ellipse_x":
                dx = p.x - center.x
                dy = p.y - center.y

                distance = math.hypot(dx, dy)

                if distance > 1e-9:
                    entity.data["radius_x"] = distance
                    entity.data["rotation"] = (
                        math.degrees(math.atan2(dy, dx)) % 360.0
                    )

            elif grip["type"] == "ellipse_y":
                dx = p.x - center.x
                dy = p.y - center.y

                distance = math.hypot(dx, dy)

                if distance > 1e-9:
                    entity.data["radius_y"] = distance

                    entity.data["rotation"] = (
                        math.degrees(math.atan2(dy, dx)) - 90.0
                    ) % 360.0        

        self.redraw()

    def _get_grip_base(self, entity, grip):
        """Este método devuelve un punto base para el modo ortogonal.
           Por ejemplo, si estás arrastrando el extremo final de una línea, 
           el punto base puede ser el inicio de la línea."""
        if entity.kind == "line":
            if grip["type"] == "start":
                return entity.data["end"]

            if grip["type"] == "end":
                return entity.data["start"]

        elif entity.kind in ("polyline", "polygon"):
            index = grip.get("index")
            points = entity.data["points"]

            if index is None:
                return None

            if not points:
                return None

            if entity.kind == "polygon":
                if index == 0 and len(points) > 1:
                    return points[-1]

            if index > 0:
                return points[index - 1]

            if len(points) > 1:
                return points[1]

            return None

        elif entity.kind == "circle":
            if grip["type"] == "radius":
                return entity.data["center"]

        elif entity.kind == "arc":
            if grip["type"] in ("arc_start", "arc_end"):
                return entity.data["center"]

        elif entity.kind == "ellipse":
            if grip["type"] in ("ellipse_x", "ellipse_y"):
                return entity.data["center"]

        return None

    # end grips
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
    # metodos para calcular snaps
    def snap_point(self, p: Point, base_point: Point = None, ignore_entity_id=None):
        """
        Devuelve:
            Point, snap_type

        snap_type puede ser:
            "POINT"
            "ENDPOINT"
            "MIDPOINT"
            "INTERSECTION"
            "ORTHO"
            "GRID"
            None
        """
        if not self.snap_modes:
            return p, None

        candidates = []

        if "POINT" in self.snap_modes:
            candidates.extend(
                self._snap_points_near(p, ignore_entity_id)
            )

        if "ENDPOINT" in self.snap_modes:
            candidates.extend(
                self._snap_endpoints_near(p, ignore_entity_id)
            )

        if "MIDPOINT" in self.snap_modes:
            candidates.extend(
                self._snap_midpoints_near(p, ignore_entity_id)
            )

        if "INTERSECTION" in self.snap_modes:
            candidates.extend(
                self._snap_intersections_near(p, ignore_entity_id)
            )

        best = self._nearest_snap_candidate(candidates, p)

        if best is not None:
            return best

        if "ORTHO" in self.snap_modes and base_point is not None:
            return self._apply_ortho(p, base_point), "ORTHO"

        if "GRID" in self.snap_modes:
            return self._snap_to_grid(p), "GRID"

        return p, None

    def _add_snap_candidate(self, candidates, point: Point, target: Point, tolerance: float, kind: str):
        distance = math.hypot(
            point.x - target.x,
            point.y - target.y,
        )

        if distance <= tolerance:
            candidates.append((point, kind))

    def _nearest_snap_candidate(self, candidates, target: Point):
        tolerance = self.snap_tolerance_pixels

        best_point = None
        best_kind = None
        best_distance = tolerance

        for point, kind in candidates:
            distance = math.hypot(
                point.x - target.x,
                point.y - target.y,
            )

            if distance <= best_distance:
                best_point = point
                best_kind = kind
                best_distance = distance

        if best_point is None:
            return None

        # Devolvemos una copia para no compartir objetos Point
        return Point(best_point.x, best_point.y), best_kind

    def _snap_to_grid(self, p: Point) -> Point:
        g = self.grid_size

        if g <= 0:
            return Point(p.x, p.y)

        x = math.floor(p.x / g + 0.5) * g
        y = math.floor(p.y / g + 0.5) * g

        return Point(x, y)

    def _apply_ortho(self, p: Point, base_point: Point) -> Point:
        dx = p.x - base_point.x
        dy = p.y - base_point.y

        if abs(dx) >= abs(dy):
            return Point(p.x, base_point.y)

        return Point(base_point.x, p.y)
    # end metodos para calcular snaps
    # snap a cualquier punto de las entidades (vértices, centro de círculo, centro de arco)
    def _snap_points_near(self, p: Point, ignore_entity_id=None):
        """snap a cualquier punto de las entidades (vértices, centro de círculo, centro de arco)"""
        tolerance = self.snap_tolerance_pixels
        candidates = []

        for entity in self.entities:
            if entity.id == ignore_entity_id:
                continue

            if entity.kind == "line":
                start = entity.data["start"]
                end = entity.data["end"]

                self._add_snap_candidate(candidates, start, p, tolerance, "POINT")
                self._add_snap_candidate(candidates, end, p, tolerance, "POINT")

            elif entity.kind in ("polyline", "polygon"):
                for point in entity.data["points"]:
                    self._add_snap_candidate(candidates, point, p, tolerance, "POINT")

            elif entity.kind == "circle":
                center = entity.data["center"]
                self._add_snap_candidate(candidates, center, p, tolerance, "POINT")

            elif entity.kind == "arc":
                center = entity.data["center"]
                start_point, end_point = self._arc_endpoints(entity)

                self._add_snap_candidate(candidates, center, p, tolerance, "POINT")
                self._add_snap_candidate(candidates, start_point, p, tolerance, "POINT")
                self._add_snap_candidate(candidates, end_point, p, tolerance, "POINT")

            elif entity.kind == "ellipse":
                center = entity.data["center"]

                self._add_snap_candidate(
                    candidates,
                    center,
                    p,
                    tolerance,
                    "POINT",
                )

                for point in self._ellipse_axis_points(entity):
                    self._add_snap_candidate(
                        candidates,
                        point,
                        p,
                        tolerance,
                        "POINT",
                    )

        return candidates

    def _snap_endpoints_near(self, p: Point, ignore_entity_id=None):
        """snap a los puntos finales de las entidades (inicio y fin de línea, vértices de polilínea/polígono, inicio y fin de arco)"""
        tolerance = self.snap_tolerance_pixels
        candidates = []

        for entity in self.entities:
            if entity.id == ignore_entity_id:
                continue

            if entity.kind == "line":
                start = entity.data["start"]
                end = entity.data["end"]

                self._add_snap_candidate(candidates, start, p, tolerance, "ENDPOINT")
                self._add_snap_candidate(candidates, end, p, tolerance, "ENDPOINT")

            elif entity.kind in ("polyline", "polygon"):
                for point in entity.data["points"]:
                    self._add_snap_candidate(candidates, point, p, tolerance, "ENDPOINT")

            elif entity.kind == "arc":
                start_point, end_point = self._arc_endpoints(entity)

                self._add_snap_candidate(candidates, start_point, p, tolerance, "ENDPOINT")
                self._add_snap_candidate(candidates, end_point, p, tolerance, "ENDPOINT")

            elif entity.kind == "ellipse":
                for point in self._ellipse_axis_points(entity):
                    self._add_snap_candidate(
                        candidates,
                        point,
                        p,
                        tolerance,
                        "ENDPOINT",
                    )

        return candidates

    def _snap_midpoints_near(self, p: Point, ignore_entity_id=None):
        """snap a los puntos medios de las entidades (líneas, segmentos de polilínea/polígono, arcos)"""
        tolerance = self.snap_tolerance_pixels
        candidates = []

        for entity in self.entities:
            if entity.id == ignore_entity_id:
                continue

            # Punto medio de línea
            if entity.kind == "line":
                start = entity.data["start"]
                end = entity.data["end"]

                midpoint = Point(
                    (start.x + end.x) / 2.0,
                    (start.y + end.y) / 2.0,
                )

                self._add_snap_candidate(candidates, midpoint, p, tolerance, "MIDPOINT")

            # Puntos medios de segmentos de polilínea / polígono
            elif entity.kind in ("polyline", "polygon"):
                points = entity.data["points"]

                if len(points) >= 2:
                    if entity.kind == "polyline":
                        segment_count = len(points) - 1
                    else:
                        segment_count = len(points)

                    for i in range(segment_count):
                        a = points[i]
                        b = points[(i + 1) % len(points)]

                        midpoint = Point(
                            (a.x + b.x) / 2.0,
                            (a.y + b.y) / 2.0,
                        )

                        self._add_snap_candidate(candidates, midpoint, p, tolerance, "MIDPOINT")

            # Punto medio de arco
            elif entity.kind == "arc":
                start_angle = entity.data["start_angle"]
                extent = entity.data["extent"]

                mid_angle = start_angle + extent / 2.0

                midpoint = self._arc_point_at_angle(entity, mid_angle)

                self._add_snap_candidate(candidates, midpoint, p, tolerance, "MIDPOINT")

        return candidates

    def _snap_intersections_near(self, p: Point, ignore_entity_id=None):
        """snap a las intersecciones entre entidades lineales (líneas, segmentos de polilínea/polígono)"""
        tolerance = self.snap_tolerance_pixels
        candidates = []

        segments = self._linear_segments(ignore_entity_id)

        # Filtramos segmentos cuya caja envolvente está cerca del punto
        filtered_segments = []

        for a, b in segments:
            if self._segment_bbox_contains_point(a, b, p, tolerance):
                filtered_segments.append((a, b))

        count = len(filtered_segments)

        for i in range(count):
            a, b = filtered_segments[i]

            for j in range(i + 1, count):
                c, d = filtered_segments[j]

                inter = line_line_intersection(a, b, c, d)

                if inter is None:
                    continue

                point, t, u = inter

                if -1e-9 <= t <= 1.0 + 1e-9 and -1e-9 <= u <= 1.0 + 1e-9:
                    self._add_snap_candidate(
                        candidates,
                        point,
                        p,
                        tolerance,
                        "INTERSECTION",
                    )

        return candidates

    def _linear_segments(self, ignore_entity_id=None):
        segments = []

        for entity in self.entities:
            if entity.id == ignore_entity_id:
                continue

            if entity.kind == "line":
                segments.append(
                    (
                        entity.data["start"],
                        entity.data["end"],
                    )
                )

            elif entity.kind == "polyline":
                points = entity.data["points"]

                for i in range(len(points) - 1):
                    segments.append((points[i], points[i + 1]))

            elif entity.kind == "polygon":
                points = entity.data["points"]

                if len(points) >= 2:
                    for i in range(len(points)):
                        a = points[i]
                        b = points[(i + 1) % len(points)]

                        segments.append((a, b))

        return segments

    def _segment_bbox_contains_point(self, a: Point, b: Point, p: Point, tolerance: float):
        min_x = min(a.x, b.x) - tolerance
        max_x = max(a.x, b.x) + tolerance

        min_y = min(a.y, b.y) - tolerance
        max_y = max(a.y, b.y) + tolerance

        return (
            min_x <= p.x <= max_x
            and min_y <= p.y <= max_y
        )

    def _arc_point_at_angle(self, entity, angle_deg: float) -> Point:
        center = entity.data["center"]
        radius = entity.data["radius"]

        rad = math.radians(angle_deg)

        return Point(
            center.x + radius * math.cos(rad),
            center.y + radius * math.sin(rad),
        )

    def _arc_endpoints(self, entity):
        start_angle = entity.data["start_angle"]
        extent = entity.data["extent"]

        start_point = self._arc_point_at_angle(entity, start_angle)
        end_point = self._arc_point_at_angle(entity, start_angle + extent)

        return start_point, end_point

    def _on_canvas_click(self, event):
        margin = 4

        items = self.canvas.find_overlapping(
            event.x - margin,
            event.y - margin,
            event.x + margin,
            event.y + margin,
        )
        # Recorremos de arriba hacia abajo para elegir la entidad
        # más visible bajo el cursor.
        for item in reversed(items):
            entity_id = self.item_to_entity.get(item)
            
            if entity_id is not None:
                self.toggle_selection(entity_id)

                if hasattr(self, "console"):
                    self.console.entry.focus_set()

                return

        # Si quieres que un clic en vacío limpie la selección,
        # descomenta esta línea:
        self.clear_selection()

        if hasattr(self, "console"):
            self.console.entry.focus_set()

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

    def _ellipse_axis_points(self, entity):
        """Calcula los puntos de los ejes de la elipse para dibujar grips y snaps."""
        center = entity.data["center"]
        rx = float(entity.data["radius_x"])
        ry = float(entity.data["radius_y"])
        rot = math.radians(entity.data.get("rotation", 0.0))

        cos_r = math.cos(rot)
        sin_r = math.sin(rot)

        x_pos = Point(
            center.x + rx * cos_r,
            center.y + rx * sin_r,
        )

        x_neg = Point(
            center.x - rx * cos_r,
            center.y - rx * sin_r,
        )

        y_rot = rot + math.pi / 2.0

        y_cos = math.cos(y_rot)
        y_sin = math.sin(y_rot)

        y_pos = Point(
            center.x + ry * y_cos,
            center.y + ry * y_sin,
        )

        y_neg = Point(
            center.x - ry * y_cos,
            center.y - ry * y_sin,
        )

        return [x_pos, x_neg, y_pos, y_neg]
    
# ============================================================
# Ejecución
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = CadApp(root)
    root.mainloop()