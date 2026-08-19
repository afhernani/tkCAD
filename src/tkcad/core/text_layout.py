"""Layout de texto multilinea (pure Python, testeable)."""


def split_lines(content: str):
    """Devuelve la lista de líneas del texto."""
    return str(content).split("\n")


def text_block_size(content: str, height: float):
    """
    Devuelve (ancho, alto) del bloque de texto en unidades de mundo.
    ancho = línea más larga; alto = nº de líneas * interlineado.
    """
    lines = split_lines(content)
    width = max((len(ln) for ln in lines), default=1) * height * 0.6
    total = len(lines) * height * 1.4
    return width, total