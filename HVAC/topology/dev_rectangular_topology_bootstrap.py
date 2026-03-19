# ======================================================================
# HVAC/topology/dev_rectangular_topology_bootstrap.py
# ======================================================================

from __future__ import annotations

from typing import List

from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


# ======================================================================
# DEV — Rectangular Topology Bootstrap
# ======================================================================

def build_rectangular_segments_for_room(project, room) -> List[BoundarySegmentV1]:
    """
    DEV bootstrap

    Generates 4 EXTERNAL boundary segments from rectangular geometry.

    Rules
    -----
    • Pure function (no mutation)
    • Geometry → segments
    • No adjacency yet
    """

    g = room.geometry
    if g is None:
        return []

    L = g.length_m
    W = g.width_m

    if not L or not W:
        return []

    return [
        BoundarySegmentV1(
            segment_id=f"{room.room_id}-wall-1",
            owner_room_id=room.room_id,
            geometry_ref="edge-1",
            length_m=float(L),
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        ),
        BoundarySegmentV1(
            segment_id=f"{room.room_id}-wall-2",
            owner_room_id=room.room_id,
            geometry_ref="edge-2",
            length_m=float(W),
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        ),
        BoundarySegmentV1(
            segment_id=f"{room.room_id}-wall-3",
            owner_room_id=room.room_id,
            geometry_ref="edge-3",
            length_m=float(L),
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        ),
        BoundarySegmentV1(
            segment_id=f"{room.room_id}-wall-4",
            owner_room_id=room.room_id,
            geometry_ref="edge-4",
            length_m=float(W),
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        ),
    ]


# ======================================================================
# Apply bootstrap to whole project
# ======================================================================

def apply_rectangular_topology_bootstrap(project) -> None:
    """
    Mutates ProjectState.boundary_segments (DEV only)
    """

    for room in project.rooms.values():

        segments = build_rectangular_segments_for_room(project, room)

        project.set_boundary_segments_for_room(
            room.room_id,
            segments
        )