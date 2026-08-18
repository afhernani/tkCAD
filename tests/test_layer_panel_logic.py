from tkcad.core import Document, Point


def test_toggle_visible_enciende_y_apaga():
    doc = Document()
    doc.add_layer("muros")
    layer = doc.get_layer("muros")
    assert layer.visible is True
    assert doc.toggle_layer_visible("muros") is True
    assert layer.visible is False
    assert doc.toggle_layer_visible("muros") is True
    assert layer.visible is True


def test_toggle_visible_capa_inexistente():
    doc = Document()
    assert doc.toggle_layer_visible("nope") is False


def test_apagar_capa_deselecciona_sus_entidades():
    doc = Document()
    doc.add_layer("muros")
    doc.set_current_layer("muros")
    e = doc.add_line(Point(0, 0), Point(1, 0))
    doc.toggle_selection(e.id)
    assert doc.get_entity_by_id(e.id).selected is True

    doc.toggle_layer_visible("muros")
    assert doc.get_entity_by_id(e.id).selected is False


def test_toggle_locked():
    doc = Document()
    doc.add_layer("muros")
    layer = doc.get_layer("muros")
    assert layer.locked is False
    doc.toggle_layer_locked("muros")
    assert layer.locked is True
    doc.toggle_layer_locked("muros")
    assert layer.locked is False


def test_toggle_locked_capa_inexistente():
    doc = Document()
    assert doc.toggle_layer_locked("nope") is False


def test_set_layer_color():
    doc = Document()
    doc.add_layer("muros")
    assert doc.set_layer_color("muros", "#ff0000") is True
    assert doc.get_layer("muros").color == "#ff0000"


def test_set_layer_color_capa_inexistente():
    doc = Document()
    assert doc.set_layer_color("nope", "#ff0000") is False