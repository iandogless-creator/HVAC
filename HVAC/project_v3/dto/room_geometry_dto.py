# HVAC/project_v3/dto/room_geometry_dto.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class RoomGeometryDTO:
    """
    Base room geometry (v1).

    Rooms are modelled as rhomboids:
    - Length
    - Width
    - Height (may inherit from Environment)
    """

    length_m: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None  # None => inherit from Environment
