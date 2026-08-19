from tkcad.core import Document, Point, ProjectIO


def test_roundtrip_json_dimension_y_spline(tmp_path):
    doc = Document()
    doc.add_dimension("linear_h", p1=Point(0, 0), p2=Point(100, 0), offset=15)
    doc.add_spline([Point(0, 0), Point(10, 5), Point(20, 0)])

    io = ProjectIO()
    path = tmp_path / "proj.json"
    io.save(
        path, doc.entities, doc.next_entity_id,
        layers=doc.layers, current_layer=doc.current_layer,
    )

    entities, next_id, layers, current_layer, _ = io.load(path)

    kinds = {e.kind for e in entities}
    assert "dimension" in kinds
    assert "spline" in kinds

    dim = next(e for e in entities if e.kind == "dimension")
    assert dim.data["p2"] == Point(100, 0)
    assert dim.data["offset"] == 15

    spl = next(e for e in entities if e.kind == "spline")
    assert len(spl.data["points"]) == 3
    assert spl.data["points"][1] == Point(10, 5)