# ======================================================================
# HVAC/topology/topology_validator_v1.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


class TopologyValidatorV1:
    """
    Minimal Phase IV-A validator.

    Scope
    -----
    • validate per-segment correctness
    • do not enforce full symmetric adjacency yet
    • perimeter closure may remain advisory for now
    """

    @staticmethod
    def validate_segment(project_state: Any, seg: BoundarySegmentV1) -> list[str]:
        reasons: list[str] = []

        if seg.length_m <= 0.0:
            reasons.append(f"Boundary segment '{seg.segment_id}' has non-positive length")

        if seg.owner_room_id not in getattr(project_state, "rooms", {}):
            reasons.append(
                f"Boundary segment '{seg.segment_id}' owner room "
                f"'{seg.owner_room_id}' does not exist"
            )

        if seg.boundary_kind == "INTER_ROOM":
            if not seg.adjacent_room_id:
                reasons.append(
                    f"Boundary segment '{seg.segment_id}' is INTER_ROOM "
                    f"but has no adjacent_room_id"
                )
            elif seg.adjacent_room_id not in getattr(project_state, "rooms", {}):
                reasons.append(
                    f"Boundary segment '{seg.segment_id}' adjacent room "
                    f"'{seg.adjacent_room_id}' does not exist"
                )

        elif seg.boundary_kind in ("EXTERNAL", "ADIABATIC"):
            if seg.adjacent_room_id is not None:
                reasons.append(
                    f"Boundary segment '{seg.segment_id}' of kind "
                    f"'{seg.boundary_kind}' must not define adjacent_room_id"
                )

        else:
            reasons.append(
                f"Boundary segment '{seg.segment_id}' has invalid "
                f"boundary_kind '{seg.boundary_kind}'"
            )

        return reasons

    @classmethod
    def validate_room_segments(cls, project_state: Any, room_id: str) -> list[str]:
        reasons: list[str] = []
        for seg in getattr(project_state, "get_boundary_segments_for_room")(room_id):
            reasons.extend(cls.validate_segment(project_state, seg))
        return reasons