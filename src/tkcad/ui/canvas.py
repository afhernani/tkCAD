import math
import tkinter as tk

from ..core import Point
from .snap_markers import SnapMarkerDrawer, SNAP_MARKER_KINDS
from ..core.dimension import (angular_geometry, angular_ray_ends, angular_text_position, dimension_geometry,
                                  dimension_text_position,
                                  dimension_text_height)


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
            "dimension": "#ff9944",
            "spline": "#66ccff",
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
            # Cota: extensiones + línea de cota + flechas + texto
            # ----------------------------------------------------
            elif entity.kind == "dimension":
                data = entity.data

                if data["dim_type"] == "angular":
                    self._draw_angular_dimension(entity, data, color)
                    continue # salta al siguiente entity

                g = dimension_geometry(entity.data)

                # Líneas de extensión
                for ext in (g["ext1"], g["ext2"]):
                    if ext is None:
                        continue
                    a, b = ext
                    x1, y1 = self.world_to_canvas(a)
                    x2, y2 = self.world_to_canvas(b)
                    item = self.create_line(x1, y1, x2, y2, fill=color)
                    self.item_to_entity[item] = entity.id

                # Línea de cota
                x1, y1 = self.world_to_canvas(g["dim_start"])
                x2, y2 = self.world_to_canvas(g["dim_end"])
                item = self.create_line(x1, y1, x2, y2, fill=color)
                self.item_to_entity[item] = entity.id

                # Flechas
                self._draw_dimension_arrows(g, color, entity.id)

                # Texto con la medida (posición y altura editables)
                prefix = {"radius": "R", "diameter": "Ø"}.get(
                    entity.data["dim_type"], ""
                )
                label = f"{prefix}{g['value']:.2f}"
                tp = dimension_text_position(entity.data)   # ← respeta text_offset
                th = dimension_text_height(entity.data)     # ← respeta text_height
                tx, ty = self.world_to_canvas(tp)
                font_px = max(int(th * self.scale), 4)
                item = self.create_text(
                    tx, ty - font_px,
                    text=label,
                    fill=color,
                    font=("TkDefaultFont", -font_px),
                )
                self.item_to_entity[item] = entity.id

            # ----------------------------------------------------
            # Spline: curva evaluada como polilínea de alta resolución
            # ----------------------------------------------------
            elif entity.kind == "spline":
                from ..core.spline import eval_cubic_spline

                curve = eval_cubic_spline(
                    entity.data["points"],
                    samples_per_segment=30,
                    closed=entity.data.get("closed", False),
                )

                screen_pts = [self.world_to_canvas(p) for p in curve]
                if len(screen_pts) >= 2:
                    item = self.create_line(screen_pts, fill=color)
                    self.item_to_entity[item] = entity.id
            
            elif entity.kind == "insert":
                self._draw_insert(entity, color)

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


    def _draw_insert(self, entity, color):
        """Dibuja un insert expandiendo su definición transformada."""
        tag = f"entity_{entity.id}"
        for kind, data, layer in self.app.insert_world_entities(entity):
            if kind == "line":
                x1, y1 = self.world_to_canvas(data["start"])
                x2, y2 = self.world_to_canvas(data["end"])
                item = self.create_line(x1, y1, x2, y2, fill=color,
                                        width=2, tags=tag)
                self.item_to_entity[item] = entity.id

            elif kind in ("polyline", "polygon"):
                points = data["points"]
                if kind == "polygon" and len(points) >= 3:
                    points = list(points) + [points[0]]
                coords = []
                for p in points:
                    coords.extend(self.world_to_canvas(p))
                if len(coords) >= 4:
                    item = self.create_line(*coords, fill=color,
                                            width=2, tags=tag)
                    self.item_to_entity[item] = entity.id

            elif kind == "circle":
                cx, cy = self.world_to_canvas(data["center"])
                r_px = self.world_to_canvas_length(data["radius"])
                item = self.create_oval(cx - r_px, cy - r_px,
                                        cx + r_px, cy + r_px,
                                        outline=color, width=2, tags=tag)
                self.item_to_entity[item] = entity.id

            elif kind == "arc":
                cx, cy = self.world_to_canvas(data["center"])
                r_px = self.world_to_canvas_length(data["radius"])
                item = self.create_arc(cx - r_px, cy - r_px,
                                       cx + r_px, cy + r_px,
                                       start=data["start_angle"],
                                       extent=data["extent"],
                                       style="arc", outline=color,
                                       width=2, tags=tag)
                self.item_to_entity[item] = entity.id

            elif kind == "ellipse":
                c = data["center"]
                rx = float(data["radius_x"])
                ry = float(data["radius_y"])
                rot = math.radians(data.get("rotation", 0.0))
                cos_r, sin_r = math.cos(rot), math.sin(rot)
                coords = []
                for i in range(64):
                    t = 2.0 * math.pi * i / 64
                    x = rx * math.cos(t)
                    y = ry * math.sin(t)
                    wp = Point(c.x + x * cos_r - y * sin_r,
                               c.y + x * sin_r + y * cos_r)
                    coords.extend(self.world_to_canvas(wp))
                if len(coords) >= 6:
                    item = self.create_polygon(*coords, outline=color,
                                               fill="", smooth=True,
                                               width=2, tags=tag)
                    self.item_to_entity[item] = entity.id

            elif kind == "text":
                x, y = self.world_to_canvas(data["position"])
                font_px = max(int(self.world_to_canvas_length(data["height"])), 4)
                item = self.create_text(x, y, text=data["content"],
                                        fill=color, anchor="center",
                                        font=("TkDefaultFont", -font_px))
                self.item_to_entity[item] = entity.id

            elif kind == "spline":
                from ..core.spline import eval_cubic_spline
                curve = eval_cubic_spline(
                    data["points"], samples_per_segment=30,
                    closed=data.get("closed", False),
                )
                pts = [self.world_to_canvas(p) for p in curve]
                if len(pts) >= 2:
                    item = self.create_line(pts, fill=color)
                    self.item_to_entity[item] = entity.id

            elif entity.kind == "dimension":
                self._draw_dimension_data(
                    entity.data, color, f"entity_{entity.id}", entity.id)

            elif kind == "dimension":
                self._draw_dimension_data(data, color, tag, entity.id)


    def _draw_dimension_data(self, data, color, tag, eid):
        """Dibuja una cota desde su data (lo usan redraw y _draw_insert)."""
        t = data.get("dim_type")
        th = float(data.get("text_height", 2.5))
        font_px = max(int(self.world_to_canvas_length(th)), 4)

        def seg(a, b, width=1):
            x1, y1 = self.world_to_canvas(a)
            x2, y2 = self.world_to_canvas(b)
            item = self.create_line(x1, y1, x2, y2, fill=color,
                                    width=width, tags=tag)
            self.item_to_entity[item] = eid

        def texto(p, s):
            x, y = self.world_to_canvas(p)
            item = self.create_text(x, y - 4, text=s, fill=color,
                                    anchor="center",
                                    font=("TkDefaultFont", -font_px))
            self.item_to_entity[item] = eid

        if t in ("linear_h", "linear_v", "aligned"):
            p1, p2 = data["p1"], data["p2"]
            off = float(data.get("offset", 10.0))
            if t == "linear_h":
                y = max(p1.y, p2.y) + off
                d1, d2 = Point(p1.x, y), Point(p2.x, y)
                value = abs(p2.x - p1.x)
            elif t == "linear_v":
                x = max(p1.x, p2.x) + off
                d1, d2 = Point(x, p1.y), Point(x, p2.y)
                value = abs(p2.y - p1.y)
            else:
                ux, uy = p2.x - p1.x, p2.y - p1.y
                L = math.hypot(ux, uy) or 1.0
                nx, ny = -uy / L, ux / L
                d1 = Point(p1.x + nx * off, p1.y + ny * off)
                d2 = Point(p2.x + nx * off, p2.y + ny * off)
                value = L
            seg(p1, d1)
            seg(p2, d2)
            seg(d1, d2)
            self._draw_arrows_simple(d1, d2, color, tag, eid)
            texto(Point((d1.x + d2.x) / 2, (d1.y + d2.y) / 2),
                  f"{value:.2f}")

        elif t == "radius":
            c, p = data["center"], data["p"]
            seg(c, p)
            r = math.hypot(p.x - c.x, p.y - c.y)
            texto(Point((c.x + p.x) / 2, (c.y + p.y) / 2), f"R{r:.2f}")

        elif t == "angular":
            g = angular_geometry(data)
            v = g["vertex"]
            seg(v, g["arc_start"])
            seg(v, g["arc_end"])
            cx, cy = self.world_to_canvas(v)
            r_px = self.world_to_canvas_length(g["radius"])
            item = self.create_arc(cx - r_px, cy - r_px,
                                   cx + r_px, cy + r_px,
                                   start=g["a1"], extent=g["extent"],
                                   style="arc", outline=color,
                                   width=1, tags=tag)
            self.item_to_entity[item] = eid
            texto(angular_text_position(data), f"{g['value']:.1f}°")

    def _draw_arrows_simple(self, a, b, color, tag, eid):
        """Flechas simples (8 px) en los extremos del segmento a→b."""
        x1, y1 = self.world_to_canvas(a)
        x2, y2 = self.world_to_canvas(b)
        ux, uy = x2 - x1, y2 - y1
        L = math.hypot(ux, uy) or 1.0
        ux, uy = ux / L, uy / L
        for tx, ty, dx, dy in ((x1, y1, ux, uy), (x2, y2, -ux, -uy)):
            for ang in (25, -25):
                ca, sa = math.cos(math.radians(ang)), \
                    math.sin(math.radians(ang))
                wx = dx * ca - dy * sa
                wy = dx * sa + dy * ca
                item = self.create_line(tx, ty, tx + wx * 8, ty + wy * 8,
                                        fill=color, width=1, tags=tag)
                self.item_to_entity[item] = eid


    def _draw_angular_dimension(self, entity, data, color):
        """Dibuja una cota angular: extensiones, arco, flechas y texto."""
        g = dimension_geometry(data)
        vertex = g["vertex"]

        # --- Líneas de extensión: vértice → puntos del rayo ---
        vx, vy = self.world_to_canvas(vertex)
        for endp in angular_ray_ends(data):          # ← antes: (g["arc_start"], g["arc_end"])
            ex, ey = self.world_to_canvas(endp)
            item = self.create_line(vx, vy, ex, ey, fill=color)
            self.item_to_entity[item] = entity.id

        # --- Arco muestreado como polilínea ---
        pts = [self.world_to_canvas(p) for p in g["arc_points"]]
        if len(pts) >= 2:
            item = self.create_line(pts, fill=color)
            self.item_to_entity[item] = entity.id

        # --- Flechas tangentes en los extremos del arco ---
        a1 = math.radians(g["a1"])
        a2 = math.radians(g["a1"] + g["extent"])
        s1 = self.world_to_canvas(g["arc_start"])
        s2 = self.world_to_canvas(g["arc_end"])

        item = self._arrow_screen(s1, math.sin(a1), math.cos(a1), color)
        self.item_to_entity[item] = entity.id
        item = self._arrow_screen(s2, -math.sin(a2), -math.cos(a2), color)
        self.item_to_entity[item] = entity.id

        # --- Texto con el ángulo en grados ---
        # tp = dimension_text_position(data)
        tp = angular_text_position(data)
        th = dimension_text_height(data)
        tx, ty = self.world_to_canvas(tp)
        font_px = max(int(th * self.scale), 4)
        item = self.create_text(
            tx, ty - font_px,
            text=f"{g['value']:.1f}°",
            fill=color,
            font=("TkDefaultFont", -font_px),
        )
        self.item_to_entity[item] = entity.id

    def _arrow_screen(self, tip, dirx, diry, color, length=10, half=3.5):
        """Flecha rellena en coordenadas de pantalla."""
        n = math.hypot(dirx, diry) or 1.0
        dx, dy = dirx / n, diry / n
        px, py = -dy, dx
        b1 = (tip[0] - dx * length + px * half,
              tip[1] - dy * length + py * half)
        b2 = (tip[0] - dx * length - px * half,
              tip[1] - dy * length - py * half)
        return self.create_polygon(
            [tip[0], tip[1], b1[0], b1[1], b2[0], b2[1]],
            fill=color, outline=color,
        )

    def _draw_grid(self):
        """Método para dibujar la malla de fondo en el canvas."""
        if not self.app.show_grid:
            return

        if self.app.grid_size <= 0:
            return

        # Cortocircuito: vista corrupta → no dibujar malla
        if not (math.isfinite(self.scale) and self.scale > 1e-9
                and math.isfinite(self.pan_x) and math.isfinite(self.pan_y)):
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
        # Si la vista está corrupta, reinicia a valores sanos
        if not all(math.isfinite(v) for v in (world.x, world.y, self.scale)):
            self.scale = 1.0
            self.pan_x = 0.0
            self.pan_y = 0.0
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

        # Protección contra bbox degenerado (vacío o con NaN/inf)
        if not all(math.isfinite(v) for v in bbox):
            # Revertir el push: la vista no cambia
            self._pop_view_silent()
            return

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

    def _pop_view_silent(self):
        """Quita la última vista guardada sin restaurarla (para reverts)."""
        if self.view_back:
            self.view_back.pop()
        self._last_view_key = None

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
        self.app._update_command_cursor()

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

    # --------------------------------------
    # AYUDAS A DIMENSIONAR FLECHAS ARRAWS
    # --------------------------------------

    def _draw_dimension_arrows(self, g, color, entity_id):
        """Dibuja las flechas en los extremos de la línea de cota."""
        ax, ay = self.world_to_canvas(g["dim_start"])
        bx, by = self.world_to_canvas(g["dim_end"])
        length = math.hypot(bx - ax, by - ay)
        if length < 1e-9:
            return

        angle = math.atan2(by - ay, bx - ax)
        size = 8.0   # tamaño fijo en píxeles (como en un CAD)

        # Radio: una sola flecha en el extremo; lineales: dos
        if g.get("ext1") is None:
            tips = [(bx, by, angle)]
        else:
            tips = [(ax, ay, angle + math.pi), (bx, by, angle)]

        for tip_x, tip_y, ang in tips:
            for delta in (math.radians(20), -math.radians(20)):
                x2 = tip_x - size * math.cos(ang + delta)
                y2 = tip_y - size * math.sin(ang + delta)
                item = self.create_line(tip_x, tip_y, x2, y2, fill=color)
                self.item_to_entity[item] = entity_id

