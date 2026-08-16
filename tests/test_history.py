from tkcad.core import Document, Point


def test_undo_revierte_la_accion():
    doc = Document()
    doc.mark_action()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.commit_action()
    assert len(doc.entities) == 1
    assert doc.undo()
    assert len(doc.entities) == 0


def test_redo_reaplica_la_accion():
    doc = Document()
    doc.mark_action()
    doc.add_line(Point(0, 0), Point(10, 0))
    doc.commit_action()
    doc.undo()
    assert doc.redo()
    assert len(doc.entities) == 1


def test_accion_sin_mutaciones_no_genera_paso():
    doc = Document()
    doc.mark_action()
    doc.commit_action()
    assert not doc.undo()


def test_nueva_accion_limpia_el_redo():
    doc = Document()
    doc.mark_action()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.commit_action()
    doc.undo()
    doc.mark_action()
    doc.add_line(Point(5, 5), Point(6, 6))
    doc.commit_action()
    assert not doc.redo()


def test_undo_restaura_capas():
    doc = Document()
    doc.mark_action()
    doc.add_layer("muros")
    doc.set_current_layer("muros")
    doc.commit_action()
    doc.undo()
    assert "muros" not in doc.layers
    assert doc.current_layer == "0"


def test_pila_de_undos_sucesivos():
    doc = Document()
    doc.mark_action()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.commit_action()
    doc.mark_action()
    doc.add_circle(Point(5, 5), 1.0)
    doc.commit_action()
    doc.undo()
    assert len(doc.entities) == 1
    doc.undo()
    assert len(doc.entities) == 0
    doc.redo()
    assert len(doc.entities) == 1
    assert doc.entities[0].kind == "line"