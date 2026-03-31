# ======================================================================
# HVAC/topology/topology_validator_v1.py
# ======================================================================

from __future__ import annotations

from typing import Any, List

from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


class TopologyValidatorV1:
    """
    Minimal Phase IV-A validator.

    Scope
    -----
    • validate per-segment correctness
    • do not enforce full symmetric adjacency yet
    • perimeter closure remains advisory
    """

    # ------------------------------------------------------------------
    # Per-segment validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_segment(
        project_state: Any,
        seg: BoundarySegmentV1,
    ) -> List[str]:

        reasons: List[str] = []

        # --------------------------------------------------
        # Length
        # --------------------------------------------------
        if seg.length_m is None or float(seg.length_m) <= 0.0:
            reasons.append(
                f"Boundary segment '{seg.segment_id}' has non-positive length"
            )

        # --------------------------------------------------
        # Owner room exists
        # --------------------------------------------------
        if seg.owner_room_id not in getattr(project_state, "rooms", {}):
            reasons.append(
                f"Boundary segment '{seg.segment_id}' owner room "
                f"'{seg.owner_room_id}' does not exist"
            )

        # --------------------------------------------------
        # Boundary kind logic
        # --------------------------------------------------
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

            elif seg.adjacent_room_id == seg.owner_room_id:
                reasons.append(
                    f"Boundary segment '{seg.segment_id}' has self-adjacency"
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

    # ------------------------------------------------------------------
    # Per-room validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_room_segments(
        cls,
        project_state: Any,
        room_id: str,
    ) -> List[str]:

        reasons: List[str] = []

        if not hasattr(project_state, "get_boundary_segments_for_room"):
            return ["ProjectState missing boundary segment accessor"]

        for seg in project_state.get_boundary_segments_for_room(room_id):
            reasons.extend(cls.validate_segment(project_state, seg))

        return reasons

    # ------------------------------------------------------------------
    # Full project validation (use this in controller)
    # ------------------------------------------------------------------

    @classmethod
    def validate_project(
        cls,
        project_state: Any,
    ) -> List[str]:

        reasons: List[str] = []

        for seg in getattr(project_state, "boundary_segments", {}).values():
            reasons.extend(cls.validate_segment(project_state, seg))

        return reasons

# ----------------------------------------------------------------------
# Phase IV-C — Room-scoped adjacency validation (NON-BLOCKING)
# ----------------------------------------------------------------------

from dataclasses import dataclass
from typing import Optional


class AdjacencySeverity:
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(slots=True)
class AdjacencyValidationResult:
    surface_id: str
    severity: str
    message: Optional[str] = None


class TopologyValidatorV1(TopologyValidatorV1):  # extend class

    @staticmethod
    def validate_room_adjacency(
        project_state: Any,
        room_id: str,
    ) -> list[AdjacencyValidationResult]:

        results: list[AdjacencyValidationResult] = []

        room = project_state.rooms.get(room_id)
        if room is None:
            return results

        segments = getattr(project_state, "boundary_segments", {}).get(room_id, [])

        for seg in segments:

            sid = getattr(seg, "segment_id", "")

            kind = getattr(seg, "boundary_kind", None)
            adj = getattr(seg, "adjacent_room_id", None)

            # --------------------------------------------------
            # EXTERNAL
            # --------------------------------------------------
            if kind == "EXTERNAL":
                if adj is not None:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.ERROR,
                            message="External boundary cannot have adjacent room",
                        )
                    )
                else:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.OK,
                        )
                    )
                continue

            # --------------------------------------------------
            # ADIABATIC
            # --------------------------------------------------
            if kind == "ADIABATIC":
                if adj is not None:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.ERROR,
                            message="Adiabatic boundary must not have adjacent room",
                        )
                    )
                else:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.OK,
                        )
                    )
                continue

            # --------------------------------------------------
            # INTER_ROOM (core logic)
            # --------------------------------------------------
            if kind == "INTER_ROOM":

                # Missing adjacent
                if not adj:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.WARNING,
                            message="No adjacent room (treated as external)",
                        )
                    )
                    continue

                # Self adjacency
                if adj == room_id:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.ERROR,
                            message="Self adjacency not allowed",
                        )
                    )
                    continue

                adj_room = project_state.rooms.get(adj)

                # Missing room
                if adj_room is None:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.WARNING,
                            message="Adjacent room not found (treated as external)",
                        )
                    )
                    continue

                # Ti check (soft requirement)
                from HVAC.core.value_resolution import resolve_effective_internal_temp_C

                Ti_adj, _ = resolve_effective_internal_temp_C(project_state, adj_room)

                if Ti_adj is None:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.WARNING,
                            message="Adjacent room has no Ti (fallback to external)",
                        )
                    )
                    continue

                # Optional reciprocal check (WARNING only)
                reciprocal_ok = False
                adj_segments = getattr(project_state, "boundary_segments", {}).get(adj, [])

                for other in adj_segments:
                    if getattr(other, "adjacent_room_id", None) == room_id:
                        reciprocal_ok = True
                        break

                if not reciprocal_ok:
                    results.append(
                        AdjacencyValidationResult(
                            surface_id=sid,
                            severity=AdjacencySeverity.WARNING,
                            message="Reciprocal wall missing",
                        )
                    )
                    continue

                # Fully valid
                results.append(
                    AdjacencyValidationResult(
                        surface_id=sid,
                        severity=AdjacencySeverity.OK,
                    )
                )

        return results