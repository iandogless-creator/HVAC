# ======================================================================
# HVAC/constructions/adapters/window_to_uvalue_dto.py
# ======================================================================

from __future__ import annotations

from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)
from HVAC_legacy.constructions.construction_preset import SurfaceClass
from HVAC_legacy.constructions.engines.window_calculation_engine import (
    WindowConstruction,
    compute_window_performance,
)


def build_window_uvalue_dto(
    *,
    construction: WindowConstruction,
    width_m: float,
    height_m: float,
    construction_id: str,
) -> ConstructionUValueResultDTO:
    """
    Adapter: Window engine → ConstructionUValueResultDTO

    RULES (LOCKED)
    --------------
    • Emits Uw ONLY
    • No frame breakdown
    """

    result = compute_window_performance(
        construction=construction,
        width_m=width_m,
        height_m=height_m,
    )

    u_value = result.Uw_W_m2K

    return ConstructionUValueResultDTO(
        surface_class=SurfaceClass.WINDOW,
        construction_ref=construction_id,
        u_value=u_value,
    )
