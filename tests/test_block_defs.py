import pytest

from tkcad.core import Document, Point, ProjectIO


def test_define_e_insertar():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    c = doc.add_circle(Point(5, 5), 2)

    assert doc.define_block_def("V1", [l.id, c.id], Point(0, 0))
    assert "V1" in doc.block_defs
    assert len(doc.entities) == 0          # originales eliminados

    ins = doc.insert_block("V1", Point(100, 0))
    assert ins is not None and ins.kind == "insert"
    assert len(doc.entities) == 1


def test_explode_insert():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    c = doc.add_circle(Point(5, 5), 2)
    doc.define_block_def("V1", [l.id, c.id], Point(0, 0))
    ins = doc.insert_block("V1", Point(100, 0))

    ids = doc.explode_insert(ins.id)
    assert len(ids) == 2
    kinds = sorted(doc.get_entity_by_id(i).kind for i in ids)
    assert kinds == ["circle", "line"]

    lin = next(doc.get_entity_by_id(i) for i in ids
               if doc.get_entity_by_id(i).kind == "line")
    assert lin.data["start"] == Point(100, 0)
    assert lin.data["end"] == Point(110, 0)


def test_insert_con_rotacion_y_escala():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    doc.define_block_def("V2", [l.id], Point(0, 0))
    ins = doc.insert_block("V2", Point(0, 0), rotation=90, scale=2)

    ids = doc.explode_insert(ins.id)
    d = doc.get_entity_by_id(ids[0]).data
    # (10,0)·2 = (20,0); rotado 90° → (0,20)
    assert d["end"].x == pytest.approx(0, abs=1e-9)
    assert d["end"].y == pytest.approx(20)


def test_mover_insert():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    doc.define_block_def("V3", [l.id], Point(0, 0))
    ins = doc.insert_block("V3", Point(50, 50))

    doc.set_selection_ids([ins.id])
    doc.move_selected(10, -5)
    assert doc.get_entity_by_id(ins.id).data["position"] == Point(60, 45)

def test_bbox_insert():
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    doc.define_block_def("V1", [l.id], Point(0, 0))
    ins = doc.insert_block("V1", Point(100, 50))

    bbox = doc._get_entity_bbox(doc.get_entity_by_id(ins.id))
    assert bbox is not None
    min_x, min_y, max_x, max_y = bbox
    assert min_x == pytest.approx(100)
    assert max_x == pytest.approx(110)
    assert min_y == pytest.approx(50)

def test_roundtrip_block_defs(tmp_path):
    doc = Document()
    l = doc.add_line(Point(0, 0), Point(10, 0))
    doc.define_block_def("V1", [l.id], Point(0, 0))
    doc.insert_block("V1", Point(50, 0))

    io = ProjectIO()
    path = tmp_path / "bd.json"
    io.save(path, doc.entities, doc.next_entity_id,
            layers=doc.layers, current_layer=doc.current_layer,
            block_names=doc.block_names, block_defs=doc.block_defs)

    entities, next_id, layers, current_layer, _ = io.load(path)

    doc2 = Document()
    doc2.entities = entities
    doc2.block_defs = io.last_block_defs

    assert "V1" in doc2.block_defs
    inserts = [e for e in entities if e.kind == "insert"]
    assert len(inserts) == 1
    assert inserts[0].data["name"] == "V1"
    