import pytest

pytest.importorskip("PIL")

from PIL import Image

from tkcad.core import Document, Point
from tkcad.core.png_export import export_png


def test_export_png_vacio_falla(tmp_path):
    ok, msg = export_png([], lambda n: None, tmp_path / "x.png")
    assert not ok


def test_export_png_crea_archivo(tmp_path):
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.add_circle(Point(5, 5), 2)

    path = tmp_path / "out.png"
    ok, msg = export_png(doc.entities, lambda n: "white", path)
    assert ok, msg

    img = Image.open(path)
    assert img.size == (800, 600)
    assert img.format == "PNG"


def test_export_png_dibuja_pixeles(tmp_path):
    doc = Document()
    doc.add_line(Point(0, 0), Point(100, 0))

    path = tmp_path / "linea.png"
    ok, msg = export_png(doc.entities, lambda n: "white", path,
                         background="black")
    assert ok, msg

    img = Image.open(path).convert("RGB")
    # Iterar sobre los píxeles sin usar getdata()
    colors = set()
    for y in range(img.height):
        for x in range(img.width):
            colors.add(img.getpixel((x, y)))
            
    assert (255, 255, 255) in colors   # la línea blanca
    assert (0, 0, 0) in colors         # el fondo negro

def test_export_png_spline(tmp_path):
    doc = Document()
    doc.add_spline([Point(0, 0), Point(10, 5), Point(20, 0)])

    path = tmp_path / "spline.png"
    ok, msg = export_png(doc.entities, lambda n: "white", path)
    assert ok, msg
    assert Image.open(path).size == (800, 600)

