from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

    def __str__(self):
        return f"{self.x:.3f},{self.y:.3f}"
