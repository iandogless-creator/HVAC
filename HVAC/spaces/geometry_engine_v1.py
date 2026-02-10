"""
geometry_engine_v1.py
---------------------

HVACgooee — Geometry Engine v1 (clean version)

Purpose
-------
Provides geometry utilities used by the Heat-Loss GUI:
    - polygon manipulation
    - snapping helpers
    - centroid/area helpers
    - rotation/alignment utilities
    - drag/vertex edit helpers

Important:
----------
This module NO LONGER defines its own Space class.
It imports the canonical Space dataclass from:

    HVAC.spaces.space_types

This ensures:
    - no duplicate definitions
    - the GUI, controllers, and engines all share one model
    - per-space temperature fields remain consistent
"""

from __future__ import annotations

import math
from typing import List, Tuple

# Import the unified Space model
from HVAC.spaces.space_types import Space


# ---------------------------------------------------------------------------
# Polygon Utilities
# ---------------------------------------------------------------------------

def polygon_area(polygon: List[Tuple[float, float]]) -> float:
    """Shoelace area — identical logic to Space.floor_area_m2 but standalone."""
    xs = [v[0] for v in polygon]
    ys = [v[1] for v in polygon]
    n = len(polygon)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += xs[i] * ys[j] - xs[j] * ys[i]
    return abs(area) / 2.0


def polygon_centroid(polygon: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Compute centroid of a simple polygon."""
    A = polygon_area(polygon)
    if A == 0:
        return (0.0, 0.0)

    cx = 0.0
    cy = 0.0
    n = len(polygon)

    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    cx /= (6 * A)
    cy /= (6 * A)

    return (cx, cy)


# ---------------------------------------------------------------------------
# Polygon Editing Helpers (GUI calls these)
# ---------------------------------------------------------------------------

def move_polygon(polygon: List[Tuple[float, float]], dx: float, dy: float) -> List[Tuple[float, float]]:
    """Translate polygon by (dx, dy)."""
    return [(x + dx, y + dy) for x, y in polygon]


def rotate_polygon(polygon: List[Tuple[float, float]], angle_deg: float, origin: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Rotate polygon around origin."""
    angle = math.radians(angle_deg)
    ox, oy = origin
    out = []

    for x, y in polygon:
        tx, ty = x - ox, y - oy
        rx = tx * math.cos(angle) - ty * math.sin(angle)
        ry = tx * math.sin(angle) + ty * math.cos(angle)
        out.append((rx + ox, ry + oy))

    return out


def snap_point_to_grid(x: float, y: float, grid: float = 0.1) -> Tuple[float, float]:
    """Snap a point to a grid (default 100 mm)."""
    sx = round(x / grid) * grid
    sy = round(y / grid) * grid
    return (sx, sy)


def align_polygon_edges(polygon: List[Tuple[float, float]], tolerance_deg: float = 5.0) -> List[Tuple[float, float]]:
    """
    Gently align edges close to horizontal or vertical.
    Used during drag or vertex edits.
    """
    aligned = []
    n = len(polygon)

    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]

        dx = x1 - x0
        dy = y1 - y0

        angle = math.degrees(math.atan2(dy, dx))

        # Snap to cardinal directions
        if abs(angle) < tolerance_deg or abs(angle - 180) < tolerance_deg:
            # horizontal
            y1 = y0
        elif abs(angle - 90) < tolerance_deg or abs(angle + 90) < tolerance_deg:
            # vertical
            x1 = x0

        aligned.append((x0, y0))
        polygon[(i + 1) % n] = (x1, y1)

    return aligned
