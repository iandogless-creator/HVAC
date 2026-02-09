# ======================================================================
# HVACgooee — Project Heat-Loss Readiness Adapter
# Phase: D.8 — Project-Level Readiness
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from typing import Optional

from HVAC_legacy.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC_legacy.gui_v3.dto.project_heatloss_readiness_dto import (
    ProjectHeatLossReadinessDTO,
)
from HVAC_legacy.gui_v3.adapters.room_readiness_adapter import RoomReadinessAdapter


class ProjectHeatLossReadinessAdapter:
    """
    Project-level readiness for heat-loss execution.

    GUI v3 rule:
    • Adapter must resolve ProjectState explicitly
    • Adapter must not assume ProjectV3 structure
    """

    def __init__(self, *, context: GuiProjectContext) -> None:
        self._context = context
        self._room_readiness = RoomReadinessAdapter(context=context)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_readiness(self) -> ProjectHeatLossReadinessDTO:
        blocking: list[str] = []

        ps = self._resolve_project_state()
        if ps is None:
            return ProjectHeatLossReadinessDTO(
                is_ready=False,
                blocking_reasons=["no project loaded"],
            )

        # -------------------------------
        # Room readiness
        # -------------------------------
        room_results = self._room_readiness.build_readiness()
        if not room_results:
            blocking.append("no rooms defined")

        for r in room_results:
            if not r.is_ready:
                blocking.append(f"room not ready: {r.name}")

        # -------------------------------
        # Environment presence
        # -------------------------------
        environment = getattr(ps, "environment", None)
        if environment is None:
            blocking.append("environment not defined")

        return ProjectHeatLossReadinessDTO(
            is_ready=len(blocking) == 0,
            blocking_reasons=blocking,
        )

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
