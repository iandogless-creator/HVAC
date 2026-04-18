# ======================================================================
# HVAC/topology/topology_adjacency_service_v1.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


class TopologyAdjacencyServiceV1:
    """
    Canonical Phase IV-B adjacency mutator.

    Authority
    ---------
    • All adjacency writes must route through this service
    • Enforces symmetry
    • Prevents duplicate / conflicting assignment
    • Supports clear/remove operations
    • Does NOT perform UI work
    • Does NOT infer geometry
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @staticmethod
    def assign_pair(
        project,
        segment_a_id: str,
        segment_b_id: str,
    ) -> None:
        """
        Assign two segments as an inter-room pair.

        Rules
        -----
        • both segments must exist
        • cannot pair segment to itself
        • segments must belong to different rooms
        • each segment must be free or already paired to the same opposite
        • relationship is always written symmetrically
        """
        seg_a = TopologyAdjacencyServiceV1._get_segment(project, segment_a_id)
        seg_b = TopologyAdjacencyServiceV1._get_segment(project, segment_b_id)

        if seg_a.segment_id == seg_b.segment_id:
            raise ValueError("Cannot pair a segment to itself.")

        if seg_a.owner_room_id == seg_b.owner_room_id:
            raise ValueError("Cannot pair two segments from the same room.")

        TopologyAdjacencyServiceV1._assert_segment_assignable(
            project=project,
            source=seg_a,
            target=seg_b,
        )
        TopologyAdjacencyServiceV1._assert_segment_assignable(
            project=project,
            source=seg_b,
            target=seg_a,
        )

        seg_a.boundary_kind = "INTER_ROOM"
        seg_a.adjacent_room_id = seg_b.owner_room_id

        seg_b.boundary_kind = "INTER_ROOM"
        seg_b.adjacent_room_id = seg_a.owner_room_id

    @staticmethod
    def clear_segment(project, segment_id: str) -> None:
        """
        Clear a segment and its symmetric counterpart if present.

        Phase IV-B rule:
        • clearing one side clears the whole pair
        """
        seg = TopologyAdjacencyServiceV1._get_segment(project, segment_id)

        if seg.boundary_kind != "INTER_ROOM" or not seg.adjacent_room_id:
            seg.boundary_kind = "EXTERNAL"
            seg.adjacent_room_id = None
            return

        counterpart = TopologyAdjacencyServiceV1._find_counterpart(project, seg)

        seg.boundary_kind = "EXTERNAL"
        seg.adjacent_room_id = None

        if counterpart is not None:
            counterpart.boundary_kind = "EXTERNAL"
            counterpart.adjacent_room_id = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_segment(project, segment_id: str) -> BoundarySegmentV1:
        seg = project.boundary_segments.get(segment_id)
        if seg is None:
            raise ValueError(f"Unknown segment_id: {segment_id}")
        return seg

    @staticmethod
    def _assert_segment_assignable(project, source, target) -> None:
        if source.boundary_kind == "INTER_ROOM":
            counterpart = TopologyAdjacencyServiceV1._find_counterpart(project, source)

            already_paired_to_target = (
                counterpart is not None
                and counterpart.segment_id == target.segment_id
            )

            if not already_paired_to_target:
                raise ValueError(
                    f"Segment already assigned: {source.segment_id}"
                )

    @staticmethod
    def _find_counterpart(project, segment) -> Optional[BoundarySegmentV1]:
        if segment.boundary_kind != "INTER_ROOM" or not segment.adjacent_room_id:
            return None

        for other in project.boundary_segments.values():
            if other.segment_id == segment.segment_id:
                continue
            if other.owner_room_id != segment.adjacent_room_id:
                continue
            if other.boundary_kind != "INTER_ROOM":
                continue
            if other.adjacent_room_id != segment.owner_room_id:
                continue
            return other

        return None