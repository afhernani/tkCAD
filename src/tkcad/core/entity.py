from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Entity:
    id: int
    kind: str
    data: Dict[str, Any]
    selected: bool = False
    layer: str = "0"
