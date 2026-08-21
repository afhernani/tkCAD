from tkcad.core import Document, Point
from tkcad.core.command import CommandResult
from tkcad.core.dxf_export import export_dxf
from tkcad.core.dxf_import import import_dxf


def test_roundtrip_dxf(tmp_path):
    doc = Document()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.add_circle(Point(5, 5), 3)
    doc.add_arc(Point(0, 0), 5, 0, 90)

    path = tmp_path / "rt.dxf"
    ok, msg = export_dxf(doc.entities, path)
    assert ok, msg

    items, defs = import_dxf(path)
    kinds = sorted(k for k, d, l in items)
    assert kinds == ["arc", "circle", "line"]

    line = next(d for k, d, l in items if k == "line")
    assert line["start"].x == 0 and line["end"].x == 10

    circ = next(d for k, d, l in items if k == "circle")
    assert circ["radius"] == 3


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