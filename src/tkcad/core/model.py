"""Modelo de documento de tkCAD: entidades, creación y selección.

No conoce Tkinter. Cuando algo cambia llama a notify_change(),
que por defecto no hace nada; la aplicación lo sobreescribe
para redibujar.
"""
import copy, math
from typing import List

from .entity import Entity
from .point import Point
from .types import EPS, TARGET_KIND_MAP
from .layer import Layer


class Document:
    """El 'plano': entidades y lógica pura de modelo."""

    def __init__(self):
        self.entities: List[Entity] = []
        self.next_entity_id = 1
        self.layers = {"0": Layer(name="0")}
        self.current_layer = "0"

    def notify_change(self):
        """Hook de cambio: CadApp lo sobreescribe con redraw."""
        pass

    def log(self, message: str):
        """Hook de mensajes: CadApp lo sobreescribe con write."""
        pass

    # --------------------------------------------------------
    # Creación de entidades
    # --------------------------------------------------------
    def add_entity(self, kind: str, data: dict, notify: bool = True) -> Entity:
        entity = Entity(
            id=self.next_entity_id,
            kind=kind,
            data=data,
            selected=False,
            layer=self.current_layer
        )
        self.next_entity_id += 1
        self.entities.append(entity)
        if notify:
            self.notify_change()
        return entity

    def add_line(self, start: Point, end: Point):
        return self.add_entity("line", {"start": start, "end": end})

    def add_polyline(self, points):
        return self.add_entity("polyline", {"points": list(points)})

    def add_circle(self, center: Point, radius: float):
        return self.add_entity("circle", {"center": center, "radius": radius})

    def add_arc(
        self,
        center: Point,
        radius: float,
        start_angle: float,
        extent: float,
    ):
        return self.add_entity(
            "arc",
            {
                "center": center,
                "radius": radius,
                "start_angle": start_angle,
                "extent": extent,
            },
        )

    def add_polygon(self, points):
        return self.add_entity("polygon", {"points": list(points)})

    def add_ellipse(
        self,
        center: Point,
        radius_x: float,
        radius_y: float,
        rotation: float = 0.0,
    ):
        return self.add_entity(
            "ellipse",
            {
                "center": center,
                "radius_x": float(radius_x),
                "radius_y": float(radius_y),
                "rotation": float(rotation) % 360.0,
            },
        )

    # --------------------------------------------------------
    # Capas
    # --------------------------------------------------------
    def _layer_of(self, entity) -> Layer:
        layer = self.layers.get(entity.layer)
        if layer is None:
            layer = self.layers["0"]
        return layer

    def visible_entities(self):
        return [
            entity for entity in self.entities
            if self._layer_of(entity).visible
        ]

    def selectable_entities(self):
        return [
            entity for entity in self.entities
            if self._layer_of(entity).visible
            and not self._layer_of(entity).locked
        ]

    def get_layer(self, name: str):
        return self.layers.get(name)

    def get_layer_names(self):
        return sorted(self.layers.keys())

    def add_layer(self, name: str, color: str = "white") -> bool:
        name = name.strip()
        if not name or name in self.layers:
            return False
        self.layers[name] = Layer(name=name, color=color)
        return True

    def set_current_layer(self, name: str) -> bool:
        if name not in self.layers:
            return False
        self.current_layer = name
        return True

    def set_layer_color(self, name: str, color: str) -> bool:
        layer = self.layers.get(name)
        if layer is None:
            return False
        layer.color = color
        self.notify_change()
        return True

    def toggle_layer_visible(self, name: str):
        layer = self.layers.get(name)
        if layer is None:
            return None
        layer.visible = not layer.visible
        if not layer.visible:
            for entity in self.entities:
                if entity.layer == name and entity.selected:
                    entity.selected = False
        self.notify_change()
        return layer.visible

    def toggle_layer_locked(self, name: str):
        layer = self.layers.get(name)
        if layer is None:
            return None
        layer.locked = not layer.locked
        if layer.locked:
            for entity in self.entities:
                if entity.layer == name and entity.selected:
                    entity.selected = False
        self.notify_change()
        return layer.locked

    def delete_layer(self, name: str) -> bool:
        # La capa 0 y la capa actual no se pueden borrar.
        if name == "0" or name == self.current_layer:
            return False
        if name not in self.layers:
            return False
        # No se borran capas con entidades (diseño simple y seguro).
        if any(entity.layer == name for entity in self.entities):
            return False
        del self.layers[name]
        return True


    # --------------------------------------------------------
    # Consultas
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # Selección
    # --------------------------------------------------------
    def select_all(self):
        for entity in self.selectable_entities():
            entity.selected = True
        self.notify_change()

    def clear_selection(self):
        for entity in self.entities:
            entity.selected = False
        self.notify_change()

    def select_last(self):
        selectable = self.selectable_entities()
        if selectable:
            selectable[-1].selected = True
            self.notify_change()

    def select_kind(self, kind: str):
        for entity in self.selectable_entities():
            if entity.kind == kind:
                entity.selected = True
        self.notify_change()

    def toggle_selection(self, entity_id: int, notify: bool = True) -> bool:
        entity = self.get_entity_by_id(entity_id)
        if entity is None:
            return False
        layer = self._layer_of(entity)
        if not layer.visible or layer.locked:
            return False
        entity.selected = not entity.selected
        if notify:
            self.notify_change()
        return True

    def set_selection_ids(self, ids):
        ids_set = set(ids)
        for entity in self.entities:
            layer = self._layer_of(entity)
            entity.selected = (
                entity.id in ids_set
                and layer.visible
                and not layer.locked
            )
        self.notify_change()

    def add_selection_ids(self, ids):
        ids_set = set(ids)
        for entity in self.selectable_entities():
            if entity.id in ids_set:
                entity.selected = True
        self.notify_change()

    def remove_selection_ids(self, ids):
        ids_set = set(ids)
        for entity in self.entities:
            if entity.id in ids_set:
                entity.selected = False
        self.notify_change()

    # --------------------------------------------------------
    # Borrado
    # --------------------------------------------------------
    def delete_selected(self):
        selected_count = self.selection_count()
        if selected_count == 0:
            return 0
        self.entities = [
            entity for entity in self.entities if not entity.selected
        ]
        self.notify_change()
        return selected_count

    def delete_entities(self, target: str):
        if target == "TODO":
            candidates = self.selectable_entities()
        else:
            kind = TARGET_KIND_MAP.get(target)
            if kind is None:
                return 0
            candidates = [
                entity for entity in self.selectable_entities()
                if entity.kind == kind
            ]
        count = len(candidates)
        if count:
            ids = {entity.id for entity in candidates}
            self.entities = [
                entity for entity in self.entities
                if entity.id not in ids
            ]
            self.notify_change()
        return count

    # --------------------------------------------------------
    # Mover
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
            self.log("Desplazamiento cero.")
            return

        for entity in self.get_selected_entities():
            self._move_entity(entity, dx, dy)

        self.notify_change()

    def move_entities(self, target: str, dx: float, dy: float):
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            self.log("Desplazamiento cero.")
            return

        if target == "TODO":
            for entity in self.entities:
                self._move_entity(entity, dx, dy)

        else:
            kind = TARGET_KIND_MAP.get(target)

            if kind is None:
                self.log(f"No se puede mover: {target}")
                return

            for entity in self.entities:
                if entity.kind == kind:
                    self._move_entity(entity, dx, dy)

        self.notify_change()

    #--------------------------------------------------------
    # COPIAR
    #--------------------------------------------------------

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
                notify=False,
            )

            self._move_entity(new_entity, dx, dy)

            new_ids.append(new_entity.id)

        self.notify_change()

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
                notify=False,
            )

            self._move_entity(new_entity, dx, dy)

            new_ids.append(new_entity.id)

        self.notify_change()

        return new_ids
    
    # --------------------------------------------------------
    # ESCALAR
    # --------------------------------------------------------

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

        self.notify_change()

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

        self.notify_change()

        return len(entities)

    # --------------------------------------------------------
    # SIMETRÍA
    # --------------------------------------------------------
    
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

        self.notify_change()

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

        self.notify_change()

        return len(entities)

    # --------------------------------------------------------
    # ROTAR
    # -------------------------------------------------------- 
        
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

        self.notify_change()

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

        self.notify_change()

        return len(entities)

    # --------------------------------------------------------
    # Edición topológica (trim / extend)
    # --------------------------------------------------------

    def trim_line_by_line(self, limit_id: int, target_id: int, keep_point: Point):
        # Import perezoso: geometry importa de core, así que core
        # no puede importar geometry a nivel de módulo (circular).
        from ..geometry import line_line_intersection, projection_param

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

        self.notify_change()

        return True, "Entidad recortada correctamente."
    
    def extend_line_to_line(self, limit_id: int, target_id: int):
        # Import perezoso: geometry importa de core, así que core
        # no puede importar geometry a nivel de módulo (circular).
        from ..geometry import line_line_intersection

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

        self.notify_change()

        return True, "Entidad extendida correctamente."

    # ----------------------------------------
    # ZOOM y PAN
    # ----------------------------------------

    def bounding_box(self):
        """Caja envolvente de las entidades visibles, o None."""
        visibles = self.visible_entities()
        if not visibles:
            return None
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")
        for entity in visibles:
            for point in self._bbox_points(entity):
                min_x = min(min_x, point.x)
                min_y = min(min_y, point.y)
                max_x = max(max_x, point.x)
                max_y = max(max_y, point.y)
        return min_x, min_y, max_x, max_y

    def _bbox_points(self, entity):
        data = entity.data
        if entity.kind == "line":
            return [data["start"], data["end"]]
        if entity.kind in ("polyline", "polygon"):
            return list(data["points"])
        if entity.kind in ("circle", "arc"):
            c = data["center"]
            r = data["radius"]
            return [Point(c.x - r, c.y - r), Point(c.x + r, c.y + r)]
        if entity.kind == "ellipse":
            c = data["center"]
            m = max(data["radius_x"], data["radius_y"])
            return [Point(c.x - m, c.y - m), Point(c.x + m, c.y + m)]
        return []