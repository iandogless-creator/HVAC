# ======================================================================
# HVAC/heatloss/dto/effective_room_snapshot.py
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EffectiveRoomSnapshotDTO:
    """
    Immutable, fully-resolved room snapshot for physics consumption.

    Contains only values needed by engines.

    No defaults.
    No resolution logic.
    No project references.
    """

    room_id: str

    # Geometry (resolved)
    floor_area_m2: float
    height_m: float
    volume_m3: float

    # Ventilation (resolved)
    ach: float

    # Thermal
    internal_design_temp_C: float