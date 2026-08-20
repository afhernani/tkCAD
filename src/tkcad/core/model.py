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
        # undo / redo
        self._undo_stack = []
        self._redo_stack = []
        self.history_limit = 100
        self._pending_snapshot = None
        self._mutated = False

        self.block_names = {}      # block_id -> nombre
        self._next_block_id = 1

        # si hay cambios en el documento.
        self.modified = False


    def notify_change(self):
        """Hook de cambio: CadApp lo sobreescribe con redraw."""
        self.update_associative_dimensions()
        self._mutated = True
        self.modified = True

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

    def add_text(self, position: Point, height: float, content: str):
        return self.add_entity("text", {
            "position": position,
            "height": float(height),
            "content": str(content),
        })

    def add_dimension(self, dim_type, p1=None, p2=None, center=None, p=None,
                    offset=10.0, assoc_entity_id=None, assoc_kind=None,
                    assoc_angle=None, text_height=2.5, vertex=None, radius=None):
        data = {
            "dim_type": dim_type,
            "offset": float(offset),
            "text_height": float(text_height),
            "text_offset": Point(0, 0),
        }
        if p1 is not None:
            data["p1"] = p1
        if p2 is not None:
            data["p2"] = p2
        if center is not None:
            data["center"] = center
        if p is not None:
            data["p"] = p
        if vertex is not None:                 # ← NUEVO (angular)
            data["vertex"] = vertex
        if radius is not None:                 # ← NUEVO (radio del arco)
            data["radius"] = float(radius)
        if assoc_entity_id is not None:
            data["assoc_entity_id"] = assoc_entity_id
        if assoc_kind is not None:
            data["assoc_kind"] = assoc_kind
        if assoc_angle is not None:
            data["assoc_angle"] = float(assoc_angle)
        
        return self.add_entity("dimension", data)

    def update_associative_dimensions(self):
        """Re-resuelve los puntos de las cotas asociativas desde su entidad."""
        from .dimension import resolve_assoc

        for entity in self.entities:
            if entity.kind != "dimension":
                continue
            ref_id = entity.data.get("assoc_entity_id")
            if ref_id is None:
                continue

            ref = self.get_entity_by_id(ref_id)
            if ref is None:
                # La entidad referida ya no existe → desasocia, conserva puntos
                entity.data.pop("assoc_entity_id", None)
                entity.data.pop("assoc_kind", None)
                continue

            resolved = resolve_assoc(entity.data, ref)
            if resolved:
                entity.data.update(resolved)

    def add_spline(self, points, closed=False):
        return self.add_entity("spline", {
            "points": list(points),
            "closed": bool(closed),
        })

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
        self.notify_change()
        return True

    def set_current_layer(self, name: str) -> bool:
        if name not in self.layers:
            return False
        self.current_layer = name
        self.notify_change()
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
        self.notify_change()
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

        # Bloques: el bloque entero se conmuta según la entidad clicada
        # (si estaba sin seleccionar → se selecciona todo el bloque;
        #  si estaba seleccionada → se quita todo el bloque)
        new_state = not entity.selected
        for i in self._expand_blocks([entity_id]):
            e = self.get_entity_by_id(i)
            if e is None:
                continue
            lay = self._layer_of(e)
            if not lay.visible or lay.locked:
                continue
            e.selected = new_state

        # entity.selected = not entity.selected
        if notify:
            self.notify_change()
        return True

    def set_selection_ids(self, ids):
        ids = self._expand_blocks(ids)
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

        # texto
        elif entity.kind == "text":
            entity.data["position"] = self._move_point(
                entity.data["position"],
                dx,
                dy,
            )

        elif entity.kind == "dimension":
            d = entity.data
            for key in ("p1", "p2", "center", "p", "vertex"):   # ← vertex añadido
                if key in d:
                    d[key] = self._move_point(d[key], dx, dy)

        elif entity.kind == "spline":
            entity.data["points"] = [
                self._move_point(p, dx, dy)
                for p in entity.data["points"]
            ]


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
        from ..geometry import line_line_intersection_infinite

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

        # Validar que ninguna línea sea degenerada (punto)
        if (abs(b.x - a.x) < EPS and abs(b.y - a.y) < EPS):
            return False, "La línea límite es degenerada (start == end)."
        if (abs(d.x - c.x) < EPS and abs(d.y - c.y) < EPS):
            return False, "La línea a extender es degenerada (start == end)."

        inter = line_line_intersection_infinite(a, b, c, d)

        if inter is None:
            return False, "Las líneas son paralelas."

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

    def trim_line_by_circle(self, limit_id: int, target_id: int, keep_point: Point):
        """
        Recorta una línea usando un círculo como límite.
        
        Args:
            limit_id: ID del círculo límite
            target_id: ID de la línea a recortar
            keep_point: Punto que indica qué lado de la línea conservar
        
        Returns:
            (bool, str): (éxito, mensaje)
        """
        from ..geometry import line_circle_intersection, projection_param

        limit = self.get_entity_by_id(limit_id)
        target = self.get_entity_by_id(target_id)

        if limit is None or target is None:
            return False, "Entidad no encontrada."
        if limit.kind != "circle":
            return False, "El límite debe ser un círculo."
        if target.kind != "line":
            return False, "Por ahora solo se recortan líneas."
        if limit_id == target_id:
            return False, "El límite y la entidad a recortar no pueden ser la misma."

        a = target.data["start"]
        b = target.data["end"]
        center = limit.data["center"]
        radius = limit.data["radius"]

        # Validar línea degenerada
        if abs(b.x - a.x) < EPS and abs(b.y - a.y) < EPS:
            return False, "La línea a recortar es degenerada."

        # Calcular intersecciones de la línea con el círculo
        hits = line_circle_intersection(a, b, center, radius)

        if not hits:
            return False, "La línea no intersecta el círculo."

        # Ordenar intersecciones por parámetro t
        hits.sort(key=lambda h: h[1])

        # Proyectar keep_point sobre la línea para saber qué lado mantener
        t_keep = projection_param(keep_point, a, b)

        if len(hits) == 1:
            # Tangente o un solo cruce: recortar en ese punto
            hit_point, t_hit = hits[0]
            if t_keep < t_hit:
                target.data["end"] = hit_point
            else:
                target.data["start"] = hit_point

        elif len(hits) == 2:
            # Dos cruces: decidir qué segmento mantener
            (p1, t1), (p2, t2) = hits

            if t_keep < t1:
                # Mantener el segmento antes del primer cruce
                target.data["end"] = p1
            elif t_keep > t2:
                # Mantener el segmento después del segundo cruce
                target.data["start"] = p2
            else:
                # Mantener el segmento entre los dos cruces
                target.data["start"] = p1
                target.data["end"] = p2

        self.notify_change()
        return True, "Línea recortada con círculo."

    def trim_line_by_arc(self, limit_id: int, target_id: int, keep_point: Point):
        """
        Recorta una línea usando un arco como límite.
        
        Args:
            limit_id: ID del arco límite
            target_id: ID de la línea a recortar
            keep_point: Punto que indica qué lado de la línea conservar
        
        Returns:
            (bool, str): (éxito, mensaje)
        """
        from ..geometry import line_arc_intersection, projection_param

        limit = self.get_entity_by_id(limit_id)
        target = self.get_entity_by_id(target_id)

        if limit is None or target is None:
            return False, "Entidad no encontrada."
        if limit.kind != "arc":
            return False, "El límite debe ser un arco."
        if target.kind != "line":
            return False, "Por ahora solo se recortan líneas."
        if limit_id == target_id:
            return False, "El límite y la entidad a recortar no pueden ser la misma."

        a = target.data["start"]
        b = target.data["end"]
        center = limit.data["center"]
        radius = limit.data["radius"]
        start_angle = limit.data["start_angle"]
        extent = limit.data["extent"]

        # Validar línea degenerada
        if abs(b.x - a.x) < EPS and abs(b.y - a.y) < EPS:
            return False, "La línea a recortar es degenerada."

        # Calcular intersecciones de la línea con el arco
        hits = line_arc_intersection(a, b, center, radius, start_angle, extent)

        if not hits:
            return False, "La línea no intersecta el arco."

        # Ordenar intersecciones por parámetro t
        hits.sort(key=lambda h: h[1])

        # Proyectar keep_point sobre la línea
        t_keep = projection_param(keep_point, a, b)

        if len(hits) == 1:
            hit_point, t_hit = hits[0]
            if t_keep < t_hit:
                target.data["end"] = hit_point
            else:
                target.data["start"] = hit_point

        elif len(hits) == 2:
            (p1, t1), (p2, t2) = hits

            if t_keep < t1:
                target.data["end"] = p1
            elif t_keep > t2:
                target.data["start"] = p2
            else:
                target.data["start"] = p1
                target.data["end"] = p2

        self.notify_change()
        return True, "Línea recortada con arco."

    def trim_by_entity(self, limit_id: int, target_id: int, keep_point: Point):
        """
        Dispatcher genérico de recorte.
        Elige el método adecuado según el tipo de entidad límite.
        
        Args:
            limit_id: ID de la entidad límite
            target_id: ID de la entidad a recortar
            keep_point: Punto que indica qué lado conservar
        
        Returns:
            (bool, str): (éxito, mensaje)
        """
        limit = self.get_entity_by_id(limit_id)
        target = self.get_entity_by_id(target_id)

        if limit is None:
            return False, f"Entidad límite {limit_id} no encontrada."
        if target is None:
            return False, f"Entidad {target_id} no encontrada."

        limit_kind = limit.kind
        target_kind = target.kind

        # --- Línea contra Línea ---
        if limit_kind == "line" and target_kind == "line":
            return self.trim_line_by_line(limit_id, target_id, keep_point)

        # --- Línea contra Círculo ---
        if limit_kind == "circle" and target_kind == "line":
            return self.trim_line_by_circle(limit_id, target_id, keep_point)

        # --- Línea contra Arco ---
        if limit_kind == "arc" and target_kind == "line":
            return self.trim_line_by_arc(limit_id, target_id, keep_point)

        # --- ARCO contra Línea / Círculo / Arco ---   ← NUEVO
        if target_kind == "arc" and limit_kind in ("line", "circle", "arc"):
            return self.trim_arc_by_entity(limit_id, target_id, keep_point)

        # --- Combinación no soportada ---
        return False, (
            f"RECORTAR no soporta {target_kind.upper()} "
            f"con límite {limit_kind.upper()}."
        )


    def trim_arc_by_entity(self, limit_id: int, target_id: int, keep_point: Point):
        """
        Recorta un ARCO usando como límite una línea, círculo u otro arco.
        
        Args:
            limit_id: ID de la entidad límite
            target_id: ID del arco a recortar
            keep_point: Punto que indica qué parte del arco conservar
        
        Returns:
            (bool, str): (éxito, mensaje)
        """
        from ..geometry import (
            line_arc_intersection,
            circle_circle_intersection,
            arc_arc_intersection,
        )

        limit = self.get_entity_by_id(limit_id)
        target = self.get_entity_by_id(target_id)

        if limit is None or target is None:
            return False, "Entidad no encontrada."
        if target.kind != "arc":
            return False, "La entidad a recortar debe ser un arco."
        if limit_id == target_id:
            return False, "El límite y la entidad a recortar no pueden ser la misma."

        center = target.data["center"]
        radius = target.data["radius"]
        start_angle = target.data["start_angle"]
        extent = target.data["extent"]

        # Calcular los puntos de corte según el tipo de límite
        if limit.kind == "line":
            hit_points = [
                p for p, _ in line_arc_intersection(
                    limit.data["start"], limit.data["end"],
                    center, radius, start_angle, extent,
                )
            ]
        elif limit.kind == "circle":
            raw = circle_circle_intersection(
                center, radius, limit.data["center"], limit.data["radius"]
            )
            hit_points = [
                p for p in raw
                if self._point_in_arc_range(p, center, start_angle, extent)
            ]
        elif limit.kind == "arc":
            hit_points = arc_arc_intersection(
                limit.data["center"], limit.data["radius"],
                limit.data["start_angle"], limit.data["extent"],
                center, radius, start_angle, extent,
            )
        else:
            return False, (
                f"RECORTAR no soporta límite {limit.kind.upper()} con arco."
            )

        if not hit_points:
            return False, "El límite no intersecta el arco."

        return self._trim_arc_at_points(
            target, center, start_angle, extent, hit_points, keep_point
        )


    def _point_in_arc_range(self, p, center, start_angle, extent) -> bool:
        """True si el ángulo de p (respecto al centro) cae dentro del arco."""
        angle = math.degrees(math.atan2(p.y - center.y, p.x - center.x))
        angle = angle % 360.0
        start = start_angle % 360.0
        end = (start + extent) % 360.0

        if extent >= 360.0 - 1e-9:
            return True
        if start <= end:
            return start - 1e-9 <= angle <= end + 1e-9
        return angle >= start - 1e-9 or angle <= end + 1e-9


    def _trim_arc_at_points(
        self, target, center, start_angle, extent, hit_points, keep_point
    ):
        """
        Aplica el recorte de un arco en los puntos de corte dados.
        Modifica start_angle / extent según el lado a conservar.
        """
        # Parámetros angulares de los cortes (posición dentro del arco, 0..extent)
        params = []
        for p in hit_points:
            angle = math.degrees(math.atan2(p.y - center.y, p.x - center.x))
            s = (angle - start_angle) % 360.0
            s = min(max(s, 0.0), extent)   # clamp por tolerancias
            params.append(s)

        params.sort()
        # Eliminar duplicados (tangentes)
        params = [
            t for i, t in enumerate(params)
            if i == 0 or t - params[i - 1] > 1e-6
        ]

        if not params:
            return False, "Sin puntos de corte válidos."

        # Parámetro del punto a conservar
        phi = math.degrees(math.atan2(keep_point.y - center.y, keep_point.x - center.x))
        s_keep = (phi - start_angle) % 360.0

        if s_keep > extent:
            # keep_point fuera del rango angular: elegir el lado más cercano
            dist_before = 360.0 - s_keep   # distancia "antes del inicio"
            dist_after = s_keep - extent   # distancia "después del final"
            s_keep = 0.0 if dist_before < dist_after else extent

        # Decidir qué tramo conservar
        if len(params) == 1:
            s1 = params[0]
            if s_keep < s1:
                new_start, new_extent = start_angle, s1
            else:
                new_start, new_extent = start_angle + s1, extent - s1
        else:
            s1, s2 = params[0], params[1]
            if s_keep < s1:
                new_start, new_extent = start_angle, s1
            elif s_keep > s2:
                new_start, new_extent = start_angle + s2, extent - s2
            else:
                new_start, new_extent = start_angle + s1, s2 - s1

        if new_extent <= 1e-6:
            return False, "El recorte eliminaría el arco por completo."

        target.data["start_angle"] = new_start % 360.0
        target.data["extent"] = new_extent

        self.notify_change()
        return True, "Arco recortado correctamente."

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

    # --------------------------------------------------------
    # Historial (deshacer / rehacer)
    # --------------------------------------------------------
    def _snapshot(self):
        return {
            "entities": copy.deepcopy(self.entities),
            "next_entity_id": self.next_entity_id,
            "layers": copy.deepcopy(self.layers),
            "current_layer": self.current_layer,
        }

    def _restore(self, state):
        self.entities = state["entities"]
        self.next_entity_id = state["next_entity_id"]
        self.layers = state["layers"]
        self.current_layer = state["current_layer"]
        self.notify_change()

    def mark_action(self):
        """Inicio de una acción potencialmente mutante."""
        self._pending_snapshot = self._snapshot()
        self._mutated = False

    def mark_saved(self):
        """El proyecto queda como 'sin cambios pendientes'."""
        self.modified = False

    def commit_action(self):
        """Fin de la acción: solo guarda el paso si hubo mutaciones."""
        if self._pending_snapshot is not None and self._mutated:
            self._undo_stack.append(self._pending_snapshot)
            if len(self._undo_stack) > self.history_limit:
                self._undo_stack.pop(0)
            self._redo_stack.clear()
        self._pending_snapshot = None
        self._mutated = False

    def clear_history(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._pending_snapshot = None
        self._mutated = False

    def undo(self) -> bool:
        self.commit_action()
        if not self._undo_stack:
            return False
        self._redo_stack.append(self._snapshot())
        self._restore(self._undo_stack.pop())
        self._pending_snapshot = None
        self._mutated = False
        return True

    def redo(self) -> bool:
        self.commit_action()
        if not self._redo_stack:
            return False
        self._undo_stack.append(self._snapshot())
        self._restore(self._redo_stack.pop())
        self._pending_snapshot = None
        self._mutated = False
        return True

    # -------------------------------
    # VENTANA SELECCION
    #--------------------------------

    def select_by_rectangle(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        mode: str = "window",
        action: str = "replace",
    ) -> int:
        """
        Selecciona entidades dentro de un rectángulo.
        
        Args:
            min_x, min_y, max_x, max_y: Coordenadas del rectángulo (mundo)
            mode: "window" (todo dentro) o "crossing" (toca el rectángulo)
            action: "replace", "add", "remove"
        
        Returns:
            Número de entidades seleccionadas/deseleccionadas
        """
        matching_ids = []
        
        for entity in self.entities:
            bbox = self._get_entity_bbox(entity)
            if bbox is None:
                continue
            
            ent_min_x, ent_min_y, ent_max_x, ent_max_y = bbox
            
            if mode == "window":
                # Window: toda la entidad debe estar dentro
                if (ent_min_x >= min_x - EPS and ent_max_x <= max_x + EPS and
                    ent_min_y >= min_y - EPS and ent_max_y <= max_y + EPS):
                    matching_ids.append(entity.id)
            else:
                # Crossing: la entidad debe tocar el rectángulo
                if (ent_max_x >= min_x - EPS and ent_min_x <= max_x + EPS and
                    ent_max_y >= min_y - EPS and ent_min_y <= max_y + EPS):
                    matching_ids.append(entity.id)

        # ← delega la aplicación de la acción (sin duplicar lógica)
        return self._apply_selection_action(matching_ids, action)

    def _get_entity_bbox(self, entity):
        """
        Calcula el bounding box de una entidad en coordenadas de mundo.
        
        Returns:
            (min_x, min_y, max_x, max_y) o None si no se puede calcular
        """
        if entity.kind == "line":
            start = entity.data["start"]
            end = entity.data["end"]
            return (
                min(start.x, end.x),
                min(start.y, end.y),
                max(start.x, end.x),
                max(start.y, end.y),
            )
        
        elif entity.kind in ("polyline", "polygon"):
            points = entity.data["points"]
            if not points:
                return None
            xs = [p.x for p in points]
            ys = [p.y for p in points]
            return (min(xs), min(ys), max(xs), max(ys))
        
        elif entity.kind == "circle":
            center = entity.data["center"]
            radius = entity.data["radius"]
            return (
                center.x - radius,
                center.y - radius,
                center.x + radius,
                center.y + radius,
            )
        
        elif entity.kind == "arc":
            center = entity.data["center"]
            radius = entity.data["radius"]
            return (
                center.x - radius,
                center.y - radius,
                center.x + radius,
                center.y + radius,
            )
        
        elif entity.kind == "ellipse":
            center = entity.data["center"]
            rx = float(entity.data["radius_x"])
            ry = float(entity.data["radius_y"])
            return (
                center.x - rx,
                center.y - ry,
                center.x + rx,
                center.y + ry,
            )

        elif entity.kind == "text":
            from .text_layout import text_block_size
            d = entity.data
            c, h = d["position"], d["height"]
            w, total = text_block_size(d["content"], h)
            return (c.x - w / 2, c.y - total / 2, c.x + w / 2, c.y + total / 2)

        elif entity.kind == "dimension":
            from .dimension import dimension_points
            pts = dimension_points(entity.data)
            xs = [p.x for p in pts]
            ys = [p.y for p in pts]
            return (min(xs), 
                    min(ys), 
                    max(xs), 
                    max(ys),
            )

        elif entity.kind == "spline":
            from .spline import eval_cubic_spline
            # bbox sobre la curva evaluada (más preciso que el polígono de control)
            pts = eval_cubic_spline(
                entity.data["points"],
                samples_per_segment=10,
                closed=entity.data.get("closed", False),
            )
            xs = [p.x for p in pts]
            ys = [p.y for p in pts]
            return (min(xs), min(ys), max(xs), max(ys))
        
        return None

    def select_by_polygon(self, poly, mode="window", action="replace") -> int:
        """
        Selecciona entidades dentro de (o que tocan) un polígono.
        """
        from ..geometry import bbox_vs_polygon

        matching = []
        for entity in self.entities:
            bbox = self._get_entity_bbox(entity)
            if bbox is None:
                continue
            if bbox_vs_polygon(bbox, poly, mode):
                matching.append(entity.id)

        return self._apply_selection_action(matching, action)

    def _apply_selection_action(self, matching_ids, action) -> int:
        """
        Aplica una acción de selección (replace/add/remove) sobre una lista de IDs.
        
        Único lugar donde vive esta lógica: lo usan select_by_rectangle,
        select_by_polygon y cualquier selección futura.
        
        Returns:
            Número de entidades afectadas
        """
        count = 0
        if action == "replace":
            self.clear_selection()
            for eid in matching_ids:
                self.toggle_selection(eid)
                count += 1

        elif action == "add":
            for eid in matching_ids:
                e = self.get_entity_by_id(eid)
                if e and not e.selected:
                    self.toggle_selection(eid)
                    count += 1

        elif action == "remove":
            for eid in matching_ids:
                e = self.get_entity_by_id(eid)
                if e and e.selected:
                    self.toggle_selection(eid)
                    count += 1

        return count


    # --------------------------------------------
    # AÑADIR / BORRAR VERTICES
    # --------------------------------------------

    def add_vertex(self, entity_id: int, index: int, point: Point):
        """
        Inserta un vértice en el segmento `index` (entre points[index] y
        points[index+1]) de una polilínea o polígono.
        
        Args:
            entity_id: ID de la entidad
            index: Índice del segmento (0 = entre points[0] y points[1])
            point: Coordenadas del nuevo vértice
        
        Returns:
            (bool, str): (éxito, mensaje)
        """
        entity = self.get_entity_by_id(entity_id)
        if entity is None:
            return False, "Entidad no encontrada."
        if entity.kind not in ("polyline", "polygon"):
            return False, "Solo polilíneas y polígonos tienen vértices."

        points = entity.data["points"]
        if index < 0 or index >= len(points):
            return False, "Índice de segmento fuera de rango."

        points.insert(index + 1, point)
        self.notify_change()
        return True, "Vértice añadido."


    def remove_vertex(self, entity_id: int, index: int):
        """
        Elimina el vértice `index` de una polilínea o polígono.
        Respeta el mínimo de puntos (2 polilínea, 3 polígono).
        
        Args:
            entity_id: ID de la entidad
            index: Índice del vértice a eliminar
        
        Returns:
            (bool, str): (éxito, mensaje)
        """
        entity = self.get_entity_by_id(entity_id)
        if entity is None:
            return False, "Entidad no encontrada."
        if entity.kind not in ("polyline", "polygon"):
            return False, "Solo polilíneas y polígonos tienen vértices."

        points = entity.data["points"]
        min_points = 3 if entity.kind == "polygon" else 2

        if len(points) <= min_points:
            return False, f"Un {entity.kind} necesita al menos {min_points} vértices."
        if index < 0 or index >= len(points):
            return False, "Índice de vértice fuera de rango."

        del points[index]
        self.notify_change()
        return True, "Vértice eliminado."

    # --------------------------------
    # LAYER PANEL
    # --------------------------------

    def toggle_layer_visible(self, name:str)-> bool:
        layer = self.get_layer(name)
        if layer is None:
            return False
        layer.visible = not layer.visible
        if not layer.visible:
            for e in self.entities:               # al apagar, deselecciona
                if e.layer == name and e.selected:
                    e.selected = False
        self.notify_change()
        return True

    def toggle_layer_locked(self, name:str)-> bool:
        layer = self.get_layer(name)
        if layer is None:
            return False
        layer.locked = not layer.locked
        self.notify_change()
        return True

    def set_layer_color(self, name: str, color: str) -> bool:
        layer = self.get_layer(name)
        if layer is None:
            return False
        layer.color = color
        self.notify_change()
        return True

    # -----------------------------------
    # LEER Y EDITAR PROPIEDADES
    # -----------------------------------

    def get_entity_properties(self, entity_id: int):
        """Devuelve [(campo, valor_mostrable)] de una entidad."""
        entity = self.get_entity_by_id(entity_id)
        if entity is None:
            return []

        def pt(p):
            return f"{p.x:g}, {p.y:g}"

        d = entity.data
        props = [("id", entity.id), ("tipo", entity.kind), ("capa", entity.layer)]

        if entity.kind == "line":
            props += [("start", pt(d["start"])), ("end", pt(d["end"]))]
        elif entity.kind in ("polyline", "polygon"):
            props += [("vértices", len(d["points"]))]
        elif entity.kind == "circle":
            props += [("center", pt(d["center"])), ("radius", round(d["radius"], 3))]
        elif entity.kind == "arc":
            props += [
                ("center", pt(d["center"])), ("radius", round(d["radius"], 3)),
                ("start_angle", round(d["start_angle"], 2)), ("extent", round(d["extent"], 2)),
            ]
        elif entity.kind == "ellipse":
            props += [
                ("center", pt(d["center"])), ("radius_x", round(d["radius_x"], 3)),
                ("radius_y", round(d["radius_y"], 3)), ("rotation", round(d.get("rotation", 0), 2)),
            ]
        elif entity.kind == "text":
            props += [
                ("position", pt(d["position"])), ("height", round(d["height"], 3)),
                ("content", d["content"]),
            ]
        elif entity.kind == "dimension":
            props += [
                ("offset", round(d.get("offset", 10.0), 3)),
                ("text_height", round(d.get("text_height", 2.5), 3)),
                ("asociada", "SI" if d.get("assoc_entity_id") else "no"),
            ]
        elif entity.kind == "spline":
            props += [
                ("puntos", len(d["points"])),
                ("closed", "SI" if d.get("closed") else "no"),
            ]
        
        return props


    def set_entity_property(self, entity_id: int, field: str, value):
        """Edita un campo de una entidad. Returns (bool, str)."""
        from . import parse_point, parse_number    # evita importacion circular
        
        entity = self.get_entity_by_id(entity_id)
        if entity is None:
            return False, "Entidad no encontrada."

        if field == "capa":
            if self.get_layer(str(value)) is None:
                return False, f"Capa inexistente: {value}"
            entity.layer = str(value)
            self.notify_change()
            return True, "OK"

        data = entity.data
        if field not in data:
            return False, f"Campo no editable: {field}"

        current = data[field]

        if isinstance(current, Point):
            try:
                data[field] = parse_point(str(value), None)
            except ValueError:
                return False, "Punto no válido (usa x,y)."

        elif isinstance(current, float):
            try:
                num = parse_number(str(value))
            except ValueError:
                return False, "Número no válido."
            if field in ("radius", "height", "radius_x", "radius_y") and num <= 0:
                return False, "Debe ser mayor que cero."
            data[field] = float(num)

        elif isinstance(current, str):
            data[field] = str(value).replace("\\n", "\n")

        else:
            return False, f"Campo no editable: {field}"

        self.notify_change()
        return True, "OK" 

    # ----------------------------------------------------
    # Matrices (arrays)
    # ----------------------------------------------------
    def _clone_entity(self, entity):
        """Duplica una entidad conservando capa. Devuelve la nueva."""
        data = copy.deepcopy(entity.data)
        new = self.add_entity(entity.kind, data)
        new.layer = entity.layer
        return new

    def _map_entity_points(self, entity, fn):
        """Aplica fn(Point)->Point a todos los puntos de definición."""
        d = entity.data
        k = entity.kind
        if k == "line":
            d["start"] = fn(d["start"])
            d["end"] = fn(d["end"])
        elif k in ("polyline", "polygon", "spline"):
            d["points"] = [fn(p) for p in d["points"]]
        elif k in ("circle", "arc", "ellipse"):
            d["center"] = fn(d["center"])
        elif k == "text":
            d["position"] = fn(d["position"])
        elif k == "dimension":
            for key in ("p1", "p2", "center", "p", "vertex"):
                if key in d:
                    d[key] = fn(d[key])

    def array_rectangular(self, ids, rows, cols, dx, dy):
        """Crea una matriz rectangular de la selección. Devuelve ids nuevos."""
        new_ids = []
        originals = [self.get_entity_by_id(i) for i in ids]
        originals = [e for e in originals if e is not None]
        for r in range(rows):
            for c in range(cols):
                if r == 0 and c == 0:
                    continue
                for orig in originals:
                    copy = self._clone_entity(orig)
                    self._map_entity_points(
                        copy,
                        lambda p, ox=c * dx, oy=r * dy:
                            Point(p.x + ox, p.y + oy),
                    )
                    new_ids.append(copy.id)
        self.notify_change()
        return new_ids

    def array_polar(self, ids, center, count, total_angle=360.0):
        """Crea una matriz polar de la selección. Devuelve ids nuevos."""
        new_ids = []
        originals = [self.get_entity_by_id(i) for i in ids]
        originals = [e for e in originals if e is not None]
        step = total_angle / max(count, 1)
        for i in range(1, count):
            ang = math.radians(step * i)
            ca, sa = math.cos(ang), math.sin(ang)
            for orig in originals:
                copy = self._clone_entity(orig)

                def rot(p):
                    dx, dy = p.x - center.x, p.y - center.y
                    return Point(center.x + dx * ca - dy * sa,
                                 center.y + dx * sa + dy * ca)

                self._map_entity_points(copy, rot)
                # Orientación propia de arcos y elipses
                if copy.kind == "arc":
                    copy.data["start_angle"] = (
                        copy.data["start_angle"] + math.degrees(ang)
                    ) % 360.0
                elif copy.kind == "ellipse":
                    copy.data["rotation"] = (
                        copy.data.get("rotation", 0.0) + math.degrees(ang)
                    ) % 360.0
                new_ids.append(copy.id)
        self.notify_change()
        return new_ids

    # ----------------------------------------------------
    # Bloques (nivel 1: grupos)
    # ----------------------------------------------------
    def make_block(self, ids, name):
        """Agrupa las entidades dadas en un bloque. Devuelve el block_id."""
        ids = [i for i in ids if self.get_entity_by_id(i) is not None]
        if not ids:
            return None
        bid = self._next_block_id
        self._next_block_id += 1
        self.block_names[bid] = name
        for i in ids:
            self.get_entity_by_id(i).block_id = bid
        self.notify_change()
        return bid

    def block_siblings(self, entity_id):
        """Ids de todas las entidades del mismo bloque (incluida la dada)."""
        e = self.get_entity_by_id(entity_id)
        bid = getattr(e, "block_id", None) if e is not None else None
        if bid is None:
            return [entity_id]
        return [o.id for o in self.entities
                if getattr(o, "block_id", None) == bid]

    def explode_block(self, ids):
        """Rompe el bloque de las entidades dadas. Devuelve nº bloques rotos."""
        broken = 0
        done = set()
        for i in ids:
            e = self.get_entity_by_id(i)
            bid = getattr(e, "block_id", None) if e is not None else None
            if bid is None or bid in done:
                continue
            done.add(bid)
            for o in self.entities:
                if getattr(o, "block_id", None) == bid:
                    o.block_id = None
            self.block_names.pop(bid, None)
            broken += 1
        if broken:
            self.notify_change()
        return broken

    def _expand_blocks(self, ids):
        """Amplía una lista de ids con sus hermanos de bloque."""
        out, seen = [], set()
        for i in ids:
            for s in self.block_siblings(i):
                if s not in seen:
                    seen.add(s)
                    out.append(s)
        return out

