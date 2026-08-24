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
from HVAC.core.construction_v1 import ConstructionV1

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
            design_flow_temp_c=75.0,
            design_return_temp_c=65.0,
        )

        # Canonical construction library used by topology, fabric,
        # Wall Wizard and U-Values projection throughout GUI v3.
        project.constructions = {
            "DEV-EXT-WALL": ConstructionV1(
                construction_id="DEV-EXT-WALL",
                name="External Wall",
                u_value_W_m2K=0.26,
            ),
            "DEV-INT-WALL": ConstructionV1(
                construction_id="DEV-INT-WALL",
                name="Internal Wall",
                u_value_W_m2K=1.50,
            ),
            "DEV-FLOOR": ConstructionV1(
                construction_id="DEV-FLOOR",
                name="Floor",
                u_value_W_m2K=0.18,
            ),
            "DEV-ROOF": ConstructionV1(
                construction_id="DEV-ROOF",
                name="Roof / Ceiling",
                u_value_W_m2K=0.16,
            ),
            "DEV-WINDOW": ConstructionV1(
                construction_id="DEV-WINDOW",
                name="Window / Door",
                u_value_W_m2K=1.60,
            ),
        }

        return project
