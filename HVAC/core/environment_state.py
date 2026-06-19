# ======================================================================
# HVAC/core/environment_state.py
# ======================================================================
"""
HVACgooee — Environment State v1 (CANONICAL)

Authoritative project-wide defaults used by snapshot building.

Rules
-----
• Stored on ProjectState.environment
• Editable via Environment Panel
• Never inferred silently
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class EnvironmentStateV1:
    external_design_temp_C: Optional[float] = None
    default_internal_temp_C: Optional[float] = None
    default_room_height_m: Optional[float] = None
    default_ach: Optional[float] = None

    # H-S21-A — Hydronic design source inputs.
    # Store source temperatures only. Derived values are calculated at use sites.
    design_flow_temp_c: Optional[float] = 75.0
    design_return_temp_c: Optional[float] = 65.0

    def to_dict(self) -> dict:
        return {
            "external_design_temp_C": self.external_design_temp_C,
            "default_internal_temp_C": self.default_internal_temp_C,
            "default_room_height_m": self.default_room_height_m,
            "default_ach": self.default_ach,
            "design_flow_temp_c": self.design_flow_temp_c,
            "design_return_temp_c": self.design_return_temp_c,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnvironmentStateV1":
        return cls(
            external_design_temp_C=data.get("external_design_temp_C"),
            default_internal_temp_C=data.get("default_internal_temp_C"),
            default_room_height_m=data.get("default_room_height_m"),
            default_ach=data.get("default_ach"),
            design_flow_temp_c=data.get("design_flow_temp_c", 75.0),
            design_return_temp_c=data.get("design_return_temp_c", 65.0),
        )
