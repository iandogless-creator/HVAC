# ======================================================================
# HVAC/hydronics_v3/dto/operating_point_result_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OperatingPointResultDTO:
    system_id: str
    pump_ref: str

    operating_flow_m3_h: float
    operating_head_pa: float
    operating_head_m: float

    note: str = ""
