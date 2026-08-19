from tkcad.core.icons import TOOLBAR_COMMANDS, build_icon


def test_todos_los_iconos_se_generan():
    for name, label in TOOLBAR_COMMANDS:
        img = build_icon(name)
        assert img.size == (24, 24)
        assert img.mode == "RGBA"


def test_icono_desconocido_usa_default():
    img = build_icon("NO_EXISTE")
    assert img.size == (24, 24)
    assert img.mode == "RGBA"