# ======================================================================
# HVAC/hydronics_v3/dto/valve_sizing_input_dto.py
# ======================================================================

"""
HVACgooee — Valve Sizing Input DTO (v1)

Purpose
-------
Declarative inputs required to size a valve at a terminal.

All values are authoritative engineering inputs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValveSizingInputDTO:
    terminal_leg_id: str

    # Design flow through the valve (m3/h)
    design_flow_m3_h: float

    # Required pressure drop across the valve (Pa)
    required_valve_dp_pa: float
