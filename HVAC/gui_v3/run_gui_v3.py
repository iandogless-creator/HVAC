# ======================================================================
# HVACgooee — GUI v3 Runner (DEV Bootstrap)
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
from HVAC.core.construction_v1 import ConstructionV1

# run_gui_v3.py

from HVAC.dev.bootstrap_registry import BOOTSTRAPS

DEFAULT_BOOTSTRAP = "vertical_stack"  # ← change here easily

def build_project(mode: str):
    fn = BOOTSTRAPS.get(mode)
    if not fn:
        raise ValueError(f"Unknown bootstrap mode: {mode}")
    return fn()
# ----------------------------------------------------------------------
# DEV Bootstrap Project
# ----------------------------------------------------------------------

def make_dev_bootstrap_project_state() -> ProjectState:
    ps = build_project(DEFAULT_BOOTSTRAP)
    _ensure_default_constructions(ps)
    project = ProjectState(
        project_id="DEV-PROJ-001",
        name="DEV Bootstrap Project",
    )

    # Environment
    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
    )

    # Constructions
    project.constructions = {
        "DEV-EXT-WALL": ConstructionV1("DEV-EXT-WALL", "External Wall", 0.28),
        "DEV-INT-WALL": ConstructionV1("DEV-INT-WALL", "Internal Wall", 1.50),
        "DEV-ROOF": ConstructionV1("DEV-ROOF", "Roof", 0.18),
        "DEV-FLOOR": ConstructionV1("DEV-FLOOR", "Floor", 0.22),
        "DEV-WINDOW": ConstructionV1("DEV-WINDOW", "Window", 1.40),
    }

    # Room
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

    project.rooms[room_id] = room

    # Topology
    TopologyResolverV1.resolve_project(project)
    # Lifecycle
    project.mark_heatloss_dirty()

    return project


# ----------------------------------------------------------------------
# Safety: ensure required constructions exist
# ----------------------------------------------------------------------

def _ensure_default_constructions(ps: ProjectState) -> None:

    ps.constructions.setdefault(
        "DEV-WALL",
        ConstructionV1("DEV-WALL", "External Wall", 0.28),
    )
    ps.constructions.setdefault(
        "DEV-INT-WALL",
        ConstructionV1("DEV-INT-WALL", "Internal Wall", 1.50),
    )
    ps.constructions.setdefault(
        "DEV-ROOF",
        ConstructionV1("DEV-ROOF", "Roof", 0.18),
    )
    ps.constructions.setdefault(
        "DEV-FLOOR",
        ConstructionV1("DEV-FLOOR", "Floor", 0.22),
    )
    ps.constructions.setdefault(
        "DEV-WINDOW",
        ConstructionV1("DEV-WINDOW", "Window", 1.40),
    )


# ----------------------------------------------------------------------
# DEV helper: auto-select first room
# ----------------------------------------------------------------------

def _select_first_room(context: GuiProjectContext) -> None:

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


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> None:
    app = QApplication(sys.argv)

    project_state = make_dev_bootstrap_project_state()
    _ensure_default_constructions(project_state)

    context = GuiProjectContext(project_state=project_state)

    win = MainWindowV3(context=context)
    win.show()

    # Auto-select first room AFTER UI is ready
    QTimer.singleShot(0, lambda: _select_first_room(context))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()