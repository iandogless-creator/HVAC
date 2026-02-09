"""
heatloss_dto.py
---------------

GUI-facing Data Transfer Objects (DTOs) for Heat-Loss results.

Rules:
✔ Read-only
✔ No physics
✔ No geometry mutation
✔ Safe for GUI consumption
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ================================================================
# SURFACE DTOs
# ================================================================
@dataclass(frozen=True)
class WallHeatLossDTO:
    name: str
    facade: str
    area_m2: float
    u_value: float
    heat_loss_w_per_k: float


@dataclass(frozen=True)
class OpeningHeatLossDTO:
    name: str
    area_m2: float
    u_value: float
    heat_loss_w_per_k: float


# ================================================================
# AGGREGATE RESULT DTO
# ================================================================
@dataclass(frozen=True)
class HeatLossResultDTO:
    """
    Single-space heat-loss result (v1).

    All values are W/K.
    """

    walls: List[WallHeatLossDTO]
    openings: List[OpeningHeatLossDTO]

    total_wall_heat_loss_w_per_k: float
    total_opening_heat_loss_w_per_k: float
    total_fabric_heat_loss_w_per_k: float
