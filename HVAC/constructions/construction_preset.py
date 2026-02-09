from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


PresetType = Literal[
    "reference",
    "calculated",
    "manufacturer",
    "user_defined",
]


class SurfaceClass(str, Enum):
    EXTERNAL_WALL = "external_wall"
    INTERNAL_WALL = "internal_wall"
    INTERNAL_DOOR = "internal_door"
    ROOF = "roof"
    CEILING = "ceiling"
    FLOOR = "floor"
    WINDOW = "window"
    DOOR = "door"


@dataclass(frozen=True)
class ConstructionPreset:
    ref: str
    name: str
    surface_class: SurfaceClass
    u_value: float
    preset_type: PresetType
