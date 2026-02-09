# ======================================================================
# HVAC/project/room_state_v1.py
# ======================================================================

"""
HVACgooee — Room State v1 (CANONICAL)

Purpose
-------
Authoritative, engine-facing representation of a room within ProjectState.

LOCKED
------
• Stored inside ProjectState.rooms: dict[str, RoomStateV1]
• GUI adapters may READ these
• Only engines / runners may VALIDATE and commit authoritative results
• GUI preview may store heatloss_preview_qt_w (non-authoritative)

Notes
-----
• This module contains NO GUI logic
• This module performs NO calculations
• This module defines intent only
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from HVAC_legacy.constructions.construction_preset import SurfaceClass
from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)


# ----------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------
@dataclass(slots=True)
class RoomGeometryV1:
    """
    Minimal room geometry contract.

    Notes
    -----
    • length/width/height enable basic read-only display
    • surface_areas_m2 is OPTIONAL but preferred for accurate previews
    • No physics, no validation, no inference
    """

    length_m: float
    width_m: float
    height_m: float

    # Optional explicit areas by surface class (preferred for preview accuracy)
    surface_areas_m2: Dict[SurfaceClass, float] = field(default_factory=dict)

    @property
    def floor_area_m2(self) -> float:
        return max(0.0, self.length_m * self.width_m)

    @property
    def volume_m3(self) -> float:
        return max(0.0, self.floor_area_m2 * self.height_m)

    def area_for(self, surface_class: SurfaceClass) -> Optional[float]:
        return self.surface_areas_m2.get(surface_class)


# ----------------------------------------------------------------------
# Room State
# ----------------------------------------------------------------------
@dataclass(slots=True)
class RoomStateV1:
    """
    Authoritative room container.

    Authority
    ---------
    • geometry and constructions are authoritative declared intent
    • heatloss_preview_qt_w is GUI-only and never authoritative
    """

    room_id: str
    name: str

    geometry: RoomGeometryV1

    # Declared fabric intent, keyed by SurfaceClass
    constructions: Dict[SurfaceClass, ConstructionUValueResultDTO] = field(
        default_factory=dict
    )

    # GUI-only preview cache (non-authoritative)
    heatloss_preview_qt_w: Optional[float] = None
