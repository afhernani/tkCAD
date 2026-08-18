from tkcad.core import Document, Point


def test_sin_cambios_no_esta_modificado():
    doc = Document()
    assert doc.modified is False


def test_cambio_marca_modified():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    assert doc.modified is True


def test_mark_saved_limpia_el_flag():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.mark_saved()
    assert doc.modified is False


def test_notify_false_no_marca_modified():
    doc = Document()
    doc.add_entity(
        "line",
        {"start": Point(0, 0), "end": Point(1, 0)},
        notify=False,
    )
    assert doc.modified is False


def test_editar_tras_guardar_vuelve_a_marcar():
    doc = Document()
    doc.add_line(Point(0, 0), Point(1, 0))
    doc.mark_saved()
    doc.move_selected(5, 5)   # cualquier edición
    assert doc.modified is True