# ======================================================================
# HVAC/hydronics/pumps/dto/pump_duty_point_v1.py
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PumpDutyPointV1:
    """
    Single design operating point for pump selection.
    """

    design_flow_m3_s: float
    required_head_Pa: float
