import math

from ..core import Point


class GripManager:
    """Gestiona los grips (tiradores) de las entidades seleccionadas.

    Dibuja los grips en el canvas, detecta cuál está bajo el cursor
    y modifica la entidad correspondiente al arrastrar.
    """

    def __init__(self, canvas, app):
        self.canvas = canvas  # CadCanvas (widget tk.Canvas)
        self.app = app        # CadApp (modelo y servicios)

        self.grips = []
        self.grip_size = 8
        self.grip_dragging = False
        self.active_grip = None


    def draw_grips(self):
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

                x1, y1 = self.canvas.world_to_canvas(start)
                x2, y2 = self.canvas.world_to_canvas(end)

                self.create_grip(x1, y1, entity.id, "start")
                self.create_grip(x2, y2, entity.id, "end")

            # ----------------------------------------------------
            # Polilínea / polígono: grip en cada vértice
            # ----------------------------------------------------
            elif entity.kind in ("polyline", "polygon"):
                points = entity.data["points"]

                for index, point in enumerate(points):
                    x, y = self.canvas.world_to_canvas(point)
                    self.create_grip(
                        x,
                        y,
                        entity.id,
                        "vertex",
                        index=index,
                    )

                # NUEVO: grips de punto medio (verdes) para añadir vértices
                n_segments = len(points) - 1 if entity.kind == "polyline" else len(points)
                for i in range(n_segments):
                    a = points[i]
                    b = points[(i + 1) % len(points)]
                    mid = Point((a.x + b.x) / 2, (a.y + b.y) / 2)
                    mx, my = self.canvas.world_to_canvas(mid)
                    self.create_mid_grip(mx, my, entity.id, i)

            # ----------------------------------------------------
            # Círculo: grip de centro y grip de radio
            # ----------------------------------------------------
            elif entity.kind == "circle":
                center = entity.data["center"]
                radius = entity.data["radius"]

                cx, cy = self.canvas.world_to_canvas(center)

                self.create_grip(cx, cy, entity.id, "center")

                radius_point = Point(center.x + radius, center.y)
                rx, ry = self.canvas.world_to_canvas(radius_point)

                self.create_grip(rx, ry, entity.id, "radius")

            # ----------------------------------------------------
            # Arco: grip de centro, inicio y fin
            # ----------------------------------------------------
            elif entity.kind == "arc":
                center = entity.data["center"]
                radius = entity.data["radius"]
                start_angle = entity.data["start_angle"]
                extent = entity.data["extent"]

                cx, cy = self.canvas.world_to_canvas(center)

                self.create_grip(cx, cy, entity.id, "center")

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

                sx, sy = self.canvas.world_to_canvas(start_point)
                ex, ey = self.canvas.world_to_canvas(end_point)

                self.create_grip(sx, sy, entity.id, "arc_start")
                self.create_grip(ex, ey, entity.id, "arc_end")

            #----------------------------------------------------
            # Elipse: grip de centro y grip de radio
            #----------------------------------------------------
            elif entity.kind == "ellipse":
                center = entity.data["center"]
                rx = float(entity.data["radius_x"])
                ry = float(entity.data["radius_y"])
                rot = math.radians(entity.data.get("rotation", 0.0))

                cx, cy = self.canvas.world_to_canvas(center)

                self.create_grip(cx, cy, entity.id, "center")

                x_point = Point(
                    center.x + rx * math.cos(rot),
                    center.y + ry * math.sin(rot),
                )

                y_rot = rot + math.pi / 2.0

                y_point = Point(
                    center.x + ry * math.cos(y_rot),
                    center.y + ry * math.sin(y_rot),
                )

                x_canvas = self.canvas.world_to_canvas(x_point)
                y_canvas = self.canvas.world_to_canvas(y_point)

                self.create_grip(
                    x_canvas[0],
                    x_canvas[1],
                    entity.id,
                    "ellipse_x",
                )

                self.create_grip(
                    y_canvas[0],
                    y_canvas[1],
                    entity.id,
                    "ellipse_y",
                )

    def create_mid_grip(self, x: float, y: float, entity_id: int, segment_index: int):
        """Crea un grip verde en el punto medio de un segmento.
        
        Al arrastrarlo, se inserta un vértice nuevo entre los dos vértices del segmento.
        """
        s = self.grip_size / 2    # mitad del tamaño de un grip normal
        item = self.canvas.create_rectangle(
            x - s / 2,
            y - s / 2,
            x + s / 2,
            y + s / 2,
            fill="#00ff88",       # verde claro (distintivo)
            outline="#004422",
        )
        self.grips.append({
            "item": item,
            "entity_id": entity_id,
            "type": "midpoint",   # tipo nuevo
            "index": segment_index,
            "x": x,
            "y": y,
        })

    def create_grip(self, x: float, y: float, entity_id: int, grip_type: str, index=None):
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

    def get_grip_at(self, x: float, y: float):
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

    def drag_grip(self, x: float, y: float):
        """modificamos la entidad asociada al grip activo según la posición del mouse"""
        grip = self.active_grip

        if grip is None:
            return

        entity = self.app.get_entity_by_id(grip["entity_id"])

        if entity is None:
            self.grip_dragging = False
            self.active_grip = None
            return

        raw_p = self.canvas.canvas_to_world(x, y)

        base_point = self.get_grip_base(entity, grip)

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

                # if 0 <= index < len(points):
                #     points[index] = p
                if grip["type"] == "vertex":
                    # Mover vértice existente (comportamiento actual)
                    if 0 <= index < len(points):
                        points[index] = p
                        
                elif grip["type"] == "midpoint":
                    # NUEVO: insertar vértice en el segmento `index`
                    # Al arrastrar, el punto sigue al cursor; al soltar queda insertado
                    if 0 <= index <= len(points):
                        # Si ya hay un vértice insertado en este segmento (del arrastre),
                        # reemplazarlo en lugar de insertar otro
                        if len(points) > index + 1 and hasattr(entity, "_mid_grip_inserted"):
                            points[index + 1] = p
                        else:
                            points.insert(index + 1, p)
                            entity._mid_grip_inserted = True

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

        self.app.redraw()

    def get_grip_base(self, entity, grip):
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

    def on_grip_released(self):
        """Limpia el flag de inserción tras soltar un grip midpoint."""
        if self.active_grip is not None and self.active_grip.get("type") == "midpoint":
            entity = self.app.get_entity_by_id(self.active_grip["entity_id"])
            if entity is not None and hasattr(entity, "_mid_grip_inserted"):
                delattr(entity, "_mid_grip_inserted")
