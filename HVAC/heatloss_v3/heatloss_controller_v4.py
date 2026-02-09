# ======================================================================
# HVACgooee — Heat-Loss Controller (v4)
# Phase: D.2 — Explicit Execution Scope
# Status: ACTIVE
# ======================================================================

from __future__ import annotations

from HVAC_legacy.heatloss_v3.heatloss_runner_v3 import HeatLossRunnerV3
from HVAC_legacy.project.project_state import ProjectState


class HeatLossControllerV4:
    """
    Orchestrates authoritative heat-loss execution.

    Responsibilities:
    • Decide execution scope (room vs project)
    • Invoke runner(s)
    • Commit results into ProjectState

    Does NOT:
    • Perform calculations
    • Infer readiness
    • Interact with GUI
    """

    def __init__(self, *, project_state: ProjectState) -> None:
        self._ps = project_state

    # ------------------------------------------------------------------
    # Room-level execution
    # ------------------------------------------------------------------
    def run_room(self, *, room_id: str) -> None:
        """
        Execute heat-loss for exactly one room.

        Commits:
        • Result for this room only

        Effects:
        • Marks project aggregate as stale
        """

        room = self._ps.rooms.get(room_id)
        if room is None:
            raise KeyError(f"Unknown room_id: {room_id}")

        # Collect inputs (existing logic assumed)
        inputs = HeatLossRunnerV3.build_inputs_for_room(
            room=room,
            project_state=self._ps,
        )

        # Execute physics (pure)
        result = HeatLossRunnerV3.run_room(inputs)

        # Commit authoritative result
        self._ps.heatloss.commit_room_result(
            room_id=room_id,
            result=result,
        )

        # Explicitly invalidate any project aggregate
        self._ps.heatloss.mark_project_stale()

    # ------------------------------------------------------------------
    # Project-level execution
    # ------------------------------------------------------------------
    def run_project(self) -> None:
        """
        Execute heat-loss for the entire project.

        Commits:
        • All room results atomically
        • Optional project aggregate
        """

        room_results = {}

        for room_id, room in self._ps.rooms.items():
            inputs = HeatLossRunnerV3.build_inputs_for_room(
                room=room,
                project_state=self._ps,
            )

            room_results[room_id] = HeatLossRunnerV3.run_room(inputs)

        # Optional: aggregate handled elsewhere or omitted
        project_result = None

        self._ps.heatloss.commit_project_results(
            room_results=room_results,
            project_result=project_result,
        )
