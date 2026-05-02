# ======================================================================
# HVAC/dev/bootstrap_project_state.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1
from HVAC.core.construction_v1 import ConstructionV1
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


# ======================================================================
# DEV Bootstrap (Phase V — Clean + Deterministic)
# ======================================================================

def make_dev_bootstrap_project_state() -> ProjectState:

    # --------------------------------------------------
    # Project
    # --------------------------------------------------

    project = ProjectState(
        project_id="DEV-PROJ-001",
        name="HVACgooee DEV Project",
    )
    project.project_dir = None  # or ps.project_dir depending on name
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
    # Constructions (canonical authority)
    # --------------------------------------------------

    from HVAC.dev.dev_constructions import ensure_dev_constructions
    project.constructions = {}
    ensure_dev_constructions(project)
    # --------------------------------------------------
    # Room
    # --------------------------------------------------

    room_id = "room-001"

    room = RoomStateV1(
        room_id=room_id,
        name="Kitchen (DEV)",
    )

    room.geometry = RoomGeometryV1(
        length_m=4.0,
        width_m=3.0,
        height_m=2.4,
        external_wall_length_m=14.0,
    )

    project.rooms[room_id] = room

    # --------------------------------------------------
    # Topology (minimal: floor + ceiling)
    # --------------------------------------------------

    project.boundary_segments = {
        "room-001-floor": BoundarySegmentV1(
            segment_id="room-001-floor",
            owner_room_id=room_id,
            geometry_ref="floor",      # 🔑 semantic (bridge expects this)
            length_m=12.0,
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        ),
        "room-001-ceil": BoundarySegmentV1(
            segment_id="room-001-ceil",
            owner_room_id=room_id,
            geometry_ref="ceiling",   # 🔑 semantic
            length_m=12.0,
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        ),
    }

    # --------------------------------------------------
    # Surface → Construction mapping
    # --------------------------------------------------

    project.surface_construction_map = {
        "room-001-floor": "DEV-FLOOR",
        "room-001-ceil": "DEV-ROOF",
    }

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    project.mark_heatloss_dirty()

    # --------------------------------------------------
    # DEV assertions
    # --------------------------------------------------

    assert project.environment is not None
    assert project.rooms
    assert project.constructions
    assert project.boundary_segments

    return project