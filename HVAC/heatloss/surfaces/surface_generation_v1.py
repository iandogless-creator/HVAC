# ============================================================
# HVACgooee — Heat-Loss Surface Generation v1 (from Space Polygon)
# File: HVAC/heatloss/surfaces/surface_generation_v1.py
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import atan2, degrees, hypot
from typing import Dict, List, Optional, Tuple

Point = Tuple[float, float]


class SurfaceType(str, Enum):
    FLOOR = "floor"
    CEILING = "ceiling"
    WALL = "wall"


@dataclass(frozen=True)
class SurfaceV1:
    """
    Heat-loss surface container (v1).

    Notes:
    - No constructions/U-values here (v1 scope)
    - No adjacency inference (v1 scope)
    - Walls are generated from polygon edges
    """
    surface_id: str
    surface_type: SurfaceType

    # Geometry
    area_m2: float

    # WALL-only fields
    length_m: Optional[float] = None
    height_m: Optional[float] = None
    p0: Optional[Point] = None
    p1: Optional[Point] = None

    # Orientation (for later)
    # Bearing is degrees clockwise from North (0=N, 90=E, 180=S, 270=W)
    bearing_deg: Optional[float] = None

    # Free-form metadata (safe for future extensions)
    meta: Optional[Dict[str, object]] = None


# ------------------------------------------------------------
# Pure geometry helpers (v1-safe)
# ------------------------------------------------------------

def polygon_area_m2(poly: List[Point]) -> float:
    """Shoelace area for OPEN polygons."""
    if len(poly) < 3:
        return 0.0
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return abs(s) * 0.5


def polygon_signed_area_m2(poly: List[Point]) -> float:
    """Signed area: positive for CCW, negative for CW (for OPEN polygons)."""
    if len(poly) < 3:
        return 0.0
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s * 0.5


def segment_length_m(p0: Point, p1: Point) -> float:
    return hypot(p1[0] - p0[0], p1[1] - p0[1])


def wall_bearing_deg(p0: Point, p1: Point) -> float:
    """
    Bearing of the wall's outward normal, degrees clockwise from North.

    Coordinate frame (your v1 rule):
      +x east, +y north

    We compute the edge direction p0->p1, then take the outward normal
    based on polygon winding:
      - For CCW polygon: outward is to the RIGHT of edge direction
      - For CW polygon: outward is to the LEFT of edge direction
    """
    # This function expects caller to pass an "outward" normal vector already
    # OR uses a default CCW assumption is unsafe.
    raise RuntimeError("Use bearing from normal vector (see _bearing_from_normal).")


def _bearing_from_normal(nx: float, ny: float) -> float:
    """
    Convert a normal vector (nx, ny) to bearing degrees clockwise from North.
    Bearing = atan2(East, North) = atan2(nx, ny)
    """
    b = degrees(atan2(nx, ny))
    if b < 0:
        b += 360.0
    return b


def _validate_polygon_open(poly: List[Point]) -> None:
    if poly is None or len(poly) < 3:
        raise ValueError("Space polygon must have at least 3 points (OPEN polygon).")
    # If someone accidentally provides a closed ring, accept but de-close it.
    # (We do not mutate input here; handled in generator.)


# ------------------------------------------------------------
# Surface generation (v1)
# ------------------------------------------------------------

def generate_surfaces_from_polygon_v1(
    *,
    space_key: str,
    polygon: List[Point],
    height_m: float,
) -> List[SurfaceV1]:
    """
    Generate v1 heat-loss surfaces from a space footprint polygon (OPEN).

    Produces:
      - 1x FLOOR
      - 1x CEILING
      - Nx WALL (one per edge)

    v1 assumptions:
      - All perimeter edges are external walls
      - No adjacency inference
      - No openings yet
      - Height is uniform
    """
    _validate_polygon_open(polygon)

    # Accept closed-ring input, convert to open (without mutating caller list)
    poly = list(polygon)
    if len(poly) >= 4 and poly[0] == poly[-1]:
        poly = poly[:-1]

    if height_m <= 0:
        raise ValueError(f"height_m must be > 0. Got: {height_m}")

    # Determine winding for outward normal selection
    signed_area = polygon_signed_area_m2(poly)
    ccw = signed_area >= 0.0  # treat 0 as CCW-ish (degenerate cases handled earlier)

    floor_area = polygon_area_m2(poly)

    surfaces: List[SurfaceV1] = []

    # FLOOR
    surfaces.append(
        SurfaceV1(
            surface_id=f"{space_key}:FLOOR",
            surface_type=SurfaceType.FLOOR,
            area_m2=floor_area,
            meta={"source": "polygon"},
        )
    )

    # CEILING
    surfaces.append(
        SurfaceV1(
            surface_id=f"{space_key}:CEILING",
            surface_type=SurfaceType.CEILING,
            area_m2=floor_area,
            meta={"source": "polygon"},
        )
    )

    # WALLS from edges
    n = len(poly)
    for i in range(n):
        p0 = poly[i]
        p1 = poly[(i + 1) % n]

        L = segment_length_m(p0, p1)
        if L <= 0:
            # Skip zero-length edges (bad input or repeated points)
            continue

        # Edge direction vector
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]

        # Outward normal depends on winding:
        # CCW polygon => interior is LEFT of edges => outward is RIGHT normal
        # CW polygon  => interior is RIGHT of edges => outward is LEFT normal
        if ccw:
            nx, ny = (dy, -dx)   # right normal
        else:
            nx, ny = (-dy, dx)   # left normal

        # Normalise for stable bearing (optional but nice)
        mag = hypot(nx, ny)
        if mag > 0:
            nx /= mag
            ny /= mag

        bearing = _bearing_from_normal(nx, ny)

        surfaces.append(
            SurfaceV1(
                surface_id=f"{space_key}:W{i+1}",
                surface_type=SurfaceType.WALL,
                area_m2=L * height_m,
                length_m=L,
                height_m=height_m,
                p0=p0,
                p1=p1,
                bearing_deg=bearing,
                meta={
                    "edge_index": i,
                    "polygon_winding": "CCW" if ccw else "CW",
                    "normal": (nx, ny),
                },
            )
        )

    return surfaces


def generate_surfaces_for_space_v1(space, *, space_key: str) -> List[SurfaceV1]:
    """
    Convenience wrapper if your Space has:
      - space.polygon (OPEN list of (x,y))
      - space.height_m
    """
    return generate_surfaces_from_polygon_v1(
        space_key=space_key,
        polygon=getattr(space, "polygon", []),
        height_m=float(getattr(space, "height_m", 2.4)),
    )
