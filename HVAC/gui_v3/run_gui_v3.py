# ======================================================================
# HVACgooee — GUI v3 Runner — Beta 1
# ======================================================================

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.main_window import MainWindowV3
from HVAC.gui_v3.widgets.startup_splash_widget_v1 import (
    StartupSplashWidgetV1,
)

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
        "DEV-EXT-WALL": ConstructionV1("DEV-EXT-WALL", "External Wall", 0.26),
        "DEV-INT-WALL": ConstructionV1("DEV-INT-WALL", "Internal Wall", 1.50),
        "DEV-ROOF": ConstructionV1("DEV-ROOF", "Roof / Ceiling", 0.16),
        "DEV-FLOOR": ConstructionV1("DEV-FLOOR", "Floor", 0.18),
        "DEV-WINDOW": ConstructionV1("DEV-WINDOW", "Window / Door", 1.60),
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
        ConstructionV1("DEV-WALL", "External Wall", 0.26),
    )
    ps.constructions.setdefault(
        "DEV-INT-WALL",
        ConstructionV1("DEV-INT-WALL", "Internal Wall", 1.50),
    )
    ps.constructions.setdefault(
        "DEV-ROOF",
        ConstructionV1("DEV-ROOF", "Roof / Ceiling", 0.16),
    )
    ps.constructions.setdefault(
        "DEV-FLOOR",
        ConstructionV1("DEV-FLOOR", "Floor", 0.18),
    )
    ps.constructions.setdefault(
        "DEV-WINDOW",
        ConstructionV1("DEV-WINDOW", "Window / Door", 1.60),
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
    from HVAC.version import __version__, DISPLAY_VERSION
    from HVAC.gui_v3.widgets.startup_project_dialog_v1 import StartupProjectDialogV1
    from HVAC.gui_v3.context.startup_projects_v1 import create_new_project_v1, open_project_v1

    if "--version" in sys.argv[1:]:
        print(f"HVACgooee {DISPLAY_VERSION}")
        return
    app = QApplication(sys.argv)
    app.setApplicationName("HVACgooee")
    app.setApplicationVersion(__version__)
    # Keep the event loop alive while the chooser hands over to the splash.
    app.setQuitOnLastWindowClosed(False)
    while True:
        chooser = StartupProjectDialogV1()
        if chooser.exec() != QDialog.Accepted:
            return
        try:
            if chooser.action == "open":
                project_state = open_project_v1(chooser.project_dir)
            elif chooser.action == "sample":
                project_state = make_dev_bootstrap_project_state()
                project_state.name = "HVACgooee sample — review example inputs"
            else:
                project_state = create_new_project_v1()
            break
        except (OSError, ValueError, RuntimeError) as exc:
            QMessageBox.warning(None, "Project could not be opened", str(exc))

    splash = StartupSplashWidgetV1()
    splash.show()
    runtime_v1 = {"splash": splash, "project": project_state}

    def build_main_window_v1() -> None:
        try:
            context = GuiProjectContext(project_state=project_state)
            context.project_dir = getattr(project_state, "project_dir", None)
            win = MainWindowV3(context=context)
            runtime_v1.update(context=context, window=win)
            splash.finish_v1(win)
            app.setQuitOnLastWindowClosed(True)
            QTimer.singleShot(0, lambda: _select_first_room(context))
        except Exception as exc:
            splash.close()
            QMessageBox.critical(None, "HVACgooee could not start", str(exc))
            app.exit(1)

    QTimer.singleShot(splash.remaining_minimum_ms_v1(), build_main_window_v1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()