from tkcad.core.exitpolicy import decide_exit_action


def test_sin_cambios_sale_directamente():
    # Sin cambios pendientes, siempre sale (aunque answer sea None)
    assert decide_exit_action(False, None) == "exit"


def test_con_cambios_y_cancelar_no_sale():
    # Hay cambios y el usuario pulsa Cancelar → no sale
    assert decide_exit_action(True, None) == "cancel"


def test_con_cambios_y_guardar():
    # Hay cambios y el usuario pulsa Sí (guardar) → guarda y sale
    assert decide_exit_action(True, True) == "save_exit"


def test_con_cambios_y_no_guardar():
    # Hay cambios y el usuario pulsa No → sale sin guardar
    assert decide_exit_action(True, False) == "exit"