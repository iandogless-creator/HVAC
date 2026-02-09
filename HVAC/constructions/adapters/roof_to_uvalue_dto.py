# ======================================================================
# HVAC/constructions/adapters/roof_to_uvalue_dto.py
# ======================================================================

from __future__ import annotations

from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)
from HVAC_legacy.constructions.construction_preset import SurfaceClass
from HVAC_legacy.constructions.engines.pitched_roof_calculator import (
    compute_roof_performance,
    PitchedRoof,
)


def build_pitched_roof_uvalue_dto(
    *,
    roof: PitchedRoof,
    construction_id: str,
) -> ConstructionUValueResultDTO:
    """
    Adapter: Pitched roof engine → ConstructionUValueResultDTO

    RULES (LOCKED)
    --------------
    • Emits U-value ONLY
    • Ignores comfort-adjusted variants
    """

    result = compute_roof_performance(roof)
    u_value = result["U_value"]

    return ConstructionUValueResultDTO(
        surface_class=SurfaceClass.ROOF,
        construction_ref=construction_id,
        u_value=u_value,
    )
