# ======================================================================
# HVAC/topology/topology_resolver_v1.py
# ======================================================================

from __future__ import annotations

from typing import List

from HVAC.project.project_state import ProjectState
from HVAC.core.room_state import RoomStateV1
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


# ======================================================================
# TopologyResolverV1
# ======================================================================

class TopologyResolverV1:
    """
    DEV rectangular topology generator.

    Status
    ------
    • Allowed only for initial topology creation in new_project()
    • Must never be called on loaded projects
    • Must never be called during geometry edits or refresh
    • Does not preserve adjacency
    """

    # ------------------------------------------------------------------
    # Build full project topology (DEV)
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_project(project: ProjectState) -> None:

        if project.boundary_segments:
            print("🚫 Resolver skipped — topology already exists")
            return

        print("🔥 TopologyResolverV1.resolve_project CALLED 🔥")

        for room in project.rooms.values():
            segments = TopologyResolverV1._build_segments_for_room(room)
            project.set_boundary_segments_for_room(room.room_id, segments)

    # ------------------------------------------------------------------
    # Geometry → segments (DEV rectangular)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_segments_for_room(room: RoomStateV1) -> List[BoundarySegmentV1]:

        g = room.geometry

        if (
            g is None
            or g.length_m is None
            or g.width_m is None
        ):
            return []

        L = float(g.length_m)
        W = float(g.width_m)

        perimeter = 2.0 * (L + W)

        ext_total = (
            float(g.external_wall_length_m)
            if g.external_wall_length_m is not None
            else perimeter
        )

        ext_total = max(0.0, min(ext_total, perimeter))

        lengths = [L, W, L, W]
        total_length = sum(lengths)

        segments: List[BoundarySegmentV1] = []

        remaining_ext = ext_total

        for i, side_len in enumerate(lengths, start=1):

            share = (side_len / total_length) * ext_total if total_length > 0 else 0.0
            share = min(share, remaining_ext)

            boundary_kind = "EXTERNAL" if share > 0.0 else "ADIABATIC"

            segments.append(
                BoundarySegmentV1(
                    segment_id=f"{room.room_id}-seg-{i}",
                    owner_room_id=room.room_id,
                    geometry_ref=f"{room.room_id}-edge-{i}",
                    length_m=float(side_len),
                    boundary_kind=boundary_kind,
                    adjacent_room_id=None,
                )
            )

            remaining_ext -= share

        return segments

    # ------------------------------------------------------------------
    # Read access (canonical)
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_room_boundaries(
        project_state: ProjectState,
        room: RoomStateV1,
    ) -> List[BoundarySegmentV1]:
        """
        Returns boundary segments for a room.
        """

        if project_state is None or room is None:
            return []

        return [
            seg
            for seg in project_state.boundary_segments.values()
            if seg.owner_room_id == room.room_id
        ]