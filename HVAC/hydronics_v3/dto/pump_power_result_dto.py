# ======================================================================
# HVAC/hydronics_v3/dto/pump_power_result_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class PumpPowerResultDTO:
    """
    Authoritative pump power evaluation at operating point.
    """

    system_id: str
    pump_ref: str

    flow_m3_h: float
    head_pa: float
    head_m: float

    efficiency: float

    hydraulic_power_w: float
    shaft_power_w: float

    # Optional electrical input (if motor efficiency provided)
    motor_efficiency: Optional[float]
    electrical_power_w: Optional[float]

    note: str = ""
