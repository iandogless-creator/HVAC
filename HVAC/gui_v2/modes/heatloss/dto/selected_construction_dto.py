# ======================================================================
# HVAC/gui_v2/modes/heatloss/dto/selected_construction_dto.py
# ======================================================================

"""
HVACgooee — Selected Construction DTO (v2)

Represents an explicit, user-committed fabric construction choice.

GUI-only:
• No calculations
• No geometry inference
• No engine imports
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SelectedConstructionDTO:
    """
    Canonical construction intent record.

    surface_id
        Human-readable surface role (e.g. "External wall")

    construction_ref
        Construction name or user-defined label

    u_value
        Authoritative U-value (W/m²·K) at time of commit
    """

    surface_id: str
    construction_ref: str
    u_value: float
