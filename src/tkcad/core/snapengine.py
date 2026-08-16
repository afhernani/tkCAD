import math
from typing import List, Optional, Tuple

from .point import Point
from .types import ALL_SNAP_MODES
from ..geometry import line_line_intersection


class SnapEngine:
    """Motor de snaps de tkCAD.
    
    Calcula puntos ajustados (ENDPOINT, MIDPOINT, INTERSECTION,
    ORTHO, GRID...) sobre una lista de entidades que recibe por
    parámetro. No conoce la UI ni redraw: solo geometría y estado.
    """

    def __init__(self):
        self.snap_modes = {"GRID", "ENDPOINT", "MIDPOINT"}
        self.grid_size = 10.0
        self.snap_tolerance_pixels = 8

    # --------------------------------------------------------
    # Configuración
    # --------------------------------------------------------
    def get_snap_modes(self) -> List[str]:
        return sorted(self.snap_modes)

    def toggle_snap_mode(self, mode: str) -> bool:
        if mode in self.snap_modes:
            self.snap_modes.remove(mode)
            return False
        else:
            self.snap_modes.add(mode)
            return True

    def set_all_snap_modes(self):
        self.snap_modes = set(ALL_SNAP_MODES)

    def clear_snap_modes(self):
        self.snap_modes = set()

    def set_grid_size(self, size: float):
        if size > 1e-9:
            self.grid_size = float(size)

    # --------------------------------------------------------
    # Cálculo principal de snap
    # --------------------------------------------------------
    def snap_point(
        self,
        entities,
        p: Point,
        base_point: Optional[Point] = None,
        ignore_entity_id=None,
        scale: float = 1.0,
    ) -> Tuple[Point, Optional[str]]:
        """
        Devuelve:
            Point, snap_type
        
        snap_type puede ser:
            "POINT", "ENDPOINT", "MIDPOINT", "INTERSECTION",
            "ORTHO", "GRID", None
        """
        if not self.snap_modes:
            return p, None

        candidates = []

        if "POINT" in self.snap_modes:
            candidates.extend(
                self._snap_points_near(entities, p, ignore_entity_id, scale)
            )
        if "ENDPOINT" in self.snap_modes:
            candidates.extend(
                self._snap_endpoints_near(entities, p, ignore_entity_id, scale)
            )
        if "MIDPOINT" in self.snap_modes:
            candidates.extend(
                self._snap_midpoints_near(entities, p, ignore_entity_id, scale)
            )
        if "INTERSECTION" in self.snap_modes:
            candidates.extend(
                self._snap_intersections_near(entities, p, ignore_entity_id, scale)
            )

        best = self._nearest_snap_candidate(candidates, p, scale)
        if best is not None:
            return best

        if "ORTHO" in self.snap_modes and base_point is not None:
            return self._apply_ortho(p, base_point), "ORTHO"

        if "GRID" in self.snap_modes:
            return self._snap_to_grid(p), "GRID"

        return p, None

    # --------------------------------------------------------
    # Helpers internos
    # --------------------------------------------------------
    def _add_snap_candidate(
        self,
        candidates,
        point: Point,
        target: Point,
        tolerance: float,
        kind: str,
    ):
        distance = math.hypot(
            point.x - target.x,
            point.y - target.y,
        )
        if distance <= tolerance:
            candidates.append((point, kind))

    def _nearest_snap_candidate(self, candidates, target: Point, scale: float = 1.0):
        tolerance = self.snap_tolerance_pixels/scale
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

    # --------------------------------------------------------
    # Snaps a puntos específicos
    # --------------------------------------------------------
    def _snap_points_near(self, entities, p: Point, ignore_entity_id=None, scale: float = 1.0):
        """Snap a vértices, centros de círculo/arco/elipse."""
        tolerance = self.snap_tolerance_pixels / scale
        candidates = []

        for entity in entities:
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
                self._add_snap_candidate(candidates, center, p, tolerance, "POINT")
                for point in self._ellipse_axis_points(entity):
                    self._add_snap_candidate(candidates, point, p, tolerance, "POINT")

        return candidates

    def _snap_endpoints_near(self, entities, p: Point, ignore_entity_id=None, scale: float = 1.0):
        """Snap a extremos de líneas, vértices, extremos de arco, ejes de elipse."""
        tolerance = self.snap_tolerance_pixels / scale
        candidates = []

        for entity in entities:
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
                    self._add_snap_candidate(candidates, point, p, tolerance, "ENDPOINT")

        return candidates

    def _snap_midpoints_near(self, entities, p: Point, ignore_entity_id=None, scale: float = 1.0):
        """Snap a puntos medios de líneas, segmentos de polilínea/polígono, arcos."""
        tolerance = self.snap_tolerance_pixels / scale
        candidates = []

        for entity in entities:
            if entity.id == ignore_entity_id:
                continue

            if entity.kind == "line":
                start = entity.data["start"]
                end = entity.data["end"]
                midpoint = Point(
                    (start.x + end.x) / 2.0,
                    (start.y + end.y) / 2.0,
                )
                self._add_snap_candidate(candidates, midpoint, p, tolerance, "MIDPOINT")

            elif entity.kind in ("polyline", "polygon"):
                points = entity.data["points"]
                if len(points) >= 2:
                    segment_count = len(points) - 1 if entity.kind == "polyline" else len(points)
                    for i in range(segment_count):
                        a = points[i]
                        b = points[(i + 1) % len(points)]
                        midpoint = Point(
                            (a.x + b.x) / 2.0,
                            (a.y + b.y) / 2.0,
                        )
                        self._add_snap_candidate(candidates, midpoint, p, tolerance, "MIDPOINT")

            elif entity.kind == "arc":
                start_angle = entity.data["start_angle"]
                extent = entity.data["extent"]
                mid_angle = start_angle + extent / 2.0
                midpoint = self._arc_point_at_angle(entity, mid_angle)
                self._add_snap_candidate(candidates, midpoint, p, tolerance, "MIDPOINT")

        return candidates

    def _snap_intersections_near(self, entities, p: Point, ignore_entity_id=None, scale: float = 1.0):
        """Snap a intersecciones entre segmentos lineales."""
        tolerance = self.snap_tolerance_pixels / scale
        candidates = []

        segments = self._linear_segments(entities, ignore_entity_id)

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

    def _linear_segments(self, entities, ignore_entity_id=None):
        segments = []

        for entity in entities:
            if entity.id == ignore_entity_id:
                continue

            if entity.kind == "line":
                segments.append((entity.data["start"], entity.data["end"]))

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

    def _segment_bbox_contains_point(
        self, a: Point, b: Point, p: Point, tolerance: float
    ) -> bool:
        min_x = min(a.x, b.x) - tolerance
        max_x = max(a.x, b.x) + tolerance
        min_y = min(a.y, b.y) - tolerance
        max_y = max(a.y, b.y) + tolerance
        return min_x <= p.x <= max_x and min_y <= p.y <= max_y

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

    def _ellipse_axis_points(self, entity):
        """Calcula los puntos de los ejes de la elipse."""
        center = entity.data["center"]
        rx = float(entity.data["radius_x"])
        ry = float(entity.data["radius_y"])
        rot = math.radians(entity.data.get("rotation", 0.0))
        cos_r = math.cos(rot)
        sin_r = math.sin(rot)

        x_pos = Point(center.x + rx * cos_r, center.y + rx * sin_r)
        x_neg = Point(center.x - rx * cos_r, center.y - rx * sin_r)

        y_rot = rot + math.pi / 2.0
        y_cos = math.cos(y_rot)
        y_sin = math.sin(y_rot)
        y_pos = Point(center.x + ry * y_cos, center.y + ry * y_sin)
        y_neg = Point(center.x - ry * y_cos, center.y - ry * y_sin)

        return [x_pos, x_neg, y_pos, y_neg]