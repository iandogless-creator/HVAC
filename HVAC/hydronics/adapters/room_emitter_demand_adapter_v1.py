# ======================================================================
# HVAC/hydronics/adapters/room_emitter_demand_adapter_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from HVAC.project.project_state import ProjectState


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
    """

    room_id: str
    room_name: str

    design_heat_load_W: Optional[float]

    emitter_id: Optional[str]
    emitter_type: Optional[str]
    emitter_output_W: Optional[float]

    status: str


# ======================================================================
# RoomEmitterDemandAdapterV1
# ======================================================================

class RoomEmitterDemandAdapterV1:
    """
    Hydronics Phase H-A.

    Builds room-level emitter demand rows from ProjectState.

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
            room_name = (
                getattr(room, "name", None)
                or getattr(room, "label", None)
                or room_id
            )

            design_heat_load_W = self._resolve_room_heat_load_W(
                project,
                room_id,
            )

            emitter = self._find_emitter_for_room(project, room_id)

            emitter_id = getattr(emitter, "emitter_id", None) if emitter else None
            emitter_type = getattr(emitter, "emitter_type", None) if emitter else None
            emitter_output_W = getattr(emitter, "design_output_W", None) if emitter else None

            status = self._resolve_status(
                design_heat_load_W=design_heat_load_W,
                emitter_output_W=emitter_output_W,
                has_emitter=emitter is not None,
            )

            rows.append(
                RoomEmitterDemandRowV1(
                    room_id=room_id,
                    room_name=room_name,
                    design_heat_load_W=design_heat_load_W,
                    emitter_id=emitter_id,
                    emitter_type=emitter_type,
                    emitter_output_W=emitter_output_W,
                    status=status,
                )
            )

        return rows

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    def _resolve_room_heat_load_W(
        self,
        project: ProjectState,
        room_id: str,
    ) -> Optional[float]:
        """
        Read committed heat-loss result if available.

        Hydronics does not calculate heat-loss.
        """
        if not getattr(project, "heatloss_valid", False):
            return None

        if not getattr(project, "heatloss_results", None):
            return None

        getter = getattr(project, "get_room_heatloss_totals", None)
        if getter is None:
            return None

        totals = getter(room_id)

        if not totals:
            return None

        # Tolerant because historical result DTO shapes have varied.
        for key in ("Qt_W", "qt_W", "total_W", "total_heat_loss_W", "Qt"):
            value = self._read_value(totals, key)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None

        return None

    def _find_emitter_for_room(
        self,
        project: ProjectState,
        room_id: str,
    ) -> Any | None:
        emitters = getattr(project, "emitters", {}) or {}

        for emitter in emitters.values():
            if getattr(emitter, "room_id", None) == room_id:
                return emitter

        return None

    def _resolve_status(
        self,
        *,
        design_heat_load_W: Optional[float],
        emitter_output_W: Optional[float],
        has_emitter: bool,
    ) -> str:
        if design_heat_load_W is None:
            return "NO_HEAT_LOSS_RESULT"

        if not has_emitter:
            return "NEEDS_EMITTER"

        if emitter_output_W is None:
            return "NEEDS_EMITTER_OUTPUT"

        try:
            if float(emitter_output_W) < float(design_heat_load_W):
                return "EMITTER_UNDERSIZED"
        except (TypeError, ValueError):
            return "NEEDS_EMITTER_OUTPUT"

        return "EMITTER_OK"

    def _read_value(self, obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(key)

        return getattr(obj, key, None)