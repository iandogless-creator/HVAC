"""
hydronics_run_result_dto.py
---------------------------

HVACgooee — Hydronics v1 Result DTOs (GUI-facing)

Rules
-----
• Dumb, flat, explicit
• No solver logic
• Stable contract
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HydronicsRunInputDTO:
    """
    Inputs for a single hydronic run (v1).

    Notes:
        - This is deliberately "single run" (no topology).
        - heat_demand_w is typically QT handed off from heat-loss.
    """
    system_type: str
    heat_demand_w: float
    design_delta_t_k: float

    pipe_length_m: float

    tees_through: int
    tees_branch: int
    reducers: int
    enlargers: int

    routing_loss_k_per_m: float  # "Auto" allowance or overridden value


@dataclass(frozen=True)
class HydronicsRunResultDTO:
    """
    Results for a single hydronic run (v1).
    """
    volume_flow_m3_h: float
    mass_flow_kg_s: float

    selected_dn: Optional[str]
    velocity_m_s: Optional[float]

    dp_total_pa: Optional[float]
    head_m: Optional[float]

    pump_name: Optional[str]
    pump_speed_ratio: Optional[float]
    head_margin_m: Optional[float]

    notes: str = ""
