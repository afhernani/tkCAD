import pytest

ezdxf = pytest.importorskip("ezdxf")   # salta si ezdxf no está instalado

from tkcad.core import Document, Point
from tkcad.core.dxf_export import export_dxf


def test_export_dxf_crea_archivo(tmp_path):
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.add_circle(Point(5, 5), 2.0)

    path = tmp_path / "out.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg
    assert path.exists()

    read = ezdxf.readfile(str(path))
    kinds = {e.dxftype() for e in read.modelspace()}
    assert "LINE" in kinds
    assert "CIRCLE" in kinds


def test_export_dxf_polilinea_y_arco(tmp_path):
    doc = Document()
    doc.add_polyline([Point(0, 0), Point(5, 0), Point(5, 5)])
    doc.add_arc(Point(0, 0), 5.0, 0.0, 90.0)

    path = tmp_path / "out2.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg

    read = ezdxf.readfile(str(path))
    kinds = {e.dxftype() for e in read.modelspace()}
    assert "LWPOLYLINE" in kinds
    assert "ARC" in kinds


def test_export_dxf_cota_lineal(tmp_path):
    doc = Document()
    doc.add_dimension("linear_h", p1=Point(0, 0), p2=Point(100, 0), offset=15)

    path = tmp_path / "cota.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg

    read = ezdxf.readfile(str(path))
    kinds = {e.dxftype() for e in read.modelspace()}
    assert "DIMENSION" in kinds


def test_export_dxf_cota_radio(tmp_path):
    doc = Document()
    doc.add_dimension("radius", center=Point(0, 0), p=Point(5, 0))

    path = tmp_path / "radio.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg

    read = ezdxf.readfile(str(path))
    kinds = {e.dxftype() for e in read.modelspace()}
    assert "DIMENSION" in kinds

def test_export_dxf_spline(tmp_path):
    doc = Document()
    doc.add_spline([Point(0, 0), Point(10, 5), Point(20, 0)])

    path = tmp_path / "spline.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg

    read = ezdxf.readfile(str(path))
    kinds = {e.dxftype() for e in read.modelspace()}
    assert "SPLINE" in kinds

