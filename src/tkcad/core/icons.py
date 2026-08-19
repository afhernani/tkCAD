"""Generación de iconos de la toolbar con Pillow (sin assets externos)."""

import math

from PIL import Image, ImageDraw

SIZE = 24
BG = (52, 52, 58, 255)          # gris oscuro de fondo

# Paleta viva
CYAN = (0, 229, 255, 255)
YELLOW = (255, 214, 0, 255)
MAGENTA = (255, 77, 204, 255)
ORANGE = (255, 145, 0, 255)
GREEN = (94, 255, 114, 255)
RED = (255, 77, 77, 255)
VIOLET = (178, 102, 255, 255)
WHITE = (240, 240, 240, 255)

TOOLBAR_COMMANDS = [
    ("LINEA", "Línea"),
    ("POLILINEA", "Polilínea"),
    ("CIRCULO", "Círculo"),
    ("ARCO", "Arco"),
    ("ELIPSE", "Elipse"),
    ("SPLINE", "Spline"),
    ("TEXTO", "Texto"),
    ("COTA", "Cota"),
    ("SELECCIONAR", "Seleccionar"),
    ("MOVER", "Mover"),
    ("BORRAR", "Borrar selección"),
    ("ZOOM", "Zoom"),
    ("DESHACER", "Deshacer"),
    ("REHACER", "Rehacer"),
    ("GUARDAR", "Guardar"),
    ("ABRIR", "Abrir"),
    ("EXPORTAR", "Exportar DXF"),
]


def _new():
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    return img, ImageDraw.Draw(img)


def _icon_linea():
    img, d = _new()
    d.line([(5, 19), (19, 5)], fill=CYAN, width=2)
    d.rectangle([3, 17, 7, 21], outline=CYAN)
    d.rectangle([17, 3, 21, 7], outline=CYAN)
    return img


def _icon_polilinea():
    img, d = _new()
    d.line([(4, 18), (10, 8), (15, 14), (20, 6)], fill=YELLOW, width=2)
    return img


def _icon_circulo():
    img, d = _new()
    d.ellipse([4, 4, 20, 20], outline=MAGENTA, width=2)
    return img


def _icon_arco():
    img, d = _new()
    d.arc([4, 4, 20, 20], start=200, end=340, fill=ORANGE, width=2)
    return img


def _icon_elipse():
    img, d = _new()
    d.ellipse([3, 7, 21, 17], outline=VIOLET, width=2)
    return img


def _icon_spline():
    img, d = _new()
    pts = [(4 + i, 12 + 6 * math.sin(i / 3)) for i in range(17)]
    d.line(pts, fill=GREEN, width=2)
    return img


def _icon_texto():
    img, d = _new()
    d.text((8, 6), "A", fill=WHITE)
    return img


def _icon_cota():
    img, d = _new()
    d.line([(4, 12), (20, 12)], fill=ORANGE, width=2)
    d.line([(4, 6), (4, 18)], fill=ORANGE, width=1)
    d.line([(20, 6), (20, 18)], fill=ORANGE, width=1)
    return img


def _icon_seleccionar():
    img, d = _new()
    d.polygon([(6, 4), (6, 18), (10, 14), (13, 20), (15, 19),
               (12, 13), (17, 13)], fill=WHITE)
    return img


def _icon_mover():
    img, d = _new()
    d.line([(12, 4), (12, 20)], fill=CYAN, width=2)
    d.line([(4, 12), (20, 12)], fill=CYAN, width=2)
    d.polygon([(12, 2), (9, 6), (15, 6)], fill=CYAN)
    d.polygon([(12, 22), (9, 18), (15, 18)], fill=CYAN)
    d.polygon([(2, 12), (6, 9), (6, 15)], fill=CYAN)
    d.polygon([(22, 12), (18, 9), (18, 15)], fill=CYAN)
    return img


def _icon_borrar():
    img, d = _new()
    d.rectangle([6, 8, 18, 20], outline=RED, width=2)
    d.line([(4, 8), (20, 8)], fill=RED, width=2)
    d.line([(10, 4), (14, 4)], fill=RED, width=2)
    return img


def _icon_zoom():
    img, d = _new()
    d.ellipse([4, 4, 16, 16], outline=CYAN, width=2)
    d.line([(14, 14), (20, 20)], fill=CYAN, width=3)
    return img


def _icon_deshacer():
    img, d = _new()
    d.arc([4, 6, 20, 22], start=180, end=360, fill=YELLOW, width=2)
    d.polygon([(4, 4), (1, 9), (7, 9)], fill=YELLOW)
    return img


def _icon_rehacer():
    img, d = _new()
    d.arc([4, 6, 20, 22], start=180, end=360, fill=YELLOW, width=2)
    d.polygon([(20, 4), (17, 9), (23, 9)], fill=YELLOW)
    return img


def _icon_guardar():
    img, d = _new()
    d.rectangle([4, 4, 20, 20], outline=GREEN, width=2)
    d.rectangle([8, 4, 16, 10], outline=GREEN)
    d.rectangle([7, 13, 17, 20], outline=GREEN)
    return img


def _icon_abrir():
    img, d = _new()
    d.polygon([(3, 8), (9, 8), (11, 10), (21, 10), (21, 19), (3, 19)],
              outline=ORANGE)
    return img


def _icon_exportar():
    img, d = _new()
    d.rectangle([4, 10, 20, 20], outline=GREEN, width=2)
    d.line([(12, 14), (12, 3)], fill=GREEN, width=2)
    d.polygon([(12, 2), (8, 7), (16, 7)], fill=GREEN)
    return img


def _icon_default():
    img, d = _new()
    d.rectangle([5, 5, 19, 19], outline=WHITE)
    return img


_DRAWERS = {
    "LINEA": _icon_linea,
    "POLILINEA": _icon_polilinea,
    "CIRCULO": _icon_circulo,
    "ARCO": _icon_arco,
    "ELIPSE": _icon_elipse,
    "SPLINE": _icon_spline,
    "TEXTO": _icon_texto,
    "COTA": _icon_cota,
    "SELECCIONAR": _icon_seleccionar,
    "MOVER": _icon_mover,
    "BORRAR": _icon_borrar,
    "ZOOM": _icon_zoom,
    "DESHACER": _icon_deshacer,
    "REHACER": _icon_rehacer,
    "GUARDAR": _icon_guardar,
    "ABRIR": _icon_abrir,
    "EXPORTAR": _icon_exportar,
}


def build_icon(name: str) -> Image.Image:
    """Devuelve una imagen RGBA 24×24 para el comando dado."""
    return _DRAWERS.get(name, _icon_default)()