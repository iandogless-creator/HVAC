# ======================================================================
# HVAC/hydronics_v3/dto/pump_efficiency_curve_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True, slots=True)
class PumpEfficiencyPointDTO:
    """
    One point on a pump efficiency curve.

    flow_m3_h : flow rate (m³/h)
    efficiency : fractional efficiency (0.0 – 1.0)
    """
    flow_m3_h: float
    efficiency: float


@dataclass(frozen=True, slots=True)
class PumpEfficiencyCurveDTO:
    """
    Declarative efficiency curve for a pump.

    Points must be ordered by flow.
    """
    pump_ref: str
    efficiency_points: List[PumpEfficiencyPointDTO]
