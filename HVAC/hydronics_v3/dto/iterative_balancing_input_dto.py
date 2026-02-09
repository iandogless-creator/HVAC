# ======================================================================
# HVAC/hydronics_v3/dto/iterative_balancing_input_dto.py
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True, slots=True)
class IterativeBalancingTerminalInputDTO:
    terminal_leg_id: str

    # Design flow (m3/h)
    design_flow_m3_h: float

    # Non-valve system Δp at design flow (Pa)
    system_dp_pa: float


@dataclass(frozen=True, slots=True)
class IterativeBalancingInputDTO:
    system_id: str

    terminals: Dict[str, IterativeBalancingTerminalInputDTO]

    # Authority requirement
    min_authority: float = 0.3

    # Max Kv refinement steps
    max_iterations: int = 10
