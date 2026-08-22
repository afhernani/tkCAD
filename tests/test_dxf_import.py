import pytest
from tkcad.core import Document, Point
from tkcad.core.command import CommandResult
from tkcad.core.dxf_export import export_dxf
from tkcad.core.dxf_import import import_dxf


import pytest


def test_roundtrip_cotas(tmp_path):
    import math
    doc = Document()
    doc.add_entity("dimension", {
        "dim_type": "linear_h", "p1": Point(0, 0), "p2": Point(50, 0),
        "offset": 10.0, "text_height": 2.5,
    })
    ang = math.radians(45.0)
    doc.add_entity("dimension", {
        "dim_type": "radius", "center": Point(100, 0),
        "p": Point(100 + 20 * math.cos(ang), 20 * math.sin(ang)),
        "text_height": 2.5,
    })

    path = tmp_path / "cotas.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg

    items, defs = import_dxf(path)
    dims = [d for k, d, l in items if k == "dimension"]
    assert len(dims) == 2

    lin = next(d for d in dims if d["dim_type"] in ("linear_h", "aligned"))
    assert lin["p1"].x == 0 and lin["p2"].x == 50

    rad = next(d for d in dims if d["dim_type"] == "radius")
    assert rad["center"].x == 100
    r = math.hypot(rad["p"].x - rad["center"].x,
                   rad["p"].y - rad["center"].y)
    assert r == pytest.approx(20.0)


def test_roundtrip_bloques_dxf(tmp_path):
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    c = doc.add_circle(Point(5, 5), 2)
    doc.define_block_def("V1", [l.id, c.id], Point(0, 0))
    doc.insert_block("V1", Point(100, 0), rotation=90, scale=2)

    path = tmp_path / "bl.dxf"
    ok, msg = export_dxf(doc.entities, path, block_defs=doc.block_defs)
    assert ok, msg

    items, defs = import_dxf(path)
    assert "V1" in defs
    inserts = [d for k, d, ly in items if k == "insert"]
    assert len(inserts) == 1
    assert inserts[0]["position"] == Point(100, 0)
    assert inserts[0]["rotation"] == 90
    assert inserts[0]["scale"] == 2
    kinds = sorted(k for k, dd, ly in defs["V1"]["entities"])
    assert kinds == ["circle", "line"]


def test_import_polilinea_y_texto(tmp_path):
    import ezdxf
    d = ezdxf.new()
    msp = d.modelspace()
    msp.add_lwpolyline([(0, 0), (10, 0), (10, 10)])
    msp.add_text("HOLA", height=2.5).set_placement((1, 1))
    path = tmp_path / "pl.dxf"
    d.saveas(str(path))

    items, defs = import_dxf(path)
    kinds = sorted(k for k, d, l in items)
    assert "polyline" in kinds
    assert "text" in kinds


def test_importar_comando(tmp_path):
    import ezdxf
    from tkcad.commands.file.importar import ImportarCommand

    d = ezdxf.new()
    d.modelspace().add_line((0, 0), (10, 0))
    path = tmp_path / "c.dxf"
    d.saveas(str(path))

    doc = Document()

    class FakeCtx:
        def __init__(self, doc):
            self.doc = doc
        def import_dxf(self, p):
            from tkcad.core.dxf_import import import_dxf as _imp
            items, defs = _imp(p)
            for kind, data, layer in items:
                self.doc.add_entity(kind, data)
            return True, f"Importadas {len(items)} entidades del DXF."
        def prompt(self, m): pass
        def write(self, m): pass

    cmd = ImportarCommand()
    ctx = FakeCtx(doc)
    cmd.start(ctx)
    assert cmd.handle_input(ctx, str(path)) == CommandResult.FINISHED
    assert len(doc.entities) == 1
    assert doc.entities[0].kind == "line"


def test_roundtrip_cota_angular(tmp_path):
    doc = Document()
    doc.add_entity("dimension", {
        "dim_type": "angular",
        "vertex": Point(0, 0),
        "p1": Point(50, 0),
        "p2": Point(30, 30),
        "radius": 20.0,
        "text_height": 2.5,
    })

    path = tmp_path / "ang.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg

    items, defs = import_dxf(path)
    dims = [d for k, d, l in items if k == "dimension"]
    assert len(dims) == 1
    
    ang = dims[0]
    assert ang["dim_type"] == "angular"
    assert ang["vertex"] == Point(0, 0)
    # Los puntos p1/p2 pueden variar ligeramente en distancia al vértice 
    # según ezdxf, pero deben estar sobre los mismos rayos
    assert ang["p1"].y == pytest.approx(0.0, abs=1e-6)
    assert ang["p2"].x == pytest.approx(ang["p2"].y, abs=1e-6)  # rayo a 45°