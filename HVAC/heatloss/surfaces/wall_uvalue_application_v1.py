"""
wall_uvalue_application_v1.py
-----------------------------

Apply U-values to wall surfaces.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class WallHeatLossResult:
    facade: str
    area_m2: float
    u_value: float
    heat_loss_w_per_k: float


def apply_uvalues_to_walls(
    *,
    wall_attributions,
    wall_uvalues,
) -> List[WallHeatLossResult]:
    results = []

    default_u = wall_uvalues.get("all", 0.35)

    for wall in wall_attributions:
        u = wall_uvalues.get(wall.facade, default_u)
        results.append(
            WallHeatLossResult(
                facade=wall.facade,
                area_m2=wall.area_m2,
                u_value=u,
                heat_loss_w_per_k=wall.area_m2 * u,
            )
        )

    return results
