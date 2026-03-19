# HVAC/project_v3/dto/surface_geometry_dto.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class SurfaceGeometryDTO:
    """
    Geometry for a single surface.

    Geometry is intent:
    - Dimensions may be inherited
    - Area is always derived
    """

    length_m: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None  # None => inherit from Environment / Room
