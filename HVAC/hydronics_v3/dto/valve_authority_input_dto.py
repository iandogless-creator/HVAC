# ======================================================================
# HVAC/hydronics_v3/dto/valve_authority_input_dto.py
# ======================================================================

"""
HVACgooee — Valve Authority Input DTO (v1)

Purpose
-------
Declarative per-terminal data required to check valve authority.

No sizing.
No inference.
No mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True, slots=True)
class ValveAuthorityTerminalDTO:
    """
    Authority inputs for a single terminal.

    All Δp values are at design flow.
    """

    terminal_leg_id: str

    # Pressure drop available across the control / balancing valve (Pa)
    valve_dp_pa: float

    # Remaining system pressure drop excluding the valve (Pa)
    system_dp_pa: float


@dataclass(frozen=True, slots=True)
class ValveAuthorityInputDTO:
    """
    Input contract for valve authority checking.
    """

    system_id: str
    terminals: List[ValveAuthorityTerminalDTO]
