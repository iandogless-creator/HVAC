# ======================================================================
# HVAC/heatloss/dto/fabric_inputs.py
# ======================================================================
"""
DTOs for feeding engines (engine boundary).

Engines must not depend on ProjectState/RoomState.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FabricSurfaceInputDTO:
    surface_id: str
    room_id: str
    surface_class: str
    area_m2: float
    u_value_W_m2K: float
    delta_t_K: float