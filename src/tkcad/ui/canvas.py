import math
import tkinter as tk

from ..core import Point
from .snap_markers import SnapMarkerDrawer, SNAP_MARKER_KINDS


class CadCanvas(tk.Canvas):
    """Canvas de tkCAD: dibujo, grips, selección visual y ratón."""

    def __init__(self, root):
        super().__init__(root, bg="#000000", highlightthickness=0)
        self.app = None  # se asigna justo después de crearlo

        # Estado propio del canvas
        self.margin = 20
        self.item_to_entity = {}
        self.scale = 1.0     # zoom (1.0 = 100%)
        self.pan_x = 0.0     # desplazamiento en unidades de mundo
        self.pan_y = 0.0        

        # Estado de selección visual
        self.select_press_point = None
        self.select_rect_item = None
        self.select_rect_mode = None
        self.select_dragging = False
        self.drag_threshold = 5

        # Estado visible snap
        self.snap_drawer = SnapMarkerDrawer(self)

        # seleccionpoligono y ciclica
        self._cycle_last_pos = None
        self._cycle_candidates = []
        self._cycle_index = 0

        # historial + zoom a rect
        self.view_back = []
        self.view_forward = []
        self._last_view_key = None
        
        self.grip_manager = None
        # seguir el puntero del ratón.
        self.rubber_item = None
        self.preview_circle_item = None
        self.pan_last = None
        self.bind_all("<MouseWheel>", self._on_wheel)
        self.bind("<Button-2>", self._on_pan_press)
        self.bind("<B2-Motion>", self._on_pan_motion)
        self.bind("<ButtonRelease-2>", self._on_pan_release)
        self.bind("<Double-Button-2>", lambda e: self.zoom_extents())
        # Eventos de ratón
        self.bind("<Motion>", self._on_motion)
        # self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonPress-1>", self._on_select_press)
        self.bind("<B1-Motion>", self._on_select_motion)
        self.bind("<ButtonRelease-1>", self._on_select_release)
        self.bind("<Button-3>", self._on_canvas_right_click)

    
    def world_to_canvas(self, p: Point):
        """
        Convierte coordenadas del mundo a coordenadas del canvas.

        Aquí estoy poniendo el origen abajo a la izquierda,
        con el eje Y apuntando hacia arriba.
        """
        h = self.winfo_height()
        x = (p.x - self.pan_x) * self.scale + self.margin
        y = h - ((p.y - self.pan_y) * self.scale + self.margin)
        return x, y

    def canvas_to_world(self, x: float, y: float) -> Point:
        """Convierte píxeles del canvas a coordenadas de mundo."""
        h = self.winfo_height()
        wx = (x - self.margin) / self.scale + self.pan_x
        wy = ((h - y) - self.margin) / self.scale + self.pan_y
        return Point(wx, wy)

    def world_to_canvas_length(self, length: float) -> float:
        """Convierte una longitud de mundo a píxeles en pantalla.

        La usamos para radios de vistas previas, tamaños de grips,
        tolerancias de snap... cualquier cosa que deba medirse
        en pantalla y no en el mundo.
        """
        return length * self.scale

    def redraw(self):
        self.delete("all")
        self.snap_drawer.items = []
        self.rubber_item = None
        self.preview_circle_item = None
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
            "text": "#ffcc66",
        }

        for entity in self.app.visible_entities():          # ← solo visibles
            layer = self.app.get_layer(entity.layer)
            if entity.selected:
                color = "yellow"
            elif layer is not None and layer.color is not None:
                color = layer.color                          # ← color de la capa
            else:
                color = normal_colors.get(entity.kind, "white")  # ← color por tipo

            tag = f"entity_{entity.id}"

            # ----------------------------------------------------
            # Línea
            # ----------------------------------------------------
            if entity.kind == "line":
                start = entity.data["start"]
                end = entity.data["end"]

                x1, y1 = self.world_to_canvas(start)
                x2, y2 = self.world_to_canvas(end)

                item = self.create_line(
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
                    item = self.create_line(
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
                r_px = self.world_to_canvas_length(radius)   # ← radio escalado

                item = self.create_oval(
                    cx - r_px,
                    cy - r_px,
                    cx + r_px,
                    cy + r_px,
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
                r_px = self.world_to_canvas_length(radius)   # ← radio escalado

                item = self.create_arc(
                    cx - r_px,
                    cy - r_px,
                    cx + r_px,
                    cy + r_px,
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

                    item = self.create_line(
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
                    item = self.create_polygon(
                        *coords,
                        outline=color,
                        fill="",
                        smooth=True,
                        width=2,
                        tags=tag,
                    )

                    self.item_to_entity[item] = entity.id

            # ----------------------------------------------------
            # Texto
            # ----------------------------------------------------
            elif entity.kind == "text":
                pos = entity.data["position"]
                height = entity.data["height"]
                content = entity.data["content"]

                x, y = self.world_to_canvas(pos)
                font_px = max(int(self.world_to_canvas_length(height)), 4)

                item = self.create_text(
                    x, y,
                    text=content,
                    fill=color,
                    anchor="center",
                    font=("TkDefaultFont", -font_px),   # tamaño en píxeles → escala con zoom
                )

                self.item_to_entity[item] = entity.id

        # ----------------------------------------------------
        # Vista previa opcional
        # ----------------------------------------------------
        if getattr(self, "preview_line", None) is not None:
            start, end = self.app.preview_line

            x1, y1 = self.world_to_canvas(start)
            x2, y2 = self.world_to_canvas(end)

            self.create_line(
                x1, y1, x2, y2,
                fill="yellow",
                width=1,
                dash=(4, 4),
            )

        # Vista previa de polilínea en construcción
        preview_points = getattr(self.app, "preview_points", None)
        if preview_points and len(preview_points) >= 2:
            coords = []
            for p in preview_points:
                coords.extend(self.world_to_canvas(p))
            self.create_line(
                *coords,
                fill="yellow",
                width=1,
                dash=(4, 4),
            )
        
        # Grips
        self.grip_manager.draw_grips()

    def _draw_grid(self):
        """Método para dibujar la malla de fondo en el canvas."""
        if not self.app.show_grid:
            return

        if self.app.grid_size <= 0:
            return

        w = self.winfo_width()
        h = self.winfo_height()

        if w <= 1 or h <= 1:
            return

        top_left = self.canvas_to_world(0, 0)
        bottom_right = self.canvas_to_world(w, h)

        min_x = min(top_left.x, bottom_right.x)
        max_x = max(top_left.x, bottom_right.x)

        min_y = min(top_left.y, bottom_right.y)
        max_y = max(top_left.y, bottom_right.y)

        # Paso adaptativo al zoom: al menos 12 píxeles entre líneas
        step = self.app.grid_size
        while step * self.scale < 12:
            step *= 2

        # g = self.app.grid_size

        # Protección contra mallas demasiado densas
        if (max_x - min_x) / step > 1000:
            return

        if (max_y - min_y) / step > 1000:
            return

        x = math.floor(min_x / step) * step

        while x <= max_x:
            cx = x + self.margin

            self.create_line(
                cx, 0, cx, h,
                fill="#222222",
            )

            x += step

        y = math.floor(min_y / step) * step

        while y <= max_y:
            _, cy = self.world_to_canvas(Point(0.0, y))

            self.create_line(
                0, cy, w, cy,
                fill="#222222",
            )

            y += step

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

    # Rectangulos de seleccion
    def _draw_selection_rect(self, x0, y0, x1, y1, mode):
        # Si el rectángulo anterior fue borrado por algún redraw,
        # volvemos a crearlo.
        if (
            self.select_rect_item is not None
            and self.type(self.select_rect_item) is None
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
                self.select_rect_item = self.create_rectangle(
                    x0, y0, x1, y1,
                    outline="#4da6ff",
                    width=1,
                )
            else:
                # Ventana de cruce: derecha -> izquierda
                self.select_rect_item = self.create_rectangle(
                    x0, y0, x1, y1,
                    outline="#66ff66",
                    width=1,
                    dash=(4, 4),
                )

            self.select_rect_mode = mode

        else:
            self.coords(
                self.select_rect_item,
                x0, y0, x1, y1,
            )

    def _select_by_window(self, x0, y0, x1, y1, action):
        """
        Selecciona entidades por ventana o cruce.
        
        Args:
            x0, y0: Esquina superior-izquierda del rectángulo (canvas coords)
            x1, y1: Esquina inferior-derecha del rectángulo (canvas coords)
            action: "replace", "add", "remove"
        """
        # Convertir coordenadas de canvas a mundo
        p0 = self.canvas_to_world(x0, y0)
        p1 = self.canvas_to_world(x1, y1)
        
        # Asegurar que p0 sea el mínimo y p1 el máximo
        min_x = min(p0.x, p1.x)
        max_x = max(p0.x, p1.x)
        min_y = min(p0.y, p1.y)
        max_y = max(p0.y, p1.y)
        
        # Determinar el modo: izquierda→derecha = window, derecha→izquierda = crossing
        mode = "window" if x1 >= x0 else "crossing"
        
        # Delegar al modelo
        self.app.select_by_rectangle(min_x, min_y, max_x, max_y, mode, action)
        self.app.redraw()

    def _delete_selection_rect(self):
        if self.select_rect_item is not None:
            self.delete(self.select_rect_item)

        self.select_rect_item = None
        self.select_rect_mode = None
    # end rectangulos de seleccion

    # métodos usado por los bins.
    def _on_canvas_right_click(self, event):
        if hasattr(self, "manager") and self.app.manager.active is not None:
            self.app.manager.process_input("", echo=False)

            if hasattr(self, "console"):
                self.app.console.entry.focus_set()

            self.app._update_command_cursor()

    
    def _on_select_press(self, event):
        # NUEVO: Ctrl+clic sobre un grip de vértice elimina ese vértice
        if event.state & 0x0004:   # Ctrl presionado
            grip = self.grip_manager.get_grip_at(event.x, event.y)
            if grip is not None and grip["type"] == "vertex":
                entity = self.app.get_entity_by_id(grip["entity_id"])
                if entity is not None and entity.kind in ("polyline", "polygon"):
                    self.app.mark_action()
                    ok, msg = self.app.remove_vertex(grip["entity_id"], grip["index"])
                    self.app.commit_action()
                    self.app.write(msg)
                    self.app.redraw()
                    if hasattr(self, "console"):
                        self.app.console.entry.focus_set()
                    return
        
        # Si un comando está esperando punto, el clic introduce un punto.
        if self.app._command_waiting_for_point():
            self._handle_point_click(event)
            return

        # ← NUEVO: elegir entidad con clic
        if self.app._command_waiting_for_entity():
            self._handle_entity_pick(event)
            return
        
        # si no comprobamos grips.
        grip = self.grip_manager.get_grip_at(event.x, event.y)

        if grip is not None:
            self.app.mark_action()
            self.grip_manager.grip_dragging = True
            self.grip_manager.active_grip = grip

            self.select_press_point = None
            self.select_dragging = False

            self._delete_selection_rect()

            return
        
        self.select_press_point = (event.x, event.y)
        self.select_dragging = False

    def _on_select_motion(self, event):
        # Si estamos arrastrando un grip, editamos la entidad.
        if self.grip_manager.grip_dragging and self.grip_manager.active_grip is not None:
            self.grip_manager.drag_grip(event.x, event.y)
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
        if self.grip_manager.grip_dragging:
            # NUEVO: notificar que se soltó un grip (limpia flags internos)
            self.grip_manager.on_grip_released()

            self.grip_manager.grip_dragging = False
            self.grip_manager.active_grip = None
            self.app.commit_action()

            self.app.redraw()

            if hasattr(self, "console"):
                self.app.console.entry.focus_set()

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
            self.app.console.entry.focus_set()
    
    
    def _on_canvas_click(self, event):
        margin = 4
        items = self.find_overlapping(
            event.x - margin, event.y - margin,
            event.x + margin, event.y + margin,
        )

        # Candidatos de arriba hacia abajo, sin duplicados
        candidates = []
        for item in reversed(items):
            eid = self.item_to_entity.get(item)
            if eid is not None and eid not in candidates:
                candidates.append(eid)

        if not candidates:
            self.app.clear_selection()
            self._reset_cycle()
            return

        same_spot = (
            self._cycle_last_pos is not None
            and abs(event.x - self._cycle_last_pos[0]) <= self.drag_threshold
            and abs(event.y - self._cycle_last_pos[1]) <= self.drag_threshold
        )

        if same_spot and candidates == self._cycle_candidates and len(candidates) > 1:
            # Ciclar al siguiente
            self._cycle_index = (self._cycle_index + 1) % len(candidates)
            self.app.clear_selection()
            self.app.toggle_selection(candidates[self._cycle_index])
        else:
            # Primer clic: conmuta el de arriba
            self._cycle_index = 0
            self.app.toggle_selection(candidates[0])

        self._cycle_last_pos = (event.x, event.y)
        self._cycle_candidates = candidates

        if hasattr(self, "console"):
            self.app.console.entry.focus_set()

    def _reset_cycle(self):
        self._cycle_last_pos = None
        self._cycle_candidates = []
        self._cycle_index = 0

    def _on_motion(self, event):
        self.app.on_cursor_move(self.canvas_to_world(event.x, event.y))
        self._update_snap_marker(event)
        # 1) Vista previa del hilo elástico (LINEA / POLILINEA)
        pts = getattr(self.app, "preview_points", None)
        if pts:
            last = pts[-1]
            raw = self.canvas_to_world(event.x, event.y)
            p, _ = self.app.snap_point(raw, base_point=last)
            x1, y1 = self.world_to_canvas(last)
            x2, y2 = self.world_to_canvas(p)
            if self.rubber_item is None or self.type(self.rubber_item) is None:
                self.rubber_item = self.create_line(
                    x1, y1, x2, y2,
                    fill="yellow", width=1, dash=(4, 4),
                )
            else:
                self.coords(self.rubber_item, x1, y1, x2, y2)
            # Si hay hilo, limpiamos la vista previa de círculo
            self._update_preview_circle(None)
            return

        # 2) No hay hilo → limpiamos el hilo si existía
        if self.rubber_item is not None and self.type(self.rubber_item) is not None:
            self.delete(self.rubber_item)
        self.rubber_item = None

        # 3) Vista previa de círculo (CIRCULO)
        cmd = self.app.manager.active
        if cmd is not None and hasattr(cmd, "preview_circle"):
            raw = self.canvas_to_world(event.x, event.y)
            data = cmd.preview_circle(self.app, raw)
            self._update_preview_circle(data)
        else:
            self._update_preview_circle(None)
       
    # end métodos usados por los bins.

    def _handle_point_click(self, event):
        raw_p = self.canvas_to_world(event.x, event.y)

        base_point = self.app.manager.get_point_base()

        p, snap_type = self.app.snap_point(
            raw_p,
            base_point=base_point,
        )

        self.app.manager.send_point(p, echo=False)
        self.snap_drawer.clear()

        if hasattr(self, "console"):
            self.app.console.entry.focus_set()

        self.app._update_command_cursor()
    
    # end metodos auxiliares pulsacion de raton
    
    def _update_preview_circle(self, data):
        """Dibuja, actualiza o borra el óvalo de vista previa."""
        if data is None:
            if (
                self.preview_circle_item is not None
                and self.type(self.preview_circle_item) is not None
            ):
                self.delete(self.preview_circle_item)
            self.preview_circle_item = None
            return

        center, radius = data
        cx, cy = self.world_to_canvas(center)
        r_px = self.world_to_canvas_length(radius)   # ← escalado
        box = (cx - r_px, cy - r_px, cx + r_px, cy + r_px)

        if (
            self.preview_circle_item is None
            or self.type(self.preview_circle_item) is None
        ):
            self.preview_circle_item = self.create_oval(
                *box, outline="yellow", dash=(4, 4),
            )
        else:
            self.coords(self.preview_circle_item, *box)

    # --------------------------------------------------------
    # Zoom y pan
    # --------------------------------------------------------
    def zoom_at(self, cx, cy, factor):
        world = self.canvas_to_world(cx, cy)
        new_scale = min(max(self.scale * factor, 0.02), 50.0)
        if new_scale == self.scale:
            return
        self.scale = new_scale
        h = self.winfo_height()
        self.pan_x = world.x - (cx - self.margin) / self.scale
        self.pan_y = world.y - ((h - cy) - self.margin) / self.scale
        self.redraw()

    def zoom_center(self, factor):
        self.zoom_at(self.winfo_width() / 2, self.winfo_height() / 2, factor)

    def zoom_extents(self):
        self._push_view("ext")
        bbox = self.app.bounding_box()
        if bbox is None:
            return
        min_x, min_y, max_x, max_y = bbox
        w = max(max_x - min_x, 1e-9)
        h_world = max(max_y - min_y, 1e-9)
        avail_w = max(self.winfo_width() - 2 * self.margin, 1)
        avail_h = max(self.winfo_height() - 2 * self.margin, 1)
        self.scale = min(avail_w / w, avail_h / h_world)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.pan_x = center_x - (self.winfo_width() / 2 - self.margin) / self.scale
        self.pan_y = center_y - (self.winfo_height() / 2 - self.margin) / self.scale
        self.redraw()

    def _on_wheel(self, event):
        self._push_view("wheel")
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        self.zoom_at(event.x, event.y, factor)

    def _on_pan_press(self, event):
        self._push_view("pan")
        self.pan_last = (event.x, event.y)
        self.config(cursor="fleur")

    def _on_pan_motion(self, event):
        if self.pan_last is None:
            return
        dx = event.x - self.pan_last[0]
        dy = event.y - self.pan_last[1]
        self.pan_last = (event.x, event.y)
        self.pan_x -= dx / self.scale
        self.pan_y += dy / self.scale
        self.redraw()

    def _on_pan_release(self, event):
        self.pan_last = None

    # historial + zoom a rect

    def _push_view(self, key=None):
        """Guarda la vista actual en el historial (agrupa ráfagas iguales)."""
        if key is None or self._last_view_key != key:
            self.view_back.append((self.scale, self.pan_x, self.pan_y))
            if len(self.view_back) > 50:
                self.view_back.pop(0)
            self.view_forward.clear()
        self._last_view_key = key

    def zoom_to_world_rect(self, min_x, min_y, max_x, max_y):
        from ..core import fit_rect_to_view
        self._push_view("rect")
        self.scale, self.pan_x, self.pan_y = fit_rect_to_view(
            min_x, min_y, max_x, max_y,
            self.winfo_width(), self.winfo_height(), self.margin,
        )
        self._last_view_key = None
        self.redraw()

    def zoom_previous(self):
        if not self.view_back:
            return False
        self.view_forward.append((self.scale, self.pan_x, self.pan_y))
        self.scale, self.pan_x, self.pan_y = self.view_back.pop()
        self._last_view_key = None
        self.redraw()
        return True

    def zoom_next(self):
        if not self.view_forward:
            return False
        self.view_back.append((self.scale, self.pan_x, self.pan_y))
        self.scale, self.pan_x, self.pan_y = self.view_forward.pop()
        self._last_view_key = None
        self.redraw()
        return True

    # -----------------------------------
    # SNAP MARKER
    # -----------------------------------

    def _update_snap_marker(self, event):
        """Dibuja el marcador de snap bajo el cursor (solo si se espera punto)."""
        if not self.app._command_waiting_for_point():
            self.snap_drawer.clear()
            return

        raw = self.canvas_to_world(event.x, event.y)
        base = self.app.manager.get_point_base()
        p, kind = self.app.snap_point(raw, base_point=base)

        if kind is not None and kind in SNAP_MARKER_KINDS:
            x, y = self.world_to_canvas(p)
            self.snap_drawer.draw(x, y, kind)
        else:
            self.snap_drawer.clear()


    # ---------------------------------
    # RECOGER IDENTITY CON EL RATON
    # ---------------------------------

    def _pick_entity_at(self, x, y, margin=4):
        """Devuelve el id de la entidad bajo el cursor, o None."""
        items = self.find_overlapping(
            x - margin, y - margin, x + margin, y + margin,
        )
        for item in reversed(items):
            entity_id = self.item_to_entity.get(item)
            if entity_id is not None:
                return entity_id
        return None

    def _handle_entity_pick(self, event):
        entity_id = self._pick_entity_at(event.x, event.y)

        if entity_id is None:
            self.app.write("No hay ninguna entidad ahí.")
            return

        # Inyecta el ID como si se hubiera tecleado.
        self.app.manager.process_input(str(entity_id))

        if hasattr(self.app, "console"):
            self.app.console.entry.focus_set()
        self.app._update_command_cursor()
