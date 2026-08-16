from tkcad.core import Document, Point


def test_capa_0_existe_por_defecto():
    doc = Document()
    assert "0" in doc.layers
    assert doc.current_layer == "0"


def test_nuevas_entidades_van_a_la_capa_actual():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    assert doc.entities[0].layer == "0"
    assert doc.add_layer("muros")
    assert doc.set_current_layer("muros")
    doc.add_circle(Point(5, 5), 1.0)
    assert doc.entities[1].layer == "muros"


def test_add_layer_duplicado_o_vacio_falla():
    doc = Document()
    assert doc.add_layer("muros")
    assert not doc.add_layer("muros")
    assert not doc.add_layer("   ")


def test_capa_0_y_capa_actual_no_se_pueden_borrar():
    doc = Document()
    doc.add_layer("muros")
    assert not doc.delete_layer("0")          # la 0 nunca
    doc.set_current_layer("muros")
    assert not doc.delete_layer("muros")      # la actual tampoco
    doc.set_current_layer("0")
    assert doc.delete_layer("muros")          # vacía y no actual: sí


def test_visible_entities_filtra_capas_apagadas():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.add_layer("muros")
    doc.set_current_layer("muros")
    doc.add_circle(Point(5, 5), 1.0)
    assert len(doc.visible_entities()) == 2
    doc.toggle_layer_visible("muros")
    visibles = doc.visible_entities()
    assert len(visibles) == 1
    assert visibles[0].kind == "line"


def test_capa_bloqueada_no_se_puede_seleccionar():
    doc = Document()
    doc.add_layer("ref")
    doc.set_current_layer("ref")
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.toggle_layer_locked("ref")
    doc.select_all()
    assert doc.selection_count() == 0


def test_apagar_capa_deselecciona_sus_entidades():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.select_all()
    assert doc.selection_count() == 1
    doc.toggle_layer_visible("0")
    assert doc.selection_count() == 0