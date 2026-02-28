# ======================================================================
# HVAC/heatloss/dto/fabric_results.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True, slots=True)
class FabricSurfaceResultDTO:
    """
    Phase II-C (LOCKED): surface-level fabric heat-loss result.

    Canonical physics:
        qf_W = u_value_W_m2K * area_m2 * delta_t_K
    """
    surface_id: str
    room_id: str
    surface_class: str

    area_m2: float
    u_value_W_m2K: float
    delta_t_K: float

    qf_W: float


@dataclass(frozen=True, slots=True)
class FabricHeatLossResultDTO:
    """
    Phase II-C (LOCKED): project-level fabric heat-loss result.

    Rules:
    • Pure aggregation of FabricSurfaceResultDTO
    • ΣQf = sum(surface.qf_W)
    • Optional room rollups are convenience views only (still pure)
    """
    project_id: str
    internal_design_temp_C: float
    external_design_temp_C: float
    delta_t_K: float

    surfaces: List[FabricSurfaceResultDTO]

    total_qf_W: float
    total_area_m2: float

    # Convenience rollups (still deterministic)
    qf_by_room_W: Dict[str, float]
    area_by_room_m2: Dict[str, float]