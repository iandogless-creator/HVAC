# ======================================================================
# BEGIN FILE: HVAC/heatloss/adapters/engine_to_dto.py
# ======================================================================
"""
engine_to_dto.py
----------------

HVACgooee — Heat Loss Engine → GUI DTO Adapter (v1/v3)

Purpose
-------
Translate engine-domain heat loss results into GUI-facing DTOs.

RULES
-----
• Imports engines, NEVER GUI
• Performs NO calculations
• Pure data translation only
"""

from __future__ import annotations

from typing import Any, List

from HVAC_legacy.heatloss.dto.heatloss_results_dto import (
    HeatLossResultDTO,
    BoundaryLossDTO,
)


def build_heatloss_dto(engine_result: Any) -> HeatLossResultDTO:
    """
    Convert single-room engine result → HeatLossResultDTO.

    Supports v3 RoomHeatLossResult shape:
        engine_result.boundaries[*].{element_type, area_m2, u_value, construction_ref,
                                    construction_name, heat_loss_w}
        engine_result.ventilation_heat_loss_w
        engine_result.total_fabric_heat_loss_w
        engine_result.total_heat_loss_w
    """

    boundaries: List[BoundaryLossDTO] = []

    for b in getattr(engine_result, "boundaries", []):
        # Prefer human readable name if present, otherwise fall back to ref.
        construction_id = getattr(b, "construction_name", None) or getattr(b, "construction_ref", None)

        boundaries.append(
            BoundaryLossDTO(
                element_type=getattr(b, "element_type", "—"),
                area_m2=float(getattr(b, "area_m2", 0.0)),
                u_value=float(getattr(b, "u_value", 0.0)),
                u_source=str(getattr(b, "construction_ref", "unknown")),
                construction_id=construction_id,
                heat_loss_w=float(getattr(b, "heat_loss_w", 0.0)),
            )
        )

    vent_w = float(getattr(engine_result, "ventilation_heat_loss_w", 0.0))
    vent_method = "ACH (v3)"
    if getattr(engine_result, "ventilation", None) is not None:
        vent_method = str(getattr(engine_result.ventilation, "method", "ACH (v3)"))

    return HeatLossResultDTO(
        room_name=str(getattr(engine_result, "room_name", "—")),
        internal_temp_c=float(getattr(engine_result, "internal_temp_c", 0.0)),
        room_volume_m3=None,  # engine may know volume; GUI room volume contract stays optional
        ventilation_method=vent_method,
        ventilation_heat_loss_w=vent_w,
        boundaries=boundaries,
        total_fabric_heat_loss_w=float(getattr(engine_result, "total_fabric_heat_loss_w", 0.0)),
        total_heat_loss_w=float(getattr(engine_result, "total_heat_loss_w", 0.0)),
    )


# ======================================================================
# END FILE: HVAC/heatloss/adapters/engine_to_dto.py
# ======================================================================
