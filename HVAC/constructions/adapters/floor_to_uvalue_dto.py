# ======================================================================
# HVAC/constructions/adapters/floor_to_uvalue_dto.py
# ======================================================================

from __future__ import annotations

from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)
from HVAC_legacy.constructions.construction_preset import SurfaceClass


def build_floor_uvalue_dto(
    *,
    construction_id: str,
    u_value: float,
) -> ConstructionUValueResultDTO:
    """
    Adapter: Floor U-value → ConstructionUValueResultDTO

    NOTE
    ----
    • Preset / lookup driven for now
    """

    if u_value <= 0.0:
        raise ValueError("Floor u_value must be positive.")

    return ConstructionUValueResultDTO(
        surface_class=SurfaceClass.FLOOR,
        construction_ref=construction_id,
        u_value=u_value,
    )
