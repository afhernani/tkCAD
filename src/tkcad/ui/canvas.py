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

        # Estado de selección visual
        self.select_press_point = None
        self.select_rect_item = None
        self.select_rect_mode = None
        self.select_dragging = False
        self.drag_threshold = 5

        # Estado de grips
        self.grips = []
        self.grip_size = 8
        self.grip_dragging = False
        self.active_grip = None

        # Eventos de ratón
        # self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonPress-1>", self._on_select_press)
        self.bind("<B1-Motion>", self._on_select_motion)
        self.bind("<ButtonRelease-1>", self._on_select_release)
        self.bind("<Button-3>", self._on_canvas_right_click)

    # >>> PEGA AQUÍ LOS MÉTODOS QUE MOVEMOS (Paso 2) <<<
    
    def world_to_canvas(self, p: Point):
        """
        Convierte coordenadas del mundo a coordenadas del canvas.

        Aquí estoy poniendo el origen abajo a la izquierda,
        con el eje Y apuntando hacia arriba.
        """
        h = self.winfo_height()

        if h <= 1:
            h = 400

        # margin = 20

        x = p.x + self.margin
        y = h - self.margin - p.y

        return x, y

    def canvas_to_world(self, x: float, y: float) -> Point:
        h = self.winfo_height()

        if h <= 1:
            h = 400

        return Point(x - self.margin, h - self.margin - y)

    def redraw(self):
        self.delete("all")
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

        for entity in self.app.entities:
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
        # Grips
        self._draw_grips()


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

    def _draw_grips(self):
        self.grips = []

        # Mientras se arrastra un grip, no dibujamos todos los grips
        # para evitar parpadeos y conflictos.
        if self.grip_dragging:
            return

        selected = self.app.get_selected_entities()

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

        item = self.create_rectangle(
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

        entity = self.app.get_entity_by_id(grip["entity_id"])

        if entity is None:
            self.grip_dragging = False
            self.active_grip = None
            return

        raw_p = self.canvas_to_world(x, y)

        base_point = self._get_grip_base(entity, grip)

        p, snap_type = self.app.snap_point(
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
    
