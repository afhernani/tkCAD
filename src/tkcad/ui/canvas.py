import math
import tkinter as tk

from ..core import Point


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

        # Estado de grips
        # self.grips = []
        # self.grip_size = 8
        # self.grip_dragging = False
        # self.active_grip = None
        self.grip_manager = None
        # seguir el puntero del ratón.
        self.rubber_item = None
        self.preview_circle_item = None
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

                item = self.create_oval(
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

                item = self.create_arc(
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

        g = self.app.grid_size

        # Protección contra mallas demasiado densas
        if (max_x - min_x) / g > 1000:
            return

        if (max_y - min_y) / g > 1000:
            return

        x = math.floor(min_x / g) * g

        while x <= max_x:
            cx = x + self.margin

            self.create_line(
                cx, 0, cx, h,
                fill="#222222",
            )

            x += g

        y = math.floor(min_y / g) * g

        while y <= max_y:
            _, cy = self.world_to_canvas(Point(0.0, y))

            self.create_line(
                0, cy, w, cy,
                fill="#222222",
            )

            y += g

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
        # Si un comando está esperando punto, el clic introduce un punto.
        if self.app._command_waiting_for_point():
            self._handle_point_click(event)
            return
        # si no comprobamos grips.
        grip = self.grip_manager.get_grip_at(event.x, event.y)

        if grip is not None:
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
            self.grip_manager.grip_dragging = False
            self.grip_manager.active_grip = None

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
                self.app.toggle_selection(entity_id)

                if hasattr(self, "console"):
                    self.app.console.entry.focus_set()

                return

        # Si quieres que un clic en vacío limpie la selección,
        # descomenta esta línea:
        self.app.clear_selection()

        if hasattr(self, "console"):
            self.app.console.entry.focus_set()

    def _on_motion(self, event):
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