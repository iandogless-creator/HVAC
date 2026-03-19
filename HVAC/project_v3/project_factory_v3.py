# ======================================================================
# HVACgooee — ProjectFactoryV3
# Phase: I/J — Intent Assembly Only
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from uuid import uuid4
from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1
from HVAC.core.fabric_element import FabricElementV1

class ProjectFactoryV3:

    @staticmethod
    def create_default() -> ProjectState:

        project = ProjectState(
            project_id="NEW-PROJECT",
            name="Untitled Project",
        )

        # Default environment
        project.environment = EnvironmentStateV1(
            external_design_temp_C=-3.0,
            default_internal_temp_C=21.0,
            default_room_height_m=2.4,
            default_ach=0.5,
        )

        # Default construction library
        project.construction_library = {
            "DEFAULT-WALL": 0.28,
            "DEFAULT-WINDOW": 1.40,
            "DEFAULT-ROOF": 0.18,
        }

        return project
