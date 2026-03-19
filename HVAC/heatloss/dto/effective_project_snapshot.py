# ======================================================================
# HVAC/heatloss/dto/effective_project_snapshot.py
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from HVAC.heatloss.dto.effective_room_snapshot import (
    EffectiveRoomSnapshotDTO,
)
from HVAC.heatloss.dto.fabric_inputs import (
    FabricSurfaceInputDTO,
)


@dataclass(frozen=True, slots=True)
class EffectiveProjectSnapshotDTO:
    """
    Immutable, fully-resolved project snapshot for physics engines.

    Engines must consume only this DTO.
    No ProjectState references allowed beyond this point.
    """

    project_id: str

    # Boundary conditions
    external_design_temp_C: float
    internal_design_temp_C: float

    # Fabric participants
    fabric_surfaces: List[FabricSurfaceInputDTO]

    # Ventilation participants
    rooms: List[EffectiveRoomSnapshotDTO]