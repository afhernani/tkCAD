from tkcad.core import Entity, Layer, Point, ProjectIO


def test_roundtrip_con_capas(tmp_path):
    io = ProjectIO()
    capas = {
        "0": Layer(name="0"),
        "muros": Layer(name="muros", color="red", visible=False),
    }
    entidad = Entity(
        id=1,
        kind="line",
        data={"start": Point(0, 0), "end": Point(1, 1)},
        layer="muros",
    )
    path = io.save(tmp_path / "p", [entidad], 2, layers=capas, current_layer="muros")
    entities, next_id, layers, current_layer, _ = io.load(path)
    assert current_layer == "muros"
    assert layers["muros"].color == "red"
    assert layers["muros"].visible is False
    assert entities[0].layer == "muros"


def test_migracion_de_version_1():
    io = ProjectIO()
    text = (
        '{"version": 1, "next_entity_id": 3, "entities": ['
        '{"id": 1, "kind": "line", "data": {}}, '
        '{"id": 2, "kind": "circle", "data": {}}]}'
    )
    entities, next_id, layers, current_layer = io.from_json(text)
    assert set(layers) == {"0"}
    assert current_layer == "0"
    assert all(entity.layer == "0" for entity in entities)