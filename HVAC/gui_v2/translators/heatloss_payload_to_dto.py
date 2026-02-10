"""
heatloss_payload_to_dto.py
-------------------------

Translate core HeatLossPayload into GUI-safe DTOs.

This module is the ONLY bridge between:
    • HVAC.heatloss (core domain)
    • HVAC.gui_v2 (presentation layer)

Rules
-----
✔ Pure translation only
✔ No physics
✔ No mutation
✔ No Qt / GUI imports
✔ No legacy imports
"""

from __future__ import annotations

from typing import List

from HVAC.heatloss.heatloss_payload_v1 import HeatLossPayload
from HVAC.gui_v2.dto.heatloss_dto import (
    HeatLossResultDTO,
    WallHeatLossDTO,
    OpeningHeatLossDTO,
)


# ================================================================
# TRANSLATION
# ================================================================

def translate_heatloss_payload_to_dto(
    payload: HeatLossPayload,
) -> HeatLossResultDTO:
    """
    Convert canonical HeatLossPayload → GUI-facing HeatLossResultDTO.

    This function performs STRUCTURAL TRANSLATION ONLY.
    """

    wall_dtos: List[WallHeatLossDTO] = []
    opening_dtos: List[OpeningHeatLossDTO] = []

    # ---------------- Walls ----------------
    for wall in payload.wall_losses:
        wall_dtos.append(
            WallHeatLossDTO(
                name=wall.name,
                facade=wall.facade,
                area_m2=wall.area_m2,
                u_value=wall.u_value,
                heat_loss_w_per_k=wall.heat_loss_w_per_k,
            )
        )

    # ---------------- Openings ----------------
    for opening in payload.opening_losses:
        opening_dtos.append(
            OpeningHeatLossDTO(
                name=opening.name,
                area_m2=opening.area_m2,
                u_value=opening.u_value,
                heat_loss_w_per_k=opening.heat_loss_w_per_k,
            )
        )

    # ---------------- Aggregate ----------------
    return HeatLossResultDTO(
        walls=wall_dtos,
        openings=opening_dtos,
        total_wall_heat_loss_w_per_k=payload.total_wall_heat_loss_w_per_k,
        total_opening_heat_loss_w_per_k=payload.total_opening_heat_loss_w_per_k,
        total_fabric_heat_loss_w_per_k=payload.total_fabric_heat_loss_w_per_k,
    )
