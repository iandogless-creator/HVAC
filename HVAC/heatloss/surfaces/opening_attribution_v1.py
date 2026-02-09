"""
opening_attribution_v1.py
-------------------------

Resolve openings into heat-loss opening surfaces.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class OpeningHeatLossSurface:
    name: str
    area_m2: float


def attribute_openings_for_heatloss(
    resolved_openings,
    *,
    default_height_m: float,
) -> List[OpeningHeatLossSurface]:
    surfaces = []

    for i, opening in enumerate(resolved_openings):
        width = opening.width_m
        height = opening.height_m or default_height_m
        area = width * height

        surfaces.append(
            OpeningHeatLossSurface(
                name=f"Opening {i + 1}",
                area_m2=area,
            )
        )

    return surfaces
