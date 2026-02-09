"""
edge_bearing_utils_v1.py
------------------------

HVACgooee — Edge / Bearing Utilities v1 (Pure Math)

Purpose
-------
Provide deterministic, UI-agnostic helpers for:

    • Orientation parsing (DMS <-> decimal degrees)
    • Polygon edge extraction
    • Local edge angle (geometry-only)
    • Global edge bearing (space.orientation_deg + local_edge_angle)
    • Projection of a point onto an edge, and distance-along-edge (for openings)
    • Simple nearest-edge selection (for UI to call, but no UI inside)

Design Rules (v1.5)
-------------------
✔ No CAD engine behaviour
✔ No wall thickness
✔ No snapping semantics
✔ No polygon rotation
✔ Orientation stored on SPACE and applied only to interpretation
✔ Geometry is a footprint polyline: List[(x, y)] in world meters

All angles:
    • Local edge angle: 0° = East, 90° = North (math convention, CCW)
    • Global bearing:   0° = North, 90° = East (bearing convention, CW)

We explicitly convert between these conventions.
"""

# ================================================================
# BEGIN IMPORTS
# ================================================================
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, isfinite, radians, sin
from typing import Iterable, List, Optional, Sequence, Tuple

# END IMPORTS
# ================================================================

Point = Tuple[float, float]


# ================================================================
# BEGIN DATA STRUCTURES
# ================================================================
@dataclass(frozen=True)
class EdgeRef:
    """References an edge in a polygon by index.

    Edge i is from footprint[i] -> footprint[i+1], with wrap to 0 for last edge.
    """
    edge_index: int


@dataclass(frozen=True)
class EdgeGeometry:
    """Computed geometry for one polygon edge."""
    edge_index: int
    a: Point
    b: Point
    length_m: float
    ux: float  # unit vector x (a -> b)
    uy: float  # unit vector y (a -> b)
    local_angle_math_deg: float  # 0°=East, 90°=North, CCW


@dataclass(frozen=True)
class ProjectionResult:
    """Result of projecting point P onto an edge segment AB."""
    edge_index: int
    closest_point: Point
    t01: float                 # clamped param along segment [0..1]
    distance_to_edge_m: float  # perpendicular/closest distance
    distance_along_edge_m: float  # from A to closest point along edge (0..length)


# END DATA STRUCTURES
# ================================================================


# ================================================================
# BEGIN ORIENTATION HELPERS (DMS)
# ================================================================
def normalize_deg_360(angle_deg: float) -> float:
    """Normalize any angle to [0, 360)."""
    if not isfinite(angle_deg):
        raise ValueError("Angle must be finite.")
    angle = angle_deg % 360.0
    # Guard against 360.0 due to float quirks
    return 0.0 if angle >= 360.0 else angle


def dms_to_decimal_deg(deg: int, minutes: int, seconds: float) -> float:
    """Convert DMS to decimal degrees, normalized to [0, 360).

    Accepts:
        deg: 0..359 (recommended)
        minutes: 0..59
        seconds: 0..59.999...

    If values overflow, caller should normalize before calling this
    (or use normalize_dms()).
    """
    if not isinstance(deg, int) or not isinstance(minutes, int):
        raise TypeError("deg and minutes must be integers.")
    if seconds is None or not isfinite(seconds):
        raise ValueError("seconds must be a finite number.")
    decimal = float(deg) + (float(minutes) / 60.0) + (float(seconds) / 3600.0)
    return normalize_deg_360(decimal)


def decimal_deg_to_dms(angle_deg: float) -> Tuple[int, int, float]:
    """Convert decimal degrees in [0, 360) to (deg, min, sec)."""
    a = normalize_deg_360(angle_deg)
    deg = int(a)
    rem_min = (a - deg) * 60.0
    minutes = int(rem_min)
    seconds = (rem_min - minutes) * 60.0
    # Clamp tiny float noise at boundaries (e.g. 59.999999 -> 60)
    if seconds >= 60.0 - 1e-9:
        seconds = 0.0
        minutes += 1
    if minutes >= 60:
        minutes = 0
        deg = (deg + 1) % 360
    return deg, minutes, float(seconds)


def normalize_dms(deg: int, minutes: int, seconds: float) -> Tuple[int, int, float]:
    """Normalize DMS with carry/borrow so that:
        deg in 0..359, minutes in 0..59, seconds in 0..59.999...

    This is useful for spin-box wrap-around behaviour.
    """
    if not isinstance(deg, int) or not isinstance(minutes, int):
        raise TypeError("deg and minutes must be integers.")
    if seconds is None or not isfinite(seconds):
        raise ValueError("seconds must be a finite number.")

    # Carry seconds to minutes
    total_seconds = minutes * 60.0 + seconds
    # Handle negative too (borrow)
    carry_min = int(total_seconds // 60.0)
    sec = total_seconds - carry_min * 60.0
    if sec < 0:
        # Fix if Python // behaved unexpectedly for negatives
        carry_min -= 1
        sec += 60.0

    # Now minutes = carry_min, carry to degrees
    total_minutes = deg * 60 + carry_min
    carry_deg = total_minutes // 60
    min_ = total_minutes - carry_deg * 60
    if min_ < 0:
        carry_deg -= 1
        min_ += 60

    deg_norm = int(carry_deg % 360)
    return deg_norm, int(min_), float(sec)


# END ORIENTATION HELPERS
# ================================================================


# ================================================================
# BEGIN ANGLE CONVENTION CONVERSIONS
# ================================================================
def math_angle_to_bearing_deg(math_deg: float) -> float:
    """Convert math angle (0°=East, CCW) to bearing (0°=North, CW)."""
    # Bearing = 90 - math_angle (then normalize)
    return normalize_deg_360(90.0 - math_deg)


def bearing_to_math_angle_deg(bearing_deg: float) -> float:
    """Convert bearing (0°=North, CW) to math angle (0°=East, CCW)."""
    # math = 90 - bearing
    return normalize_deg_360(90.0 - normalize_deg_360(bearing_deg))


# END ANGLE CONVERSION
# ================================================================


# ================================================================
# BEGIN POLYGON / EDGE GEOMETRY
# ================================================================
def _validate_footprint(footprint: Sequence[Point]) -> None:
    if footprint is None or len(footprint) < 3:
        raise ValueError("Footprint must contain at least 3 points.")
    for p in footprint:
        if p is None or len(p) != 2:
            raise ValueError("Each footprint point must be a 2-tuple (x, y).")
        x, y = p
        if not (isfinite(x) and isfinite(y)):
            raise ValueError("Footprint points must be finite numbers.")


def iter_edges(footprint: Sequence[Point]) -> Iterable[Tuple[int, Point, Point]]:
    """Yield (edge_index, A, B) for each edge with wrap-around."""
    _validate_footprint(footprint)
    n = len(footprint)
    for i in range(n):
        a = footprint[i]
        b = footprint[(i + 1) % n]
        yield i, a, b


def edge_geometry(footprint: Sequence[Point], edge_index: int) -> EdgeGeometry:
    """Compute EdgeGeometry for a given edge index."""
    _validate_footprint(footprint)
    n = len(footprint)
    if edge_index < 0 or edge_index >= n:
        raise IndexError(f"edge_index out of range: {edge_index} (n={n})")

    a = footprint[edge_index]
    b = footprint[(edge_index + 1) % n]
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = hypot(dx, dy)
    if length <= 1e-12:
        # Degenerate edge; still return but unit vector 0 and angle 0
        return EdgeGeometry(edge_index=edge_index, a=a, b=b, length_m=0.0, ux=0.0, uy=0.0, local_angle_math_deg=0.0)

    ux = dx / length
    uy = dy / length
    # atan2 gives angle in radians from +x (East), CCW positive
    ang = atan2(dy, dx)
    ang_deg = normalize_deg_360(ang * 180.0 / 3.141592653589793)
    return EdgeGeometry(edge_index=edge_index, a=a, b=b, length_m=length, ux=ux, uy=uy, local_angle_math_deg=ang_deg)


def local_edge_bearing_deg(footprint: Sequence[Point], edge_index: int) -> float:
    """Bearing of the edge direction A->B in bearing convention (0°=North, CW)."""
    eg = edge_geometry(footprint, edge_index)
    return math_angle_to_bearing_deg(eg.local_angle_math_deg)


def global_edge_bearing_deg(
    footprint: Sequence[Point],
    edge_index: int,
    space_orientation_deg: float,
) -> float:
    """Global edge bearing applying space orientation (v1.5 rule).

    Interpretation:
        global = (space.orientation_deg + local_edge_bearing) % 360
    where local_edge_bearing is derived from geometry alone.
    """
    local_bear = local_edge_bearing_deg(footprint, edge_index)
    return normalize_deg_360(normalize_deg_360(space_orientation_deg) + local_bear)


def polygon_signed_area_m2(footprint: Sequence[Point]) -> float:
    """Signed area (shoelace). CCW footprint gives positive area."""
    _validate_footprint(footprint)
    area2 = 0.0
    n = len(footprint)
    for i in range(n):
        x1, y1 = footprint[i]
        x2, y2 = footprint[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1
    return 0.5 * area2


def polygon_area_m2(footprint: Sequence[Point]) -> float:
    """Absolute polygon area in m²."""
    return abs(polygon_signed_area_m2(footprint))


# END POLYGON / EDGE GEOMETRY
# ================================================================


# ================================================================
# BEGIN PROJECTION / DISTANCE ALONG EDGE (OPENINGS SUPPORT)
# ================================================================
def project_point_to_edge(footprint: Sequence[Point], edge_index: int, p: Point) -> ProjectionResult:
    """Project point P onto segment AB (edge_index), clamped to segment.

    Returns:
        closest point on segment,
        t01 clamped in [0..1],
        distance to segment,
        distance along edge from A.
    """
    eg = edge_geometry(footprint, edge_index)
    ax, ay = eg.a
    bx, by = eg.b
    px, py = p

    dx = bx - ax
    dy = by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        # Degenerate edge: closest is A
        dist = hypot(px - ax, py - ay)
        return ProjectionResult(
            edge_index=edge_index,
            closest_point=(ax, ay),
            t01=0.0,
            distance_to_edge_m=dist,
            distance_along_edge_m=0.0,
        )

    t = ((px - ax) * dx + (py - ay) * dy) / denom
    t_clamped = 0.0 if t < 0.0 else (1.0 if t > 1.0 else float(t))

    cx = ax + t_clamped * dx
    cy = ay + t_clamped * dy
    dist = hypot(px - cx, py - cy)
    along = t_clamped * eg.length_m
    return ProjectionResult(
        edge_index=edge_index,
        closest_point=(cx, cy),
        t01=t_clamped,
        distance_to_edge_m=dist,
        distance_along_edge_m=along,
    )


def point_on_edge_by_offset(footprint: Sequence[Point], edge_index: int, offset_m: float) -> Point:
    """Return a point along edge at offset from A (clamped to [0, length])."""
    eg = edge_geometry(footprint, edge_index)
    if eg.length_m <= 1e-12:
        return eg.a
    off = max(0.0, min(float(offset_m), eg.length_m))
    return (eg.a[0] + eg.ux * off, eg.a[1] + eg.uy * off)


def opening_span_on_edge(
    footprint: Sequence[Point],
    edge_index: int,
    offset_m: float,
    width_m: float,
) -> Tuple[Point, Point]:
    """Return (start_point, end_point) for an opening placed on an edge.

    This does NOT modify geometry. It simply returns the two points along the edge.

    offset_m: distance from edge start A
    width_m: opening width (>= 0)
    """
    eg = edge_geometry(footprint, edge_index)
    if eg.length_m <= 1e-12:
        return eg.a, eg.a

    off = max(0.0, min(float(offset_m), eg.length_m))
    w = max(0.0, float(width_m))
    end_off = max(0.0, min(off + w, eg.length_m))
    p0 = (eg.a[0] + eg.ux * off, eg.a[1] + eg.uy * off)
    p1 = (eg.a[0] + eg.ux * end_off, eg.a[1] + eg.uy * end_off)
    return p0, p1


def nearest_edge_to_point(
    footprint: Sequence[Point],
    p: Point,
    max_distance_m: Optional[float] = None,
) -> Optional[ProjectionResult]:
    """Find nearest edge of polygon footprint to point P by projection distance.

    This is useful for UI hit-testing, but remains a pure math function.

    If max_distance_m is provided, returns None if the closest edge is farther.
    """
    _validate_footprint(footprint)
    best: Optional[ProjectionResult] = None
    best_dist = float("inf")
    for i, _, _ in iter_edges(footprint):
        pr = project_point_to_edge(footprint, i, p)
        if pr.distance_to_edge_m < best_dist:
            best_dist = pr.distance_to_edge_m
            best = pr

    if best is None:
        return None
    if max_distance_m is not None and best.distance_to_edge_m > float(max_distance_m):
        return None
    return best


# END PROJECTION / DISTANCE
# ================================================================


# ================================================================
# BEGIN SMALL CONVENIENCE HELPERS
# ================================================================
def bearing_to_cardinal_8(bearing_deg: float) -> str:
    """Return 8-wind label: N, NE, E, SE, S, SW, W, NW (display helper)."""
    b = normalize_deg_360(bearing_deg)
    # Center bins on the cardinal/intercardinal directions.
    labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    # Each bin is 45°, offset by 22.5° for nearest
    idx = int(((b + 22.5) % 360.0) // 45.0)
    return labels[idx]


def edge_length_m(footprint: Sequence[Point], edge_index: int) -> float:
    """Length of edge in meters."""
    return edge_geometry(footprint, edge_index).length_m


# END CONVENIENCE
# ================================================================
