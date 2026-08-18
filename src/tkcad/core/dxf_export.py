"""Exportación de entidades tkCAD a formato DXF (AutoCAD).

Mapea cada entidad del modelo a su equivalente DXF usando ezdxf.
"""

import math


def export_dxf(entities, path):
    """
    Exporta una lista de entidades a un archivo DXF.
    
    Args:
        entities: Lista de Entity del modelo
        path: Ruta de destino (Path o str)
    
    Returns:
        (bool, str): (éxito, mensaje)
    """
    try:
        import ezdxf
    except ImportError:
        return False, "ezdxf no está instalado. Ejecuta: pixi add ezdxf"

    try:
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        count = 0
        for entity in entities:
            if _add_entity(msp, doc, entity):
                count += 1

        doc.saveas(str(path))
        return True, f"Exportadas {count} entidades a {path}"
    except Exception as ex:
        return False, f"Error al exportar DXF: {ex}"


def _add_entity(msp, doc, entity) -> bool:
    """Añade una entidad al modelspace. Devuelve True si se añadió."""
    kind = entity.kind
    data = entity.data

    if kind == "line":
        e = msp.add_line(
            (data["start"].x, data["start"].y, 0),
            (data["end"].x, data["end"].y, 0),
        )

    elif kind == "polyline":
        pts = [(p.x, p.y) for p in data["points"]]
        e = msp.add_lwpolyline(pts, close=False)

    elif kind == "polygon":
        pts = [(p.x, p.y) for p in data["points"]]
        e = msp.add_lwpolyline(pts, close=True)

    elif kind == "circle":
        e = msp.add_circle(
            (data["center"].x, data["center"].y, 0),
            data["radius"],
        )

    elif kind == "arc":
        e = msp.add_arc(
            (data["center"].x, data["center"].y, 0),
            data["radius"],
            data["start_angle"],
            data["start_angle"] + data["extent"],
        )

    elif kind == "ellipse":
        e = _add_ellipse(msp, data)

    elif kind == "text":
        e = msp.add_text(data["content"], height=data["height"])
        e.set_pos((data["position"].x, data["position"].y))

    else:
        return False

    # Mapear capa tkCAD → capa DXF (opcional, no rompe si falla)
    try:
        _ensure_layer(doc, entity.layer)
        e.dxf.layer = entity.layer
    except Exception:
        pass

    return True


def _add_ellipse(msp, data):
    """Convierte una elipse tkCAD (rx, ry, rotación) a elipse DXF."""
    center = data["center"]
    rx = float(data["radius_x"])
    ry = float(data["radius_y"])
    rot = math.radians(data.get("rotation", 0.0))

    if rx >= ry:
        major = rx
        ratio = ry / rx if rx > 1e-9 else 1.0
        axis = (major * math.cos(rot), major * math.sin(rot), 0)
    else:
        major = ry
        ratio = rx / ry if ry > 1e-9 else 1.0
        rot2 = rot + math.pi / 2
        axis = (major * math.cos(rot2), major * math.sin(rot2), 0)

    return msp.add_ellipse(
        center=(center.x, center.y, 0),
        major_axis=axis,
        ratio=ratio,
    )


def _ensure_layer(doc, name):
    if name and name not in doc.layers:
        doc.layers.add(name)