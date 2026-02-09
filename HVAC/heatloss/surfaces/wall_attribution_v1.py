"""
wall_attribution_v1.py
----------------------

Generate gross wall surfaces minus openings.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class WallHeatLossSurface:
    facade: str
    area_m2: float


def attribute_walls_for_heatloss(
    *,
    footprint,
    space_orientation_deg,
    space_height_m,
    opening_attributions,
) -> List[WallHeatLossSurface]:
    perimeter = 0.0
    for (x1, y1), (x2, y2) in zip(footprint, footprint[1:] + footprint[:1]):
        perimeter += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    gross_wall_area = perimeter * space_height_m
    opening_area = sum(o.area_m2 for o in opening_attributions)

    net_wall_area = max(gross_wall_area - opening_area, 0.0)

    return [
        WallHeatLossSurface(
            facade="all",
            area_m2=net_wall_area,
        )
    ]

