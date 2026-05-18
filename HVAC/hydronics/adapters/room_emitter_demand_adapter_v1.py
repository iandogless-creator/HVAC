# ======================================================================
# HVAC/hydronics/adapters/room_emitter_demand_adapter_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from HVAC.project.project_state import ProjectState
from HVAC.core.room_identity import room_short_label

# ======================================================================
# RoomEmitterDemandRowV1
# ======================================================================

@dataclass(frozen=True)
class RoomEmitterDemandRowV1:
    """
    Read-only hydronics observer row.

    Authority
    ---------
    • Derived from ProjectState
    • Does not mutate ProjectState
    • Does not calculate heat loss
    • Does not size pipes

    H-D rule
    --------
    A room may have zero, one, or many emitters.
    This row represents the aggregate room-level emitter state.
    """

    room_id: str
    room_name: str

    design_heat_load_W: Optional[float]

    emitter_count: int
    emitter_summary: str
    emitter_output_W: Optional[float]

    status: str


# ======================================================================
# RoomEmitterDemandAdapterV1
# ======================================================================

class RoomEmitterDemandAdapterV1:
    """
    Hydronics Phase H-D.

    Builds room-level aggregate emitter demand rows from ProjectState.

    Explicitly forbidden
    --------------------
    • no heat-loss calculation
    • no pipe sizing
    • no pump sizing
    • no pressure-loss calculation
    • no ProjectState mutation
    """

    def build_rows(self, project: ProjectState) -> list[RoomEmitterDemandRowV1]:
        rows: list[RoomEmitterDemandRowV1] = []

        rooms = getattr(project, "rooms", {}) or {}

        for room_id, room in rooms.items():
            room_name = room_short_label(room_id, room)

            design_heat_load_W = self._resolve_room_heat_load_W(
                project,
                room_id,
            )

            emitters = self._emitters_for_room(project, room_id)

            emitter_count = len(emitters)
            emitter_summary = self._summarise_emitters(emitters)
            emitter_output_W = self._sum_emitter_output_W(emitters)

            status = self._resolve_status(
                design_heat_load_W=design_heat_load_W,
                emitter_output_W=emitter_output_W,
                emitter_count=emitter_count,
            )

            rows.append(
                RoomEmitterDemandRowV1(
                    room_id=room_id,
                    room_name=room_name,
                    design_heat_load_W=design_heat_load_W,
                    emitter_count=emitter_count,
                    emitter_summary=emitter_summary,
                    emitter_output_W=emitter_output_W,
                    status=status,
                )
            )

        return rows

    # ------------------------------------------------------------------
    # Heat-loss demand resolution
    # ------------------------------------------------------------------

    def _resolve_room_heat_load_W(
            self,
            project: ProjectState,
            room_id: str,
    ) -> Optional[float]:
        """
        Read committed heat-loss total if available.

        Hydronics consumes q_total_W only.
        It does not calculate heat loss.

        Supports both:
        • dict shape: {"q_fabric_W": ..., "q_ventilation_W": ..., "q_total_W": ...}
        • legacy tuple/list shape: (q_fabric_W, q_ventilation_W, q_total_W)
        """
        if not getattr(project, "heatloss_valid", False):
            return None

        getter = getattr(project, "get_room_heatloss_totals", None)

        if callable(getter):
            totals = getter(room_id)

            if isinstance(totals, dict):
                qt = totals.get("q_total_W")
                if qt is not None:
                    try:
                        return float(qt)
                    except (TypeError, ValueError):
                        return None

            elif totals:
                try:
                    _qf, _qv, qt = totals
                except (TypeError, ValueError):
                    qt = None

                if qt is not None:
                    try:
                        return float(qt)
                    except (TypeError, ValueError):
                        return None

        # --------------------------------------------------
        # Fallback: persisted/canonical heat-loss container
        # --------------------------------------------------
        heatloss_results = getattr(project, "heatloss_results", None) or {}

        if isinstance(heatloss_results, dict):
            room_totals = heatloss_results.get("room_totals", {}) or {}
            room_total = room_totals.get(room_id, {}) or {}

            if isinstance(room_total, dict):
                qt = room_total.get("q_total_W")

                if qt is not None:
                    try:
                        return float(qt)
                    except (TypeError, ValueError):
                        return None

        return None

    # ------------------------------------------------------------------
    # Emitter aggregation
    # ------------------------------------------------------------------

    def _emitters_for_room(
        self,
        project: ProjectState,
        room_id: str,
    ) -> list[Any]:
        emitters = getattr(project, "emitters", {}) or {}

        return [
            emitter
            for emitter in emitters.values()
            if getattr(emitter, "room_id", None) == room_id
        ]

    def _summarise_emitters(self, emitters: list[Any]) -> str:
        if not emitters:
            return "—"

        counts: dict[str, int] = {}

        for emitter in emitters:
            emitter_type = (
                getattr(emitter, "emitter_type", None)
                or "emitter"
            )
            counts[emitter_type] = counts.get(emitter_type, 0) + 1

        parts = [
            f"{count} × {emitter_type}"
            if count > 1
            else emitter_type
            for emitter_type, count in sorted(counts.items())
        ]

        return ", ".join(parts)

    def _sum_emitter_output_W(self, emitters: list[Any]) -> Optional[float]:
        if not emitters:
            return None

        total = 0.0
        has_output = False

        for emitter in emitters:
            value = getattr(emitter, "design_output_W", None)

            if value is None:
                continue

            try:
                total += float(value)
                has_output = True
            except (TypeError, ValueError):
                continue

        if not has_output:
            return None

        return total

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def _resolve_status(
        self,
        *,
        design_heat_load_W: Optional[float],
        emitter_output_W: Optional[float],
        emitter_count: int,
    ) -> str:
        if design_heat_load_W is None:
            return "NO_HEAT_LOSS_RESULT"

        if emitter_count <= 0:
            return "NEEDS_EMITTER"

        if emitter_output_W is None:
            return "NEEDS_EMITTER_OUTPUT"

        try:
            if float(emitter_output_W) < float(design_heat_load_W):
                return "EMITTER_UNDERSIZED"
        except (TypeError, ValueError):
            return "NEEDS_EMITTER_OUTPUT"

        return "EMITTER_OK"