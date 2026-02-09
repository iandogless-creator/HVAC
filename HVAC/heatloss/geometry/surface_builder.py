"""
surface_builder.py
------------------

HVACgooee — Geometry → Surface Derivation (v1)

Converts Space geometry into abstract thermal surfaces.

V1 OUTPUT:
    • wall surfaces (vertical, external)
    • floor surface
    • ceiling surface

NO adjacency
NO constructions
NO physics
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from HVAC_legacy.spaces.space_types import Space


# ==========================================================
# Surface Model (v1)
# ==========================================================
@dataclass
class Surface:
    """
    Abstract thermal surface.

    kind:
        • 'wall'
        • 'floor'
        • 'ceiling'
    """
    kind: str
    area_m2: float
    space_name: str


# ==========================================================
# Builders
# ==========================================================
def build_surfaces_from_space(space: Space) -> List[Surface]:
    """
    Build surfaces for a single Space.

    Requires:
        • space.polygon (≥ 3 points)
        • space.height_m
    """
    surfaces: List[Surface] = []

    if not space.polygon or len(space.polygon) < 3:
        return surfaces

    # ---- Floor + ceiling
    floor_area = space.floor_area
    if floor_area > 0:
        surfaces.append(
            Surface("floor", floor_area, space.name)
        )
        surfaces.append(
            Surface("ceiling", floor_area, space.name)
        )

    # ---- Walls (per edge × height)
    pts = space.polygon
    h = space.height_m

    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        area = length * h

        if area > 0:
            surfaces.append(
                Surface("wall", area, space.name)
            )

    return surfaces


def build_surfaces_for_project(project) -> List[Surface]:
    """
    Build surfaces for all spaces in a project.
    """
    all_surfaces: List[Surface] = []

    spaces = getattr(project, "spaces", [])
    for space in spaces:
        all_surfaces.extend(build_surfaces_from_space(space))

    return all_surfaces
