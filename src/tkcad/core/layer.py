from dataclasses import dataclass


@dataclass
class Layer:
    """Una capa de dibujo de tkCAD.

    La capa "0" es la predefinida: siempre existe y no puede
    borrarse. Las entidades nuevas se asignan a la capa actual.
    """

    name: str
    color: str = "white"
    visible: bool = True
    locked: bool = False