# ======================================================================
# HVAC/hydronics_v3/dto/pump_duty_point_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PumpDutyPointInputDTO:
    """
    Required duty point for the system.

    design_flow_m3_h: system design flow (m³/h)
    required_head_pa: required pump head (Pa) at that flow
    """
    system_id: str
    design_flow_m3_h: float
    required_head_pa: float

    # Optional design margin (fraction, e.g. 0.1 = +10% head)
    head_margin_frac: float = 0.0
