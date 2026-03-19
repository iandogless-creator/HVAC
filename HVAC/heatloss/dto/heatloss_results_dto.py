# ======================================================================
# HVAC/heatloss/dto/heatloss_results_dto.py
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


# ----------------------------------------------------------------------
# Per-room authoritative result
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RoomHeatLossResultDTO:
    """
    Authoritative steady-state room heat-loss result.

    Pure physics output.
    No GUI concerns.
    No overrides.
    """

    room_id: str
    q_fabric_W: float
    q_ventilation_W: float
    q_total_W: float


# ----------------------------------------------------------------------
# Project-level authoritative result
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ProjectHeatLossResultDTO:
    """
    Canonical project heat-loss result container.

    This is the ONLY structure committed to ProjectState.
    """

    project_id: str
    rooms: Tuple[RoomHeatLossResultDTO, ...]
    project_total_W: float