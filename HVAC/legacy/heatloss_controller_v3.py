# ======================================================================
# HVAC/heatloss_v3/heatloss_controller_v3.py
# ======================================================================
"""
HVACgooee — Heat-Loss Controller v3

Purpose
-------
GUI-safe orchestration layer between:
    • GUI inputs
    • HeatLossEngineV3
    • Engine → DTO adapter

Rules
-----
• No GUI imports
• No Qt
• No physics
• Single-room execution (v3)
"""

from __future__ import annotations

from HVAC.heatloss.engines.heatloss_engine_v3 import (
    HeatLossEngineV3,
    RoomHeatLossInput,
)

from HVAC.heatloss.adapters.engine_to_dto import (
    build_heatloss_dto,
)

from HVAC.project_v3.project_models_v3 import SurfaceV3
from HVAC.project_v3.dto.heatloss_readiness import HeatLossReadiness


class HeatLossControllerV3:
    """
    Thin controller coordinating engine execution for GUI.
    """

    def __init__(self) -> None:
        self._engine = HeatLossEngineV3()

    def compute_room(self, room_input: RoomHeatLossInput):
        """
        Execute v3 engine and return GUI DTO.
        """
        engine_result = self._engine.compute_room(room_input)
        return build_heatloss_dto(engine_result)

    def request_run_for_room(self, room_id: str, project_state: ProjectState):
        room_input = RoomHeatLossInput.from_project(
            project_state, room_id
        )
        return self.compute_room(room_input)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_project(self) -> None:
        """
        Execute heat-loss calculation for the current project.

        Phase I-A:
        • Explicit readiness gate
        • Abort-on-not-ready
        • No side effects on failure
        """

        project_state = self._gui_context.project_state
        if project_state is None:
            return  # No project loaded

        # --------------------------------------------------------------
        # Execution readiness gate (authoritative)
        # --------------------------------------------------------------
        readiness: HeatLossReadiness = project_state.evaluate_heatloss_readiness()

        if not readiness.is_ready:
            # Mark project as NOT RUN (explicit)
            project_state.heat_loss_valid = False

            # Optional: store readiness snapshot for GUI observers
            project_state.heatloss_readiness = readiness

            return  # 🚫 HARD ABORT — no calculation

        # --------------------------------------------------------------
        # Ready → proceed with execution
        # --------------------------------------------------------------
        # From this point on, ALL inputs are assumed valid

        # Clear prior results
        project_state.heat_loss_valid = False

        # --- Existing calculation pipeline starts here ---
        #
        # (Leave your existing engine wiring untouched)
        #
        # Example:
        # results = self._engine.run(project_state)
        # project_state.apply_heatloss_results(results)
        #
        # --------------------------------------------------

        # Mark results as valid
        project_state.heat_loss_valid = True