# HVAC/project_v3/dto/surface_intent_dto.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from HVAC.project_v3.dto.surface_geometry_dto import SurfaceGeometryDTO


@dataclass
class SurfaceIntentDTO:
    """
    Declared intent for a single surface.
    """
    element_class: str
    construction_id: Optional[str] = None

    geometry: SurfaceGeometryDTO = field(
        default_factory=SurfaceGeometryDTO
    )

    delta_t_override: Optional[float] = None
    internal_losses_enabled: bool = False
