from tkcad.core import Document, Point
from tkcad.core.svg_export import export_svg


def test_export_svg_vacio_falla():
    ok, msg = export_svg([], lambda n: None, "x.svg")
    assert not ok


def test_export_svg_contiene_elementos(tmp_path):
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.add_circle(Point(5, 5), 2)

    path = tmp_path / "out.svg"
    ok, msg = export_svg(doc.entities, lambda n: "white", path)
    assert ok, msg

    content = path.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "<line" in content
    assert "<circle" in content


def test_export_svg_polilinea_y_texto(tmp_path):
    doc = Document()
    doc.add_polyline([Point(0, 0), Point(5, 5), Point(10, 0)])
    doc.add_text(Point(5, 8), 2, "HOLA")

    path = tmp_path / "p.svg"
    ok, msg = export_svg(doc.entities, lambda n: "white", path)
    assert ok, msg

    content = path.read_text(encoding="utf-8")
    assert "<polyline" in content
    assert "HOLA" in content


def test_export_svg_cota(tmp_path):
    doc = Document()
    doc.add_dimension("linear_h", p1=Point(0, 0), p2=Point(100, 0), offset=15)

    path = tmp_path / "cota.svg"
    ok, msg = export_svg(doc.entities, lambda n: "white", path)
    assert ok, msg

    content = path.read_text(encoding="utf-8")
    assert "100.00" in content

def test_export_svg_spline(tmp_path):
    doc = Document()
    doc.add_spline([Point(0, 0), Point(10, 5), Point(20, 0)])

    path = tmp_path / "spline.svg"
    ok, msg = export_svg(doc.entities, lambda n: "white", path)
    assert ok, msg
    assert "<polyline" in path.read_text(encoding="utf-8")