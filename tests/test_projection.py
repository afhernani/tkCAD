import pytest

from tkcad.core import Entity, Point, ProjectIO


def make_line():
    return Entity(
        id=1,
        kind="line",
        data={"start": Point(1, 2), "end": Point(3, 4)},
    )


def test_roundtrip_de_entidad():
    io = ProjectIO()
    restaurada = io.entity_from_dict(io.entity_to_dict(make_line()))
    assert restaurada.id == 1
    assert restaurada.kind == "line"
    assert restaurada.data["start"] == Point(1.0, 2.0)
    assert restaurada.data["end"] == Point(3.0, 4.0)
    assert restaurada.selected is False


def test_roundtrip_de_polilinea():
    io = ProjectIO()
    original = Entity(
        id=2,
        kind="polyline",
        data={"points": [Point(0, 0), Point(1, 1), Point(2, 0)]},
    )
    restaurada = io.entity_from_dict(io.entity_to_dict(original))
    assert restaurada.data["points"] == [
        Point(0, 0), Point(1, 1), Point(2, 0),
    ]


def test_save_y_load(tmp_path):
    io = ProjectIO()
    path = io.save(tmp_path / "proyecto", [make_line()], 7)
    assert path == tmp_path / "proyecto.json"
    assert path.exists()
    entities, next_id, layers, current_layer, resolved = io.load(tmp_path / "proyecto")
    assert next_id == 7
    assert len(entities) == 1
    assert entities[0].data["start"] == Point(1.0, 2.0)
    assert "0" in layers
    assert current_layer == "0"


def test_load_archivo_inexistente(tmp_path):
    io = ProjectIO()
    with pytest.raises(FileNotFoundError):
        io.load(tmp_path / "no_existe.json")


def test_from_json_repara_next_id():
    io = ProjectIO()
    text = (
        '{"version": 1, "next_entity_id": 0, "entities": '
        '[{"id": 5, "kind": "line", "data": {}}]}'
    )
    entities, next_id, layers, current_layer = io.from_json(text)
    assert next_id == 6