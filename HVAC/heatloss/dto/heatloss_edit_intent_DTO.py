# ======================================================================
# HVACgooee — Heat-Loss Edit Intent DTO
# Phase: G-C
# Status: ACTIVE
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HeatLossEditIntentDTO:
    """
    Explicit user edit intent for heat-loss inputs.

    Rules:
    - Represents a single, atomic edit
    - No defaults
    - No inference
    - No calculation
    """

    room_id: str
    element_id: str
    scope: str            # "geometry" | "construction" | "assumptions"
    payload: dict[str, Any]
