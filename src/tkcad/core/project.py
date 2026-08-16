import json
from pathlib import Path

from .entity import Entity
from .point import Point
from .layer import Layer


class ProjectIO:
    """Serialización y acceso a disco de proyectos tkCAD (JSON).

    No conoce la UI ni el modelo: solo transforma entidades <-> JSON
    y lee/escribe archivos. Los diálogos los gestiona CadApp.
    """

    VERSION = 2

    # --------------------------------------------------------
    # Encode / decode de valores
    # --------------------------------------------------------
    def encode_value(self, value):
        if isinstance(value, Point):
            return {
                "__type__": "Point",
                "x": value.x,
                "y": value.y,
            }
        if isinstance(value, list):
            return [self.encode_value(item) for item in value]
        return value

    def decode_value(self, value):
        if isinstance(value, dict):
            if value.get("__type__") == "Point":
                return Point(
                    float(value["x"]),
                    float(value["y"]),
                )
            return value
        if isinstance(value, list):
            return [self.decode_value(item) for item in value]
        return value

    # --------------------------------------------------------
    # Encode / decode de entidades
    # --------------------------------------------------------
    def entity_to_dict(self, entity) -> dict:
        return {
            "id": entity.id,
            "kind": entity.kind,
            "layer":entity.layer,
            "data": {
                key: self.encode_value(value)
                for key, value in entity.data.items()
            },
        }

    def entity_from_dict(self, data) -> Entity:
        entity_id = int(data["id"])
        kind = str(data["kind"])
        raw_data = data.get("data", {})
        decoded_data = {
            key: self.decode_value(value)
            for key, value in raw_data.items()
        }
        return Entity(
            id=entity_id,
            kind=kind,
            data=decoded_data,
            selected=False,
            layer=str(data.get("layer","0")),
        )

    # --------------------------------------------------------
    # Proyecto completo <-> JSON
    # --------------------------------------------------------

    def layer_to_dict(self, layer) -> dict:
        return {
            "name": layer.name,
            "color": layer.color,
            "visible": layer.visible,
            "locked": layer.locked,
        }

    def layer_from_dict(self, data) -> Layer:
        return Layer(
            name=str(data["name"]),
            color=str(data.get("color", "white")),
            visible=bool(data.get("visible", True)),
            locked=bool(data.get("locked", False)),
        )

    def to_json(self, entities, next_entity_id, layers=None, current_layer="0") -> str:
        if layers is None:
            layers = {"0": Layer(name="0")}
        project_data = {
            "version": self.VERSION,
            "next_entity_id": next_entity_id,
            "current_layer": current_layer,
            "layers": [
                self.layer_to_dict(layer)
                for layer in layers.values()
            ],
            "entities": [
                self.entity_to_dict(entity)
                for entity in entities
            ],
        }
        return json.dumps(project_data, indent=2, ensure_ascii=False)

    def from_json(self, text: str):
        """Devuelve (entities, next_entity_id, layers, current_layer)."""
        project_data = json.loads(text)
        entities = [
            self.entity_from_dict(entity_data)
            for entity_data in project_data.get("entities", [])
        ]
        max_id = max((entity.id for entity in entities), default=0)
        next_id = project_data.get("next_entity_id")
        if not isinstance(next_id, int) or next_id <= max_id:
            next_id = max_id + 1

        # Capas: los archivos v1 no tienen → migración a la capa "0".
        layers_data = project_data.get("layers")
        if layers_data:
            layers = {
                layer.name: layer
                for layer in map(self.layer_from_dict, layers_data)
            }
        else:
            layers = {}
        if "0" not in layers:
            layers["0"] = Layer(name="0")
        current_layer = str(project_data.get("current_layer", "0"))
        if current_layer not in layers:
            current_layer = "0"
        return entities, next_id, layers, current_layer
    # --------------------------------------------------------
    # Acceso a disco (sin diálogos)
    # --------------------------------------------------------
    def save(self, path, entities, next_entity_id, layers=None, current_layer="0") -> Path:
        path = Path(path).expanduser()
        if path.suffix == "":
            path = path.with_suffix(".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.to_json(entities, next_entity_id, layers, current_layer),
            encoding="utf-8",
        )
        return path

    def load(self, path):
        """Devuelve (entities, next_entity_id, layers, current_layer, path)."""
        path = Path(path).expanduser()
        if not path.exists() and path.suffix == "":
            alternative = path.with_suffix(".json")
            if alternative.exists():
                path = alternative
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo: {path}")
        entities, next_id, layers, current_layer = self.from_json(
            path.read_text(encoding="utf-8")
        )
        return entities, next_id, layers, current_layer, path