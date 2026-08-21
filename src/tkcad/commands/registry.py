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
from .drawing.texto import TextoCommand
from .drawing.cota import CotaCommand
from .drawing.spline import SplineCommand

# Modify
from .modify.mover import MoveCommand
from .modify.copiar import CopyCommand
from .modify.borrar import DeleteCommand
from .modify.rotar import RotateCommand
from .modify.escalar import ScaleCommand
from .modify.simetria import MirrorCommand
from .modify.recortar import TrimCommand
from .modify.extender import ExtendCommand
from .modify.matriz import MatrizCommand
from .modify.bloque import BloqueCommand
from .modify.descomponer import DescomponerCommand
from .modify.defbloque import DefBloqueCommand
from .modify.insertar import InsertarCommand

# File
from .file.guardar import SaveCommand, SaveAsCommand
from .file.abrir import OpenCommand
from .file.nuevo import NewCommand
from .file.exportar import ExportCommand
from .file.exportarimg import ExportarImgCommand
from .file.importar import ImportarCommand

# View
from .view.seleccion import SelectCommand, ListCommand
from .view.snap import SnapCommand, GridCommand, ShowGridCommand
from .view.capa import CapaCommand
from .view.zoom import ZoomCommand
from .view.ortho import OrthoCommand
from .view.seleccion_poligono import SeleccionPoligonoCommand
from .view.zoom_avanzado import ZoomPrevioCommand, ZoomSiguienteCommand, ZoomVentanaCommand
from .view.panel_capas import PanelCapasCommand
from .view.panel_properties import PanelPropiedadesCommand
from .view.barra_estado import BarraEstadoCommand

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
    TextoCommand,
    CotaCommand,
    SplineCommand,
    # Modify
    MoveCommand,
    CopyCommand,
    DeleteCommand,
    RotateCommand,
    ScaleCommand,
    MirrorCommand,
    TrimCommand,
    ExtendCommand,
    MatrizCommand,
    BloqueCommand,
    DescomponerCommand,
    DefBloqueCommand,
    InsertarCommand,
    # File
    SaveCommand,
    SaveAsCommand,
    OpenCommand,
    NewCommand,
    ExportCommand,
    ExportarImgCommand,
    ImportarCommand,
    # View
    SelectCommand,
    ListCommand,
    SnapCommand,
    GridCommand,
    ShowGridCommand,
    CapaCommand,
    ZoomCommand,
    OrthoCommand,
    SeleccionPoligonoCommand,
    ZoomPrevioCommand, 
    ZoomSiguienteCommand, 
    ZoomVentanaCommand,
    PanelCapasCommand,
    PanelPropiedadesCommand,
    BarraEstadoCommand,
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
        # print("REG:", command_class.__name__, getattr(command_class, "name", None))