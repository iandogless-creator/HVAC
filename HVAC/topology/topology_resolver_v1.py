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

    @staticmethod
    def _build_enclosure_segments_for_room(
        room: RoomStateV1,
    ) -> List[BoundarySegmentV1]:
        """
        Build full v1 room enclosure topology.

        Order
        -----
        1. floor
        2. wall-1
        3. wall-2
        4. wall-3
        5. wall-4
        6. ceiling

        Defaults
        --------
        • All surfaces are EXTERNAL
        • No adjacency is inferred
        • Storey does not imply adjacency
        """

        g = room.geometry

        if (
            g is None
            or g.length_m is None
            or g.width_m is None
        ):
            return []

        L = float(g.length_m)
        W = float(g.width_m)
        area_m2 = L * W

        segments: List[BoundarySegmentV1] = []

        # --------------------------------------------------
        # Floor
        # --------------------------------------------------
        segments.append(
            BoundarySegmentV1(
                segment_id=f"{room.room_id}-floor",
                owner_room_id=room.room_id,
                geometry_ref="floor",
                length_m=float(area_m2),
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
            )
        )

        # --------------------------------------------------
        # Walls
        # --------------------------------------------------
        for i, side_len in enumerate([L, W, L, W], start=1):
            segments.append(
                BoundarySegmentV1(
                    segment_id=f"{room.room_id}-seg-{i}",
                    owner_room_id=room.room_id,
                    geometry_ref=f"{room.room_id}-edge-{i}",
                    length_m=float(side_len),
                    boundary_kind="EXTERNAL",
                    adjacent_room_id=None,
                )
            )

        # --------------------------------------------------
        # Ceiling / roof
        # --------------------------------------------------
        segments.append(
            BoundarySegmentV1(
                segment_id=f"{room.room_id}-ceiling",
                owner_room_id=room.room_id,
                geometry_ref="ceiling",
                length_m=float(area_m2),
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
            )
        )

        return segments


    # ------------------------------------------------------------------
    # Ensure one room has topology (live Add Room path)
    # ------------------------------------------------------------------

    @staticmethod
    def ensure_room_topology(
            project: ProjectState,
            room_id: str,
    ) -> None:
        """
        Ensure a single room has basic rectangular topology.

        Intended for live Add Room.

        Rules
        -----
        • Does not rebuild project topology
        • Does not alter other rooms
        • Does not infer adjacency
        • Only creates segments if this room has none
        """

        room = project.rooms.get(room_id)
        if room is None:
            return

        existing = [
            seg
            for seg in project.boundary_segments.values()
            if seg.owner_room_id == room_id
        ]

        if existing:
            return

        segments = TopologyResolverV1._build_enclosure_segments_for_room(room)
        project.set_boundary_segments_for_room(room_id, segments)
