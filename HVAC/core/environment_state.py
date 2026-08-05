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

from dataclasses import dataclass, field
from typing import Optional

from HVAC.heatloss.physics.environment_pipe_pair_spacing_defaults_v1 import (
    default_environment_pipe_pair_spacing_defaults_v1,
    normalise_environment_pipe_pair_spacing_defaults_v1,
)


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

    # H-S37-B1 — Inherited Basic PS first-pass velocity criterion.
    # Local section overrides are a later, separate intent stage.
    basic_ps_max_velocity_m_s: Optional[float] = 1.0

    # H-S66-K — Project-wide bare-pipe surface emissivity authority.
    # None is intentionally unresolved; local committed-section overrides
    # are persisted separately with the exact section identity.
    bare_pipe_emissivity: Optional[float] = None

    # H-S66-N1A — Universal support geometry for stacked F&R pairs only.
    # Separate RR sections do not consume these values. Exact committed-
    # section overrides are deliberately deferred to H-S66-N1B.
    bare_pipe_pair_spacing_defaults_by_nominal_od_mm: dict[str, dict] = field(
        default_factory=default_environment_pipe_pair_spacing_defaults_v1
    )

    def to_dict(self) -> dict:
        return {
            "external_design_temp_C": self.external_design_temp_C,
            "default_internal_temp_C": self.default_internal_temp_C,
            "default_room_height_m": self.default_room_height_m,
            "default_ach": self.default_ach,
            "design_flow_temp_c": self.design_flow_temp_c,
            "design_return_temp_c": self.design_return_temp_c,
            "basic_ps_max_velocity_m_s": self.basic_ps_max_velocity_m_s,
            "bare_pipe_emissivity": self.bare_pipe_emissivity,
            "bare_pipe_pair_spacing_defaults_by_nominal_od_mm": (
                normalise_environment_pipe_pair_spacing_defaults_v1(
                    self.bare_pipe_pair_spacing_defaults_by_nominal_od_mm
                )
            ),
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
            basic_ps_max_velocity_m_s=data.get(
                "basic_ps_max_velocity_m_s",
                1.0,
            ),
            bare_pipe_emissivity=data.get("bare_pipe_emissivity"),
            bare_pipe_pair_spacing_defaults_by_nominal_od_mm=(
                normalise_environment_pipe_pair_spacing_defaults_v1(
                    data.get(
                        "bare_pipe_pair_spacing_defaults_by_nominal_od_mm",
                        default_environment_pipe_pair_spacing_defaults_v1(),
                    )
                )
            ),
        )
