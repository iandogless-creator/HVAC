# ================================================================
# HVAC/heatloss/dto/project_heatloss_results_dto.py
# ================================================================
"""
HVACgooee — Project Heat-Loss Results DTO (v1)

Container for multi-room heat-loss results.

Rules
-----
• DTO only
• No physics
• No GUI
• Aggregation only
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from HVAC_legacy.heatloss.dto.heatloss_results_dto import HeatLossResultDTO


@dataclass(slots=True)
class ProjectHeatLossResultsDTO:
    """
    Canonical multi-room heat-loss result container.
    """

    rooms: List[HeatLossResultDTO]

    @property
    def total_heat_loss_w(self) -> float:
        return sum(r.total_heat_loss_w for r in self.rooms)

    @property
    def total_fabric_heat_loss_w(self) -> float:
        return sum(r.total_fabric_heat_loss_w for r in self.rooms)

    @property
    def total_ventilation_heat_loss_w(self) -> float:
        return sum(r.ventilation_heat_loss_w for r in self.rooms)
