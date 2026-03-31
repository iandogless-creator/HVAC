# ======================================================================
# HVACgooee — GUI v3 Runner (DEV Bootstrap)
#
# Purpose
# -------
# Launch GUI with a minimal valid ProjectState for development.
#
# Timestamp: Thursday 6 March 2026
# ======================================================================

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.main_window import MainWindowV3

from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1
from HVAC.topology.topology_resolver_v1 import TopologyResolverV1

# ----------------------------------------------------------------------
# DEV Bootstrap Project
# ----------------------------------------------------------------------

def make_dev_bootstrap_project_state() -> ProjectState:

    project = ProjectState(
        project_id="DEV-PROJ-001",
        name="DEV Bootstrap Project",
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
    # Construction library (DEV)
    # --------------------------------------------------

    project.construction_library = {
        "DEV-WALL": 0.28,
        "DEV-WINDOW": 1.40,
        "DEV-ROOF": 0.18,
    }

    # --------------------------------------------------
    # Room
    # --------------------------------------------------

    room_id = "room-001"

    geometry = RoomGeometryV1(
        length_m=4.0,
        width_m=3.0,
        height_m=2.4,
        external_wall_length_m=14.0,
    )

    room = RoomStateV1(
        room_id=room_id,
        name="Kitchen (DEV)",
        geometry=geometry,
    )

    # --------------------------------------------------
    # Fabric (canonical: EMPTY — will be built from topology)
    # --------------------------------------------------

    room.fabric_elements = []  # 🔒 DO NOT seed legacy FabricElementV1

    project.rooms[room_id] = room

    # --------------------------------------------------
    # 🔑 Build topology immediately (CRITICAL)
    # --------------------------------------------------
    TopologyResolverV1.resolve_project(project)
    print("[BOOT] Segments:", project.boundary_segments)
    # --------------------------------------------------
    # Fabric remains derived (DO NOT persist here)
    # --------------------------------------------------
    room.fabric_elements = []

    project.mark_heatloss_dirty()

    return project


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> None:

    app = QApplication(sys.argv)

    # --------------------------------------------------
    # Create bootstrap project
    # --------------------------------------------------

    project_state = make_dev_bootstrap_project_state()

    context = GuiProjectContext(project_state=project_state)

    win = MainWindowV3(context=context)
    win.show()

    # --------------------------------------------------
    # DEV convenience: auto-select first room
    # --------------------------------------------------

    def _select_first_room() -> None:

        ps = context.project_state

        if not ps.rooms:
            return

        first_room_id = next(iter(ps.rooms))

        if hasattr(context, "set_current_room"):
            context.set_current_room(first_room_id)

        elif hasattr(context, "set_current_room_id"):
            context.set_current_room_id(first_room_id)

        else:
            context.current_room_id = first_room_id

            if hasattr(context, "current_room_changed"):
                context.current_room_changed.emit(first_room_id)

    QTimer.singleShot(0, _select_first_room)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()