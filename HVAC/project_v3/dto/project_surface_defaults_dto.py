# HVAC/project_v3/dto/project_surface_defaults_dto.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProjectSurfaceDefaultsDTO:
    """
    Project-wide default constructions per element class.

    These defaults are:
    - Applied to new rooms/surfaces
    - Used by surfaces that do not override locally
    - Always editable
    """

    external_wall: Optional[str] = None
    internal_wall: Optional[str] = None
    floor: Optional[str] = None
    ceiling: Optional[str] = None
    roof: Optional[str] = None
    window: Optional[str] = None
    door: Optional[str] = None
