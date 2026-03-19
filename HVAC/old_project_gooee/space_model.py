"""
HVAC/project/space_model.py
---------------------------
# ⚠️ FROZEN — DO NOT EXTEND

HVACgooee — Space Model (v1)

v1 assumptions:
    • One project → one space → one polygon
    • Polygon is 2D, planar, closed implicitly
    • Height is uniform for the space
    • Geometry-derived quantities belong here
    • NO physics
    • NO controllers
    • NO GUI logic

This model exists to provide a stable contract between:
    • Geometry editors
    • Surface builders
    • Heat-loss engines
"""
"""
Project Gooee — Space Domain Model
---------------------------------

Role:
• Defines declarative spatial intent within a project
• Represents rooms / zones / thermal spaces

Rules:
• No calculations
• No file IO
• No GUI imports
• No ProjectState usage
• No inference or defaults

This module is part of the Project Gooee persistence layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple
import math


Point2D = Tuple[float, float]


@dataclass
class Space:
    """
    Represents a single enclosed space (v1).
    """

    id: str
    name: str
    polygon: List[Point2D]
    height_m: float = 2.4

    # --------------------------------------------------
    # Geometry helpers
    # --------------------------------------------------
    def floor_area_m2(self) -> float:
        """
        Returns floor area using the shoelace formula.
        """
        if len(self.polygon) < 3:
            return 0.0

        area = 0.0
        pts = self.polygon + [self.polygon[0]]

        for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
            area += (x1 * y2) - (x2 * y1)

        return abs(area) * 0.5

    @property
    def floor_area(self) -> float:
        """
        Alias for compatibility with legacy engines.
        """
        return self.floor_area_m2()

    @property
    def ceiling_area(self) -> float:
        """
        Flat ceiling assumed in v1.
        """
        return self.floor_area_m2()

    def wall_lengths(self) -> List[float]:
        """
        Returns individual wall lengths from polygon edges.
        """
        if len(self.polygon) < 2:
            return []

        lengths: List[float] = []
        pts = self.polygon + [self.polygon[0]]

        for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
            dx = x2 - x1
            dy = y2 - y1
            lengths.append(math.hypot(dx, dy))

        return lengths

    def perimeter_m(self) -> float:
        """
        Total perimeter length.
        """
        return sum(self.wall_lengths())

    def wall_areas_m2(self) -> List[float]:
        """
        Returns wall areas per edge.
        """
        return [length * self.height_m for length in self.wall_lengths()]

    def volume_m3(self) -> float:
        """
        Simple volume = floor area × height.
        """
        return self.floor_area_m2() * self.height_m
