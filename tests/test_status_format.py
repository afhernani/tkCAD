from tkcad.core.status_format import (
    format_coords, format_flags, format_selection, format_snaps, format_zoom,
)


def test_format_coords():
    assert format_coords(1.234, -5.678) == "X: 1.2  Y: -5.7"


def test_format_snaps():
    assert format_snaps({"ENDPOINT", "MIDPOINT"}) == "SNAP: END MID"


def test_format_snaps_vacio():
    assert format_snaps(set()) == "SNAP: —"


def test_format_flags():
    assert format_flags(True, False) == "ORTHO ON  GRID OFF"
    assert format_flags(False, True) == "ORTHO OFF  GRID ON"


def test_format_selection():
    assert format_selection(3) == "3 entidades"
    assert format_selection(0) == "0 entidades"


def test_format_zoom():
    assert format_zoom(2.5) == "Escala: 2.50"