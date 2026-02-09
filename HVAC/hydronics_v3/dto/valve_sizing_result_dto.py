# ======================================================================
# HVAC/hydronics_v3/dto/valve_sizing_result_dto.py
# ======================================================================

"""
HVACgooee — Valve Sizing Result DTO (v1)

Purpose
-------
Authoritative result of valve Kv selection.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValveSizingResultDTO:
    terminal_leg_id: str
    valve_ref: str
    selected_kv_m3_h: float

    # Calculated Δp at design flow using selected Kv (Pa)
    achieved_valve_dp_pa: float

    note: str = ""
