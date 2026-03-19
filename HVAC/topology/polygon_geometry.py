# ======================================================================
# HVAC/topology/polygon_geometry.py
# ======================================================================

from __future__ import annotations
from typing import Iterable, Tuple, List


Point = Tuple[float, float]


# ----------------------------------------------------------------------
# Polygon Area (Shoelace Formula)
# ----------------------------------------------------------------------
def polygon_area_m2(points: Iterable[Point]) -> float:
    """
    Compute polygon area using the shoelace formula.

    Parameters
    ----------
    points:
        Iterable of (x, y) coordinates in metres.

    Returns
    -------
    float
        Area in square metres.

    Notes
    -----
    • Polygon must be non-self-intersecting
    • First/last point do not need to repeat
    """

    pts: List[Point] = list(points)

    if len(pts) < 3:
        return 0.0

    area = 0.0

    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]

        area += (x1 * y2) - (x2 * y1)

    return abs(area) * 0.5


# ----------------------------------------------------------------------
# Bounding Rectangle (DEV compatibility helper)
# ----------------------------------------------------------------------
def bounding_box_dimensions(points: Iterable[Point]) -> Tuple[float, float]:
    """
    Compute bounding box dimensions for polygon.

    Returns
    -------
    (length_m, width_m)

    DEV use only — compatibility with legacy readiness checks.
    """

    pts = list(points)

    if not pts:
        return 0.0, 0.0

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    length = max(xs) - min(xs)
    width = max(ys) - min(ys)

    return abs(length), abs(width)