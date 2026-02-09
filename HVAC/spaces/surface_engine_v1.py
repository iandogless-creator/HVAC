"""
surface_engine_v1.py
--------------------

HVACgooee — Surface Engine v1

Purpose
=======
Given a Space (with:
    - polygon: list[(x, y)] in metres
    - height_m: float
),
generate a simple list of Surface objects.

This is the first "real physics" adjacency step:

    - Each polygon edge becomes a vertical surface (wall-like)
    - We also create a floor surface and a ceiling/roof surface

In v1, we make the following simplifying assumptions:

    - All vertical surfaces are EXTERNAL_WALL
      (adjacency / internal partitions come in later versions)
    - Floor is GROUND_FLOOR
    - Top is CEILING_ROOF
    - No U-values yet
    - No Y-values, psi-bridges, or dynamic mass yet

Outputs
-------
    surfaces: List[Surface]

Each Surface includes:
    - name
    - type
    - area_m2
    - length_m
    - height_m
    - orientation_deg (for vertical surfaces, 0–360°)

This module is *pure geometry + metadata*.
It does not perform any heat-loss calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from math import atan2, degrees, hypot
from typing import List, Tuple

from HVAC_legacy.spaces.space_types import Space


# ---------------------------------------------------------------------------
# Enums and Dataclasses
# ---------------------------------------------------------------------------

class SurfaceType(Enum):
    """Basic surface classification for v1."""
    EXTERNAL_WALL = auto()
    INTERNAL_PARTITION = auto()  # reserved for future versions
    GROUND_FLOOR = auto()
    CEILING_ROOF = auto()
    UNKNOWN = auto()


@dataclass
class Surface:
    """
    Geometric surface derived from a space.

    This does NOT yet contain U-values or construction data.
    It is purely geometric + classification metadata.

    For vertical surfaces:
        - length_m × height_m = area_m2
        - orientation_deg is the outward-facing azimuth (0–360°)

    For floor/roof surfaces:
        - area_m2 is the floor area
        - length_m and height_m can be used as descriptive placeholders
          (e.g. length_m = characteristic dimension, height_m = 0.0)
    """
    name: str
    surface_type: SurfaceType

    area_m2: float
    length_m: float
    height_m: float

    orientation_deg: float | None = None  # vertical surfaces only
    # Future fields (v2+):
    #   construction_id: str | None
    #   u_value_W_m2K: float | None
    #   adjacency: str | None


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _edge_orientation_deg(p0: Tuple[float, float],
                          p1: Tuple[float, float]) -> float:
    """
    Compute the azimuth (in degrees 0–360) of the NORMAL pointing
    *outward* from the edge p0→p1.

    Convention:
        - We take the edge vector v = p1 - p0
        - The outward normal is obtained by rotating v by -90°
          (assuming polygon is defined in a consistent winding order).
        - 0° = +X axis, 90° = +Y axis, etc.
    """
    x0, y0 = p0
    x1, y1 = p1
    dx = x1 - x0
    dy = y1 - y0

    # Edge vector angle
    edge_angle_rad = atan2(dy, dx)
    # Outward normal: rotate edge by -90° (clockwise)
    normal_angle_rad = edge_angle_rad - (3.141592653589793 / 2.0)
    angle_deg = degrees(normal_angle_rad)

    # Normalize to [0, 360)
    while angle_deg < 0.0:
        angle_deg += 360.0
    while angle_deg >= 360.0:
        angle_deg -= 360.0

    return angle_deg


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def generate_surfaces_for_space(space: Space) -> List[Surface]:
    """
    Generate a list of surfaces for a given Space.

    v1 rules:
        - Each polygon edge → vertical EXTERNAL_WALL surface
        - One GROUND_FLOOR surface (area = floor area)
        - One CEILING_ROOF surface (area = floor area)

    Parameters
    ----------
    space : Space
        The Space dataclass instance from HVAC.spaces.space_types

    Returns
    -------
    List[Surface]
    """
    polygon = space.polygon
    n = len(polygon)
    surfaces: List[Surface] = []

    # -------------------------
    # Vertical wall-like surfaces
    # -------------------------
    for i in range(n):
        p0 = polygon[i]
        p1 = polygon[(i + 1) % n]

        # Edge length
        length = hypot(p1[0] - p0[0], p1[1] - p0[1])
        if length <= 0.0:
            # Degenerate edge, skip
            continue

        height = space.height_m
        area = length * height
        orientation = _edge_orientation_deg(p0, p1)

        surf_name = f"{space.name}_wall_{i}"

        surf = Surface(
            name=surf_name,
            surface_type=SurfaceType.EXTERNAL_WALL,
            area_m2=area,
            length_m=length,
            height_m=height,
            orientation_deg=orientation,
        )
        surfaces.append(surf)

    # -------------------------
    # Floor surface
    # -------------------------
    floor_area = space.floor_area_m2()
    floor_surface = Surface(
        name=f"{space.name}_floor",
        surface_type=SurfaceType.GROUND_FLOOR,
        area_m2=floor_area,
        length_m=floor_area ** 0.5,  # characteristic dimension only
        height_m=0.0,
        orientation_deg=None,
    )
    surfaces.append(floor_surface)

    # -------------------------
    # Ceiling/Roof surface
    # -------------------------
    roof_surface = Surface(
        name=f"{space.name}_roof",
        surface_type=SurfaceType.CEILING_ROOF,
        area_m2=floor_area,
        length_m=floor_area ** 0.5,
        height_m=0.0,
        orientation_deg=None,
    )
    surfaces.append(roof_surface)

    return surfaces
