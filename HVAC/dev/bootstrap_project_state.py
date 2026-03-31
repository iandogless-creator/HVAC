# ======================================================================
# HVAC/dev/bootstrap_project_state.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1


# ======================================================================
# DEV Bootstrap (Phase IV — TOPOLOGY-DRIVEN)
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
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
    )

    # --------------------------------------------------
    # Construction library (v1 stable)
    # --------------------------------------------------

    project.construction_library = {
        "DEV-WALL": 0.28,
        "DEV-ROOF": 0.18,
        "DEV-FLOOR": 0.22,
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
    # Geometry (authoritative intent)
    # --------------------------------------------------

    room.geometry = RoomGeometryV1(
        length_m=4.0,
        width_m=3.0,
        height_m=2.4,
        external_wall_length_m=14.0,  # full perimeter
    )

    # --------------------------------------------------
    # Fabric (canonical: EMPTY — derived only)
    # --------------------------------------------------

    room.fabric_elements = []  # 🔒 DO NOT seed FabricElementV1

    # --------------------------------------------------
    # Attach room
    # --------------------------------------------------

    project.rooms[room_id] = room

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    project.mark_heatloss_dirty()

    # --------------------------------------------------
    # DEV assertions (updated for new architecture)
    # --------------------------------------------------

    assert project.environment is not None
    assert project.rooms
    assert project.construction_library

    return project