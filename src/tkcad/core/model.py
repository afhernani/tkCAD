"""Modelo de documento de tkCAD: entidades, creación y selección.

No conoce Tkinter. Cuando algo cambia llama a notify_change(),
que por defecto no hace nada; la aplicación lo sobreescribe
para redibujar.
"""
from typing import List

from .entity import Entity
from .point import Point
from .types import TARGET_KIND_MAP


class Document:
    """El 'plano': entidades y lógica pura de modelo."""

    def __init__(self):
        self.entities: List[Entity] = []
        self.next_entity_id = 1

    def notify_change(self):
        """Hook de cambio: CadApp lo sobreescribe con redraw."""
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
        for entity in self.entities:
            entity.selected = True
        self.notify_change()

    def clear_selection(self):
        for entity in self.entities:
            entity.selected = False
        self.notify_change()

    def select_last(self):
        if self.entities:
            self.entities[-1].selected = True
            self.notify_change()

    def select_kind(self, kind: str):
        for entity in self.entities:
            if entity.kind == kind:
                entity.selected = True
        self.notify_change()

    def toggle_selection(self, entity_id: int, notify: bool = True) -> bool:
        entity = self.get_entity_by_id(entity_id)
        if entity is None:
            return False
        entity.selected = not entity.selected
        if notify:
            self.notify_change()
        return True

    def set_selection_ids(self, ids):
        ids_set = set(ids)
        for entity in self.entities:
            entity.selected = entity.id in ids_set
        self.notify_change()

    def add_selection_ids(self, ids):
        ids_set = set(ids)
        for entity in self.entities:
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
            count = len(self.entities)
            self.entities = []
            self.notify_change()
            return count
        kind = TARGET_KIND_MAP.get(target)
        if kind is None:
            return 0
        count = sum(1 for entity in self.entities if entity.kind == kind)
        if count > 0:
            self.entities = [
                entity for entity in self.entities if entity.kind != kind
            ]
            self.notify_change()
        return count