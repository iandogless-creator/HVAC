"""
GeometryResolutionService — V3
------------------------------

Resolve geometric intent into explicit surfaces and volumes.

• Assembly only
• No CAD
• No physics
• No adjacency
• No wall/window subtraction (V4+)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

Point = Tuple[float, float]


@dataclass(slots=True)
class ResolvedSurface:
    """
    Minimal surface representation for V3 assembly.
    """
    name: str
    area_m2: float
    kind: str           # "wall", "roof", "floor", "window"
    u_value: float      # injected from construction preset


class GeometryResolutionService:
    """
    V3 geometry façade.

    Converts footprint + height + construction preset
    into explicit surfaces with areas.
    """

    def build_surfaces_from_footprint(
        self,
        footprint: List[Point],
        height_m: float,
        preset,
    ) -> List[ResolvedSurface]:
        """
        Build wall, roof, and floor surfaces.

        Windows are added later by opening attribution.
        """

        if len(footprint) < 3:
            raise ValueError("Footprint must have at least 3 points")

        # --- Perimeter ---
        perimeter = 0.0
        for i in range(len(footprint)):
            x1, y1 = footprint[i]
            x2, y2 = footprint[(i + 1) % len(footprint)]
            dx = x2 - x1
            dy = y2 - y1
            perimeter += (dx ** 2 + dy ** 2) ** 0.5

        wall_area = perimeter * height_m

        # --- Plan area (shoelace) ---
        area = 0.0
        for i in range(len(footprint)):
            x1, y1 = footprint[i]
            x2, y2 = footprint[(i + 1) % len(footprint)]
            area += x1 * y2 - x2 * y1
        plan_area = abs(area) * 0.5

        surfaces: List[ResolvedSurface] = []

        # Walls
        surfaces.append(
            ResolvedSurface(
                name="External Walls",
                area_m2=wall_area,
                kind="wall",
                u_value=preset.wall_u_value,
            )
        )

        # Roof
        surfaces.append(
            ResolvedSurface(
                name="Roof",
                area_m2=plan_area,
                kind="roof",
                u_value=preset.roof_u_value,
            )
        )

        # Floor
        surfaces.append(
            ResolvedSurface(
                name="Floor",
                area_m2=plan_area,
                kind="floor",
                u_value=preset.floor_u_value,
            )
        )

        return surfaces

    def volume_from_footprint(
        self,
        footprint: List[Point],
        height_m: float,
    ) -> float:
        """
        Simple volume = plan area × height.
        """

        area = 0.0
        for i in range(len(footprint)):
            x1, y1 = footprint[i]
            x2, y2 = footprint[(i + 1) % len(footprint)]
            area += x1 * y2 - x2 * y1

        plan_area = abs(area) * 0.5
        return plan_area * height_m
