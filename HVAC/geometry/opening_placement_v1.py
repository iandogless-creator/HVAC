"""
opening_placement_v1.py
-----------------------

HVACgooee — Opening Placement Helpers v1 (Pure Model + Math)

Purpose
-------
Defines how windows and doors are placed on geometry WITHOUT:

    • splitting edges
    • mutating polygons
    • creating wall objects
    • implying construction thickness
    • implying adjacency

Openings are ENGINEERING ATTACHMENTS to polygon EDGES.

This module depends only on:
    • geometry footprint (List[(x, y)])
    • edge_bearing_utils_v1

Design Rules (v1.5)
------------------
✔ Openings reference edges parametrically
✔ Placement is distance-based, not vertex-based
✔ Orientation is handled elsewhere (edge bearings)
✔ This module is UI-agnostic and CAD-free

SAFE FOR CORE.
"""

# ================================================================
# BEGIN IMPORTS
# ================================================================
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, Sequence, Tuple

from HVAC.geometry.edge_bearing_utils_v1 import (
    EdgeGeometry,
    ProjectionResult,
    edge_geometry,
    global_edge_bearing_deg,
    nearest_edge_to_point,
    opening_span_on_edge,
)

# END IMPORTS
# ================================================================

Point = Tuple[float, float]


# ================================================================
# BEGIN DATA MODELS
# ================================================================
OpeningType = Literal["window", "door"]


@dataclass(frozen=True)
class OpeningPlacement:
    """
    Canonical placement definition for an opening.

    This does NOT describe geometry.
    It describes PARAMETRIC POSITION on an EDGE.
    """

    edge_index: int              # Which polygon edge
    offset_m: float              # Distance from edge start (A)
    width_m: float               # Opening width along edge
    opening_type: OpeningType = "window"

    sill_height_m: Optional[float] = None
    head_height_m: Optional[float] = None

    notes: Optional[str] = None


@dataclass(frozen=True)
class OpeningResolvedGeometry:
    """
    Resolved geometry for an opening — derived, not stored.

    Used for:
        • preview drawing
        • heat-loss attribution
        • fenestration engines
    """

    placement: OpeningPlacement
    start_point: Point
    end_point: Point
    edge_bearing_deg: float
    edge_length_m: float


# END DATA MODELS
# ================================================================


# ================================================================
# BEGIN CREATION HELPERS
# ================================================================
def create_opening_from_click(
    footprint: Sequence[Point],
    click_point: Point,
    width_m: float,
    opening_type: OpeningType = "window",
    max_snap_distance_m: float = 0.5,
) -> Optional[OpeningPlacement]:
    """
    Create an OpeningPlacement by clicking near a polygon edge.

    UI supplies:
        • click_point (world coords)
        • width_m

    Returns:
        OpeningPlacement or None if no edge is close enough.

    NOTE:
        This does NOT snap geometry.
        It merely *measures* distance to edges.
    """

    proj: Optional[ProjectionResult] = nearest_edge_to_point(
        footprint=footprint,
        p=click_point,
        max_distance_m=max_snap_distance_m,
    )

    if proj is None:
        return None

    return OpeningPlacement(
        edge_index=proj.edge_index,
        offset_m=proj.distance_along_edge_m,
        width_m=float(width_m),
        opening_type=opening_type,
    )


# END CREATION HELPERS
# ================================================================


# ================================================================
# BEGIN RESOLUTION HELPERS
# ================================================================
def resolve_opening_geometry(
    footprint: Sequence[Point],
    opening: OpeningPlacement,
    space_orientation_deg: float,
) -> OpeningResolvedGeometry:
    """
    Resolve an OpeningPlacement into concrete geometry and bearing.

    This function:
        • computes start/end points on the edge
        • computes the GLOBAL edge bearing
        • does NOT modify geometry
    """

    eg: EdgeGeometry = edge_geometry(footprint, opening.edge_index)

    start_pt, end_pt = opening_span_on_edge(
        footprint=footprint,
        edge_index=opening.edge_index,
        offset_m=opening.offset_m,
        width_m=opening.width_m,
    )

    bearing = global_edge_bearing_deg(
        footprint=footprint,
        edge_index=opening.edge_index,
        space_orientation_deg=space_orientation_deg,
    )

    return OpeningResolvedGeometry(
        placement=opening,
        start_point=start_pt,
        end_point=end_pt,
        edge_bearing_deg=bearing,
        edge_length_m=eg.length_m,
    )


def resolve_all_openings(
    footprint: Sequence[Point],
    openings: Sequence[OpeningPlacement],
    space_orientation_deg: float,
) -> List[OpeningResolvedGeometry]:
    """
    Resolve multiple openings for confirmation, preview, or calculation.
    """
    return [
        resolve_opening_geometry(
            footprint=footprint,
            opening=o,
            space_orientation_deg=space_orientation_deg,
        )
        for o in openings
    ]


# END RESOLUTION HELPERS
# ================================================================


# ================================================================
# BEGIN VALIDATION HELPERS
# ================================================================
def opening_fits_on_edge(
    footprint: Sequence[Point],
    opening: OpeningPlacement,
    allow_partial_clip: bool = False,
) -> bool:
    """
    Validate whether an opening fits entirely on its referenced edge.

    If allow_partial_clip is True:
        • returns True even if width exceeds remaining edge length

    This does NOT auto-adjust.
    """

    eg = edge_geometry(footprint, opening.edge_index)
    if eg.length_m <= 0:
        return False

    if opening.offset_m < 0:
        return False

    if allow_partial_clip:
        return opening.offset_m < eg.length_m

    return (opening.offset_m + opening.width_m) <= eg.length_m


# END VALIDATION HELPERS
# ================================================================


# ================================================================
# BEGIN SMALL CONVENIENCE
# ================================================================
def opening_midpoint(resolved: OpeningResolvedGeometry) -> Point:
    """Return midpoint of an opening span (useful for labels)."""
    x0, y0 = resolved.start_point
    x1, y1 = resolved.end_point
    return ((x0 + x1) * 0.5, (y0 + y1) * 0.5)


# END CONVENIENCE
# ================================================================
