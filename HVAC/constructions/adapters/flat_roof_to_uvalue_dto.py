#======================================================================
# HVAC/constructions/adapters/flat_roof_to_uvalue_dto.py
# ======================================================================

from __future__ import annotations

from HVAC.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)
from HVAC.constructions.construction_preset import SurfaceClass


def build_flat_roof_uvalue_dto(
    *,
    construction_id: str,
    u_value: float,
) -> ConstructionUValueResultDTO:
    """
    Adapter: Flat roof (preset-only placeholder)

    NOTE
    ----
    • No engine yet
    • Registry must supply u_value explicitly
    """

    if u_value <= 0.0:
        raise ValueError("Flat roof u_value must be positive.")

    return ConstructionUValueResultDTO(
        surface_class=SurfaceClass.ROOF,
        construction_ref=construction_id,
        u_value=u_value,
    )

