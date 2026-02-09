from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


# ------------------------------------------------------------------
# Boundary (fabric element) DTO
# ------------------------------------------------------------------

@dataclass(slots=True)
class BoundaryLossDTO:
    """
    GUI-facing representation of a single fabric boundary heat loss.

    NOTE:
    - No physics terms (ΔT, boundary temp, etc.)
    - Values are already calculated upstream
    """
    element_type: str                 # e.g. "Wall", "Window"
    area_m2: float
    u_value: float
    u_source: str                     # "Construction", "Manual (TEMP)", etc.
    construction_id: Optional[str]    # None in TEMP wiring
    heat_loss_w: float                # Qt for this boundary


# ------------------------------------------------------------------
# Room-level heat loss result DTO
# ------------------------------------------------------------------

@dataclass(slots=True)
class HeatLossResultDTO:
    """
    GUI-facing heat-loss result for ONE room.
    """

    room_name: str
    internal_temp_c: float
    room_volume_m3: Optional[float]

    ventilation_method: str
    ventilation_heat_loss_w: float

    boundaries: List[BoundaryLossDTO]

    total_fabric_heat_loss_w: float
    total_heat_loss_w: float
