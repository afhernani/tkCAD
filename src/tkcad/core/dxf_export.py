"""Exportación de entidades tkCAD a formato DXF (AutoCAD).

Mapea cada entidad del modelo a su equivalente DXF usando ezdxf.
"""

import math
from .dimension import angular_geometry, angular_text_position, dimension_geometry
from .blocks import expand_inserts

def export_dxf(entities, path, block_defs=None):
    """
    Exporta una lista de entidades a un archivo DXF.
    
    Args:
        entities: Lista de Entity del modelo
        path: Ruta de destino (Path o str)
    
    Returns:
        (bool, str): (éxito, mensaje)
    """
    if block_defs:
        entities = expand_inserts(entities, block_defs)
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
        content = data["content"]
        if "\n" in content:
            # Multilinea: usar MTEXT
            msp.add_mtext(
                content.replace("\n", "\\P"),
                dxfattribs={
                    "insert": (data["position"].x, data["position"].y, 0),
                    "char_height": data["height"],
                    "attachment_point": 8,   # Middle Bottom-Center
                },
            )
        else:
            # Texto simple
            msp.add_text(
                content,
                height=data["height"],
                dxfattribs={
                    "insert": (data["position"].x, data["position"].y, 0),
                },
            )

    elif kind == "dimension":
        if data["dim_type"] == "angular":
            e = _add_angular(msp, data)
        else:
            e = _add_dimension(msp, data)   # o como lo tengas ahora

    elif kind == "spline":
        e = _add_spline(msp, data)

    else:
        return False

    # Mapear capa tkCAD → capa DXF (opcional, no rompe si falla)
    try:
        _ensure_layer(doc, entity.layer)
        e.dxf.layer = entity.layer
    except Exception:
        pass

    return True

def _add_angular(msp, data):
    g = angular_geometry(data)
    v = g["vertex"]
    try:
        return msp.add_angular_dim_cra(
            center=(v.x, v.y, 0),
            radius=g["radius"],
            start_angle=g["a1"],
            end_angle=g["a1"] + g["extent"],
        )
    except Exception:
        # Respaldo: geometría (2 líneas + arco + texto)
        for endp in (g["arc_start"], g["arc_end"]):
            msp.add_line((v.x, v.y, 0), (endp.x, endp.y, 0))
        msp.add_arc(
            center=(v.x, v.y, 0),
            radius=g["radius"],
            start_angle=g["a1"],
            end_angle=g["a1"] + g["extent"],
        )
        tp = angular_text_position(data)
        msp.add_text(f"{g['value']:.1f}°", height=data.get("text_height", 2.5))\
           .set_placement((tp.x, tp.y, 0))
        return None

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

# -----------------------------------
# AYUDAS COTAS
# -----------------------------------

def _add_dimension(msp, data):
    """Convierte una cota tkCAD en un DIMENSION de DXF."""
    g = dimension_geometry(data)
    base = (g["text_point"].x, g["text_point"].y, 0)
    t = data["dim_type"]

    if t == "linear_h":
        dim = msp.add_linear_dim(
            base=base,
            p1=(data["p1"].x, data["p1"].y, 0),
            p2=(data["p2"].x, data["p2"].y, 0),
            angle=0,
        )
    elif t == "linear_v":
        dim = msp.add_linear_dim(
            base=base,
            p1=(data["p1"].x, data["p1"].y, 0),
            p2=(data["p2"].x, data["p2"].y, 0),
            angle=90,
        )
    elif t == "aligned":
        dim = msp.add_aligned_dim(
            base=base,
            p1=(data["p1"].x, data["p1"].y, 0),
            p2=(data["p2"].x, data["p2"].y, 0),
        )
    else:  # radius / diameter
        dim = _add_radius_dim(msp, data["center"], data["p"])

    dim.render()
    return dim


def _add_radius_dim(msp, center, p):
    """Cota de radio, compatible con las dos firmas de ezdxf."""
    try:
        return msp.add_radius_dim(
            center=(center.x, center.y, 0),
            mpoint=(p.x, p.y, 0),
        )
    except TypeError:
        r = math.hypot(p.x - center.x, p.y - center.y)
        ang = math.degrees(math.atan2(p.y - center.y, p.x - center.x))
        return msp.add_radius_dim(
            center=(center.x, center.y, 0),
            radius=r,
            angle=ang,
        )

# ---------------------------
# AYUDA AÑADIR CURVA SPLINE
# ---------------------------

def _add_spline(msp, data):
    """Convierte una spline tkCAD en un SPLINE de DXF."""
    pts = list(data["points"])
    if data.get("closed", False) and len(pts) >= 3:
        pts = pts + [pts[0]]
    coords = [(p.x, p.y, 0) for p in pts]

    spline = msp.add_spline()

    # ezdxf moderno: fit_points es un atributo asignable
    try:
        spline.fit_points = coords
    except Exception:
        # Respaldo: definir por puntos de control
        spline.control_points = coords
        try:
            spline.set_uniform_knots()
        except Exception:
            pass

    try:
        spline.dxf.degree = 3
    except Exception:
        pass

    return spline

