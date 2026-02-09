# ======================================================================
# HVAC/hydronics_v3/dto/pump_selection_result_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PumpSelectionResultDTO:
    system_id: str
    pump_ref: str

    design_flow_m3_h: float

    required_head_m: float
    required_head_pa: float

    predicted_pump_head_m: float
    head_excess_m: float

    note: str = ""
