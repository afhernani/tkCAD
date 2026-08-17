"""Utilidades de polígonos para selección."""

from .intersection import line_line_intersection
from ..core import Point


def point_in_polygon(p: Point, poly) -> bool:
    """True si el punto p está dentro del polígono (ray casting)."""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        a = poly[i]
        b = poly[j]
        if (a.y > p.y) != (b.y > p.y):
            xint = (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x
            if p.x < xint:
                inside = not inside
        j = i
    return inside


def bbox_vs_polygon(bbox, poly, mode: str) -> bool:
    """
    Evalúa el bounding box de una entidad contra un polígono.
    
    mode="window": el bbox debe estar completamente dentro.
    mode="crossing": el bbox debe tocar o cruzar el polígono.
    """
    min_x, min_y, max_x, max_y = bbox
    corners = [
        Point(min_x, min_y), Point(max_x, min_y),
        Point(max_x, max_y), Point(min_x, max_y),
    ]
    rect_edges = [
        (corners[0], corners[1]), (corners[1], corners[2]),
        (corners[2], corners[3]), (corners[3], corners[0]),
    ]
    poly_edges = [
        (poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))
    ]

    corners_in = [point_in_polygon(c, poly) for c in corners]
    edge_cross = any(
        line_line_intersection(a, b, c, d) is not None
        for (a, b) in rect_edges
        for (c, d) in poly_edges
    )
    poly_in_rect = any(
        min_x <= v.x <= max_x and min_y <= v.y <= max_y for v in poly
    )

    if mode == "window":
        return all(corners_in) and not edge_cross
    return any(corners_in) or edge_cross or poly_in_rect