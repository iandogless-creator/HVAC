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
