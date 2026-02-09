# ======================================================================
# HVAC/hydronics/dto/hydronics_results_dto_v1.py
# ======================================================================

"""
HVACgooee — Hydronics Results DTO v1
-----------------------------------

GUI-facing, read-only representations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(slots=True)
class PathPressureDropDTO:
    terminal_id: str
    total_dp_pa: float


@dataclass(slots=True)
class PumpDutyDTO:
    flow_l_s: float
    head_m: float
    electrical_power_w: float


@dataclass(slots=True)
class BalancingRowDTO:
    terminal_id: str
    setting: Optional[str]
    dp_added_pa: float
    residual_pa: float


@dataclass(slots=True)
class HydronicsResultsDTO:
    paths: List[PathPressureDropDTO]
    pump: PumpDutyDTO
    balancing: Optional[List[BalancingRowDTO]]
