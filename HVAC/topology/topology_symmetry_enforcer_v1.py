# ======================================================================
# HVAC/topology/topology_symmetry_enforcer_v1.py
# ======================================================================

from __future__ import annotations

from typing import Dict, Optional

from HVAC.project.project_state import ProjectState
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


# ======================================================================
# TopologySymmetryEnforcerV1
# ======================================================================

class TopologySymmetryEnforcerV1:
    """
    Enforces bidirectional adjacency (A ↔ B).

    Rules
    -----
    • INTER_ROOM segments must have a reverse counterpart
    • Reverse segment must point back to owner
    • Missing reverse segments are created (DEV-safe)
    • No geometry inference
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def enforce(project: ProjectState) -> None:

        segments: Dict[str, BoundarySegmentV1] = project.boundary_segments

        if not segments:
            return

        # snapshot to avoid mutation issues
        existing = list(segments.values())

        for seg in existing:

            if seg.boundary_kind != "INTER_ROOM":
                continue

            if not seg.adjacent_room_id:
                continue

            reverse = TopologySymmetryEnforcerV1._find_reverse_segment(
                project,
                owner_room_id=seg.adjacent_room_id,
                adjacent_room_id=seg.owner_room_id,
            )

            if reverse is None:
                TopologySymmetryEnforcerV1._create_reverse_segment(
                    project,
                    seg,
                )
            else:
                TopologySymmetryEnforcerV1._enforce_consistency(
                    seg,
                    reverse,
                )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_reverse_segment(
        project: ProjectState,
        *,
        owner_room_id: str,
        adjacent_room_id: str,
    ) -> Optional[BoundarySegmentV1]:

        for seg in project.boundary_segments.values():
            if (
                seg.owner_room_id == owner_room_id
                and seg.boundary_kind == "INTER_ROOM"
                and seg.adjacent_room_id == adjacent_room_id
            ):
                return seg

        return None

    @staticmethod
    def _create_reverse_segment(
        project: ProjectState,
        source: BoundarySegmentV1,
    ) -> None:

        reverse = BoundarySegmentV1(
            segment_id=f"{source.adjacent_room_id}-rev-{source.segment_id}",
            owner_room_id=source.adjacent_room_id,
            geometry_ref=None,
            length_m=source.length_m,
            boundary_kind="INTER_ROOM",
            adjacent_room_id=source.owner_room_id,
        )

        project.boundary_segments[reverse.segment_id] = reverse

    @staticmethod
    def _enforce_consistency(
        source: BoundarySegmentV1,
        reverse: BoundarySegmentV1,
    ) -> None:

        if reverse.adjacent_room_id != source.owner_room_id:
            reverse.adjacent_room_id = source.owner_room_id