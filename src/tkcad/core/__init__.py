# Re-exportamos TODO para que 'from .core import X' siga funcionando igual
from .types import ALL_SNAP_MODES, TARGET_ALIASES, TARGET_KIND_MAP, parse_target, parse_kind
from .point import Point
from .entity import Entity
from .command import CommandResult, Command
from .parser import parse_number, parse_point
from .manager import CommandLineManager
from .snapengine import SnapEngine

# (Opcional) definir qué se exporta con "from tkcad.core import *"
__all__ = [
    "ALL_SNAP_MODES", "TARGET_ALIASES", "TARGET_KIND_MAP",
    "parse_target", "parse_kind",
    "Point", "Entity",
    "CommandResult", "Command",
    "parse_number", "parse_point",
    "CommandLineManager", "SnapEngine",
]