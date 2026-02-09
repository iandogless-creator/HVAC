# ======================================================================
# HVACgooee — Room Readiness Adapter
# Phase: D.7 — Presence-Based Readiness
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from typing import List, Optional

from HVAC_legacy.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC_legacy.gui_v3.dto.room_readiness_dto import RoomReadinessDTO


class RoomReadinessAdapter:
    """
    Presence-based readiness check for rooms.

    GUI v3 rule:
    • Adapter must resolve ProjectState explicitly
    • Adapter must NOT assume context.project_state shape
    """

    def __init__(self, *, context: GuiProjectContext) -> None:
        self._context = context

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_readiness(self) -> List[RoomReadinessDTO]:
        ps = self._resolve_project_state()
        if ps is None:
            return []

        rooms = getattr(ps, "rooms", None)
        if not rooms:
            return []

        results: List[RoomReadinessDTO] = []

        for room in rooms.values():
            missing: list[str] = []

            geom = room.geometry
            if geom.length_m <= 0:
                missing.append("length")
            if geom.width_m <= 0:
                missing.append("width")
            if geom.height_m <= 0:
                missing.append("height")

            if not room.constructions:
                missing.append("constructions")

            results.append(
                RoomReadinessDTO(
                    room_id=room.room_id,
                    name=room.name,
                    is_ready=len(missing) == 0,
                    missing_items=missing,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Resolution helper (CANONICAL)
    # ------------------------------------------------------------------
    def _resolve_project_state(self) -> Optional[object]:
        """
        Returns authoritative ProjectState regardless of whether
        context.project_state is ProjectState or ProjectV3.
        """
        ps = getattr(self._context, "project_state", None)
        if ps is None:
            return None

        inner = getattr(ps, "project_state", None)
        return inner if inner is not None else ps
