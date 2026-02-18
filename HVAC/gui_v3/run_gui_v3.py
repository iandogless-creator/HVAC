# ======================================================================
# HVACgooee — GUI v3 Runner (DEV BOOTSTRAP)
# Purpose: Prove HLPE Area edit spine (NO fabric model)
# ======================================================================

import sys
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.main_window import MainWindowV3

from HVAC.project.project_state import ProjectState
from HVAC.project.room_state_v1 import (
    RoomStateV1,
    RoomGeometryV1,
)
from HVAC.constructions.construction_preset import SurfaceClass


# ----------------------------------------------------------------------
# DEV bootstrap project
# ----------------------------------------------------------------------
def make_dev_bootstrap_project_state() -> ProjectState:
    """
    DEV ONLY — GUI bootstrap project.

    Purpose
    -------
    • GUI opens with visible worksheet rows
    • Area values exist and are editable
    • No fabric / construction authority yet
    """

    geometry = RoomGeometryV1(
        length_m=5.0,
        width_m=4.0,
        height_m=2.4,
        surface_areas_m2={
            SurfaceClass.EXTERNAL_WALL: 30.0,
            SurfaceClass.FLOOR: 20.0,
            SurfaceClass.CEILING: 20.0,
        },
    )

    room = RoomStateV1(
        room_id="room-001",
        name="Living Room",
        geometry=geometry,
        constructions={},  # intentionally empty (v1)
    )

    return ProjectState(
        project_id="dev-bootstrap",
        name="DEV Bootstrap Project",
        rooms={"room-001": room},
    )


# ----------------------------------------------------------------------
# Main entry
# ----------------------------------------------------------------------
def main() -> None:
    app = QApplication(sys.argv)

    project_state = make_dev_bootstrap_project_state()

    context = GuiProjectContext(
        project_state=project_state
    )

    # Deterministic selection
    context.set_current_room("room-001")

    window = MainWindowV3(context)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
