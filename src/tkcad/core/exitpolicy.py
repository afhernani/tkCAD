"""Política de salida: decide qué hacer al cerrar según cambios y respuesta."""


def decide_exit_action(modified: bool, answer) -> str:
    """
    Args:
        modified: True si hay cambios sin guardar.
        answer: respuesta del diálogo: True=Guardar, False=No, None=Cancelar.
                (Si no hay cambios, answer es irrelevante.)

    Returns:
        "exit"      → salir sin guardar
        "save_exit" → guardar y salir
        "cancel"    → no salir
    """
    if not modified:
        return "exit"
    if answer is None:
        return "cancel"
    return "save_exit" if answer else "exit"