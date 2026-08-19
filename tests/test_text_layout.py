import pytest

from tkcad.core.text_layout import split_lines, text_block_size


def test_split_lines():
    assert split_lines("HOLA\nMUNDO") == ["HOLA", "MUNDO"]
    assert split_lines("SOLO") == ["SOLO"]


def test_block_size_una_linea():
    w, h = text_block_size("ABC", 2.0)
    assert w == pytest.approx(3 * 2.0 * 0.6)
    assert h == pytest.approx(1 * 2.0 * 1.4)


def test_block_size_multilinea():
    w, h = text_block_size("AB\nABCDE", 2.0)
    assert w == pytest.approx(5 * 2.0 * 0.6)   # manda la más larga
    assert h == pytest.approx(2 * 2.0 * 1.4)   # dos líneas

def test_split_lines_con_saltos_escapados():
    """El escape \\n del usuario debe ser interpretado como salto real."""
    raw = "HOLA\\nMUNDO"
    normalized = raw.replace("\\n", "\n")
    assert split_lines(normalized) == ["HOLA", "MUNDO"]