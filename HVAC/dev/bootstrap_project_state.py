# ======================================================================
# HVAC/dev/bootstrap_project_state.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1
from HVAC.core.fabric_element import FabricElementV1


# ======================================================================
# DEV Bootstrap
# ======================================================================

def make_dev_bootstrap_project_state() -> ProjectState:

    project = ProjectState(
        project_id="DEV-PROJ-001",
        name="HVACgooee DEV Project",
    )

    # --------------------------------------------------
    # Environment
    # --------------------------------------------------

    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
    )

    # --------------------------------------------------
    # Construction library (v1)
    # construction_id -> U-value
    # --------------------------------------------------

    project.construction_library = {

        "EXT-WALL": 0.28,
        "WINDOW": 1.40,
        "DOOR": 2.00,
        "ROOF": 0.18,
        "FLOOR": 0.22,

    }

    # --------------------------------------------------
    # Room
    # --------------------------------------------------

    room_id = "room-001"

    room = RoomStateV1(
        room_id=room_id,
        name="Kitchen (DEV)",
    )

    # --------------------------------------------------
    # Geometry intent
    # --------------------------------------------------

    room.geometry = RoomGeometryV1(
        length_m=3.0,
        width_m=4.0,
        height_override_m=None,
        external_wall_length_m=4.0,
        floor_area_m2=12.0,
    )

    # --------------------------------------------------
    # Fabric elements (modelling intent)
    # --------------------------------------------------

    room.fabric_elements = [

        FabricElementV1(
            element_class="external_wall",
            area_m2=8.4,
            construction_id="EXT-WALL",
        ),

        FabricElementV1(
            element_class="window",
            area_m2=2.4,
            construction_id="WINDOW",
        ),

        FabricElementV1(
            element_class="door",
            area_m2=1.8,
            construction_id="DOOR",
        ),

        FabricElementV1(
            element_class="roof",
            area_m2=12.0,
            construction_id="ROOF",
        ),

        FabricElementV1(
            element_class="floor",
            area_m2=12.0,
            construction_id="FLOOR",
        ),

    ]

    # --------------------------------------------------
    # Attach room
    # --------------------------------------------------

    project.rooms[room_id] = room

    # --------------------------------------------------
    # DEV assertions
    # --------------------------------------------------

    assert project.environment is not None
    assert project.rooms
    assert project.construction_library
    assert room.fabric_elements

    return project