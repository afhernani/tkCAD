"""
Registro central de comandos de tkCAD.

Añadir un comando nuevo en el futuro =
crear su archivo en la carpeta correcta + añadirlo a ALL_COMMANDS.
"""
from typing import List, Type

from ..core import Command

# Drawing
from .drawing.line import LineCommand
from .drawing.poliline import PolylineCommand
from .drawing.circulo import CircleCommand
from .drawing.arco import ArcCommand
from .drawing.poligono import PolygonCommand
from .drawing.elipse import ElipseCommand

# Modify
from .modify.mover import MoveCommand
from .modify.copiar import CopyCommand
from .modify.borrar import DeleteCommand
from .modify.rotar import RotateCommand
from .modify.escalar import ScaleCommand
from .modify.simetria import MirrorCommand
from .modify.recortar import TrimCommand
from .modify.extender import ExtendCommand

# File
from .file.guardar import SaveCommand, SaveAsCommand
from .file.abrir import OpenCommand
from .file.nuevo import NewCommand

# View
from .view.seleccion import SelectCommand, ListCommand
from .view.snap import SnapCommand, GridCommand, ShowGridCommand
from .view.capa import CapaCommand
from .view.zoom import ZoomCommand
from .view.ortho import OrthoCommand

# System
from .system.ayuda import HelpCommand
from .system.exitx import ExitCommand
from .system.deshacer import UndoCommand, RedoCommand


ALL_COMMANDS: List[Type[Command]] = [
    # Drawing
    LineCommand,
    PolylineCommand,
    CircleCommand,
    ArcCommand,
    PolygonCommand,
    ElipseCommand,
    # Modify
    MoveCommand,
    CopyCommand,
    DeleteCommand,
    RotateCommand,
    ScaleCommand,
    MirrorCommand,
    TrimCommand,
    ExtendCommand,
    # File
    SaveCommand,
    SaveAsCommand,
    OpenCommand,
    NewCommand,
    # View
    SelectCommand,
    ListCommand,
    SnapCommand,
    GridCommand,
    ShowGridCommand,
    CapaCommand,
    ZoomCommand,
    OrthoCommand,
    # System
    HelpCommand,
    ExitCommand,
    UndoCommand, 
    RedoCommand,
]


def register_all(manager) -> None:
    """Registra todos los comandos en un CommandLineManager."""
    for command_class in ALL_COMMANDS:
        manager.register(command_class)