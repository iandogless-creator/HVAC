# ======================================================================
# HVAC/gui_v3/main_window.py
# ======================================================================
# Sub-Phase: Phase II-A — Fabric Navigation & U-Value Readiness (LOCKED)
#
# Phase II-A establishes:
# • Surface-centric navigation (surface_id is the sole identity)
# • A single, canonical U-Values activation path
# • MainWindowV3 as the sole navigation authority
#
# Phase II-A explicitly does NOT modify:
# • HLPE (Edit Overlay) behaviour or ESC handling
# • Adapter fan-out or observer responsibilities
# • Controller execution or readiness evaluation logic
# • Persistence, menus, or dock layout policy
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, QSettings, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QWidget,
    QLabel,
)
from PySide6.QtWidgets import QMenu, QFileDialog, QMessageBox
from pathlib import Path

# ----------------------------------------------------------------------
# GUI context (authority boundary)
# ----------------------------------------------------------------------
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext

# ----------------------------------------------------------------------
# Panels
# ----------------------------------------------------------------------
from HVAC.gui_v3.panels.project_panel import ProjectPanel
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel
from HVAC.gui_v3.panels.construction_panel import ConstructionPanel
from HVAC.gui_v3.panels.uvp_panel import UVPPanel
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.gui_v3.panels.education_panel import EducationPanel
from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel
from HVAC.gui_v3.panels.ach_mini_panel import ACHMiniPanel
from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel
from HVAC.gui_v3.panels.hlpe_overlay_panel import HLPEOverlayPanel

# ----------------------------------------------------------------------
# Adapters (observer / intent routing only)
# ----------------------------------------------------------------------
from HVAC.gui_v3.adapters.project_panel_adapter import ProjectPanelAdapter
from HVAC.gui_v3.adapters.environment_panel_adapter import EnvironmentPanelAdapter
from HVAC.gui_v3.adapters.room_tree_panel_adapter import RoomTreePanelAdapter
from HVAC.gui_v3.adapters.heat_loss_panel_adapter import HeatLossPanelAdapter
from HVAC.gui_v3.adapters.heat_loss_worksheet_adapter import HeatLossWorksheetAdapter
from HVAC.gui_v3.adapters.project_heatloss_readiness_adapter import (
    ProjectHeatLossReadinessAdapter,
)
from HVAC.gui_v3.adapters.education_panel_adapter import EducationPanelAdapter
from HVAC.gui_v3.adapters.geometry_mini_panel_adapter import GeometryMiniPanelAdapter
from HVAC.gui_v3.adapters.ach_mini_panel_adapter import ACHMiniPanelAdapter
from HVAC.gui_v3.adapters.hlpe_overlay_adapter import HLPEOverlayAdapter
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)

# ----------------------------------------------------------------------
# Controllers (stateless orchestrators)
# ----------------------------------------------------------------------
from HVAC.heatloss.controller_v4_orchestrator import HeatLossControllerV4
from HVAC.project_v3.persistence.loader import load as load_project
from HVAC.project_v3.persistence.saver import save as save_project
from HVAC.project_v3.project_factory_v3 import ProjectFactoryV3
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.adapters.geometry_mini_panel_adapter import GeometryMiniPanelAdapter
from HVAC.gui_v3.controllers.overlay_editor_controller import OverlayEditorController
from HVAC.heatloss.fabric.topology_fabric_bridge import generate_fabric_from_boundaries
from HVAC.topology.dev_topology_fabric_bridge import generate_fabric_from_topology
from HVAC.core.value_resolution import resolve_effective_internal_temp_C
from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
from HVAC.topology.dev_rectangular_topology_bootstrap import (
    apply_rectangular_topology_bootstrap
)

class MainWindowV3(QMainWindow):
    """
    GUI v3 main window.

    Observer-only shell:
    • Owns docks, panels, adapters, menus
    • Hosts HLPE (edit overlay)
    • Persists installation-level GUI state
    • Never owns engineering authority
    """

    fix_uvalues_requested = Signal()


    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, context: GuiProjectContext) -> None:
        super().__init__()
        self._context = context

        self.setCentralWidget(QWidget(self))
        self.setWindowTitle("HVACgooee")
        self.setMinimumWidth(260)

        self._settings = QSettings("HVACgooee", "GUIv3")
        settings_dir = Path.home() / ".hvacgooee"
        self._gui_settings = GuiSettings(settings_dir)
        self._build_ui()
        self._build_menu()
        self._wire_context_fanout()
        self._restore_workspace()
        self._heat_loss_panel.geometry_edit_requested.connect(
            self._overlay_controller.open_geometry_editor
        )

        self._heat_loss_panel.ach_edit_requested.connect(
            self._overlay_controller.open_ach_editor
        )
        # Global ESC — SINGLE listener (LOCKED)
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    def _restore_workspace(self) -> None:
        if self._gui_settings.window_geometry:
            self.restoreGeometry(self._gui_settings.window_geometry)

        if self._gui_settings.window_state:
            self.restoreState(self._gui_settings.window_state)


    # ------------------------------------------------------------------
    # Global ESC handling (Phase G-A.1)
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if getattr(self._context, "hlpe_active", False):
                if hasattr(self._context, "exit_hlpe"):
                    self._context.exit_hlpe()
                elif hasattr(self._context, "close_hlpe"):
                    self._context.close_hlpe()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        # Capture current geometry
        self._gui_settings.window_geometry = bytes(self.saveGeometry())
        self._gui_settings.window_state = bytes(self.saveState())

        self._gui_settings.save()

        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Context fan-out
    # ------------------------------------------------------------------
    def _wire_context_fanout(self) -> None:
        if hasattr(self._context, "subscribe_room_selection_changed"):
            self._context.subscribe_room_selection_changed(
                self._on_room_selection_changed
            )

    def _on_room_selection_changed(self, room_id: str | None) -> None:

        ps = self._context.project_state

        if not ps or not room_id:
            return

        room = ps.rooms.get(room_id)

        if not room:
            return

        # --------------------------------------------------
        # DEV bridge: topology → fabric elements
        # --------------------------------------------------

        if hasattr(ps, "boundary_segments"):
            from HVAC.heatloss.fabric.topology_fabric_bridge import generate_fabric_from_boundaries

            # rebuild surfaces for every room
            for r in ps.rooms.values():
                generate_fabric_from_boundaries(ps, r)

        # --------------------------------------------------
        # Set active room
        # --------------------------------------------------

        if hasattr(self._heat_loss_panel, "set_room"):
            self._heat_loss_panel.set_room(room_id)

        # --------------------------------------------------
        # Refresh adapters AFTER surfaces exist
        # --------------------------------------------------

        self._refresh_all_adapters()


    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # Panels
        self._project_panel = ProjectPanel(self)
        self._environment_panel = EnvironmentPanel(self)
        self._room_tree_panel = RoomTreePanel(self)
        self._construction_panel = ConstructionPanel(self)
        self._uvp_panel = UVPPanel(self)
        self._heat_loss_panel = HeatLossPanelV3(self)
        self._education_panel = EducationPanel(self)
        self._hydronics_schematic_panel = HydronicsSchematicPanel(self)
        self._geometry_mini_panel = GeometryMiniPanel(self)
        self._ach_mini_panel = ACHMiniPanel(self)

        # HLPE overlay
        self._overlay_controller = OverlayEditorController(self, self._context)
        self._hlpe_panel = HLPEOverlayPanel(self)
        self._hlpe_overlay_adapter = HLPEOverlayAdapter(
            panel=self._hlpe_panel,
            context=self._context,
        )

        # Docks
        self._dock_project = self._mk_dock("Project", "dock_project", self._project_panel)
        self._dock_environment = self._mk_dock("Environment", "dock_environment", self._environment_panel)
        self._dock_rooms = self._mk_dock("Rooms", "dock_rooms", self._room_tree_panel)
        self._dock_construction = self._mk_dock("Construction", "dock_construction", self._construction_panel)
        self._dock_uvp = self._mk_dock("U-Values", "dock_uvp", self._uvp_panel)
        self._dock_heat_loss = self._mk_dock("Heat-Loss", "dock_heat_loss", self._heat_loss_panel)
        self._dock_education = self._mk_dock("Education", "dock_education", self._education_panel)
        self._dock_hydronics = self._mk_dock("Hydronics Schematic", "dock_hydronics", self._hydronics_schematic_panel)
        self._dock_geometry = self._mk_dock("Geometry", "dock_geometry", self._geometry_mini_panel)
        self._dock_ach = self._mk_dock("ACH", "dock_ach", self._ach_mini_panel)

        for dock in (
                self._dock_project,
                self._dock_environment,
                self._dock_geometry,
                self._dock_ach,
                self._dock_rooms,
                self._dock_construction,
                self._dock_uvp,
        ):
            self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        for dock in (
            self._dock_heat_loss,
            self._dock_education,
            self._dock_hydronics,
        ):
            self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Adapters
        self._environment_panel_adapter = EnvironmentPanelAdapter(
            self._context,
            self._environment_panel,
        )
        self._room_tree_panel_adapter = RoomTreePanelAdapter(
            panel=self._room_tree_panel,
            context=self._context,
        )
        self._heat_loss_panel_adapter = HeatLossPanelAdapter(
            panel=self._heat_loss_panel,
            context=self._context,
        )
        self._project_heatloss_readiness_adapter = ProjectHeatLossReadinessAdapter(
            panel=self._heat_loss_panel,
            context=self._context,
        )

        self._heat_loss_worksheet_adapter = HeatLossWorksheetAdapter(
            panel=self._heat_loss_panel,
            context=self._context,
        )


        self._geometry_mini_panel_adapter = GeometryMiniPanelAdapter(
            self._geometry_mini_panel,
            self._context,
        )

        self._education_panel_adapter = EducationPanelAdapter(
            panel=self._education_panel,
            domain="heatloss",
            topic="overview",
            mode="standard",
        )

        self._hydronics_schematic_panel_adapter = HydronicsSchematicPanelAdapter(
            panel=self._hydronics_schematic_panel,
            project_state=self._context.project_state,
        )

        # ---------------- Phase II-A Navigation Wiring ----------------

        # Construction → U-Values
        self._construction_panel.u_values_requested.connect(
            self._on_uvp_focus_requested
        )

        # Run request (GUI → MainWindow)
        self._heat_loss_panel.run_requested.connect(
            self._on_run_heat_loss_requested
        )

        # Fix U-Values link
        if hasattr(self._heat_loss_panel, "open_uvalues_requested"):
            self._heat_loss_panel.open_uvalues_requested.connect(
                self._on_uvp_focus_requested
            )

        self._heat_loss_panel.ach_changed.connect(
            self._on_ach_changed
        )

    # ------------------------------------------------------------------
    # Phase II-A canonical navigation handler
    # ------------------------------------------------------------------
    def _on_uvp_focus_requested(self, surface_id: str | None) -> None:
        self._dock_uvp.show()
        self._dock_uvp.raise_()
        self._context.set_uvp_focus(surface_id)

    # ------------------------------------------------------------------
    # Run action
    # ------------------------------------------------------------------
    def _on_run_heat_loss_requested(self) -> None:
        self._rebuild_dev_fabric_for_current_room()
        ps = self._context.project_state
        room_id = self._context.current_room_id
        controller = HeatLossControllerV4(
            project_state=self._context.project_state
        )

        self._refresh_all_adapters()
        if ps is None or room_id is None:
            return

        # --------------------------------------------------
        # 1️⃣ Force commit from mini panels
        # --------------------------------------------------

        if hasattr(self._geometry_mini_panel, "commit_if_valid"):
            self._geometry_mini_panel.commit_if_valid()

        if hasattr(self._ach_mini_panel, "commit_if_valid"):
            self._ach_mini_panel.commit_if_valid()

        # --------------------------------------------------
        # 2️⃣ Resolve inputs
        # --------------------------------------------------

        room = ps.rooms.get(room_id)
        if room is None:
            return

        ti_C, _ = resolve_effective_internal_temp_C(ps, room)
        ach = self._heat_loss_panel._ach_input.value()

        # --------------------------------------------------
        # 3️⃣ Execute controller
        # --------------------------------------------------

        controller = HeatLossControllerV4(
            project_state=ps
        )

        # ⚠️ adjust this to your actual controller API
        controller.run_for_room(
            room_id=room_id,
            internal_temp_C=ti_C,
            ach=ach,
        )

        # --------------------------------------------------
        # 4️⃣ Refresh GUI
        # --------------------------------------------------

        self._refresh_all_adapters()


    def _build_menu(self) -> None:
        menubar = self.menuBar()

        # ---------------------------
        # File Menu
        # ---------------------------
        file_menu = menubar.addMenu("File")

        action_new = QAction("New Project", self)
        action_new.triggered.connect(self.new_project)
        file_menu.addAction(action_new)

        action_open = QAction("Open Project…", self)
        action_open.triggered.connect(self._open_project)
        file_menu.addAction(action_open)

        file_menu.addSeparator()

        action_save = QAction("Save", self)
        action_save.triggered.connect(self._save_project)
        file_menu.addAction(action_save)

        action_save_as = QAction("Save As…", self)
        action_save_as.triggered.connect(self._save_project_as)
        file_menu.addAction(action_save_as)

        file_menu.addSeparator()

        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # ---------------------------
        # View Menu
        # ---------------------------
        view_menu = menubar.addMenu("View")

        for dock in self.findChildren(QDockWidget):
            view_menu.addAction(dock.toggleViewAction())

        # ---------------------------
        # Help Menu
        # ---------------------------
        help_menu = menubar.addMenu("Help")

        action_about = QAction("About HVACgooee", self)
        action_about.triggered.connect(self._show_about)
        help_menu.addAction(action_about)

    def new_project(self) -> None:

        project_state = ProjectFactoryV3.create_default()

        self._context.set_project_state(
            project_state,
            project_dir=None,
        )
        self._refresh_all()

    def _open_project(self) -> None:

        # --------------------------------------------------
        # Select project directory
        # --------------------------------------------------

        hvac_root = Path(__file__).resolve().parents[1]
        default_dir = hvac_root / "HVACprojects"

        directory = QFileDialog.getExistingDirectory(
            self,
            "Open Project",
            str(default_dir),
        )

        if not directory:
            return

        project_dir = Path(directory)

        # --------------------------------------------------
        # Load project
        # --------------------------------------------------

        project_state = load_project(project_dir)

        ps = project_state

        if not ps.construction_library:
            ps.construction_library = {
                "DEV-WALL": 0.28,
                "DEV-ROOF": 0.18,
                "DEV-WINDOW": 1.40,
            }

        # --------------------------------------------------
        # Normalise environment defaults
        # --------------------------------------------------

        env = project_state.environment

        if env.default_internal_temp_C is None:
            env.default_internal_temp_C = 21.0

        if env.default_room_height_m is None:
            env.default_room_height_m = 2.4

        if env.default_ach is None:
            env.default_ach = 0.5

        TopologyResolverV1.resolve_project(project_state)
        # --------------------------------------------------
        # Attach project to GUI context
        # --------------------------------------------------

        self._context.set_project_state(
            project_state,
            project_dir=project_dir,
        )

        # --------------------------------------------------
        # Auto-select first room
        # --------------------------------------------------

        rooms = list(project_state.rooms.keys())

        if rooms:
            first_room_id = rooms[0]
            self._on_room_selection_changed(first_room_id)

        # --------------------------------------------------
        # Update panels
        # --------------------------------------------------

        self._heat_loss_panel.update_room_totals_from_project(project_state)
        from HVAC.topology.dev_two_room_adjacency_bootstrap import (
            apply_two_room_adjacency_bootstrap,
        )

        apply_two_room_adjacency_bootstrap(project_state)
        project_state.construction_library = {
            "DEV-WALL": 0.35,
            "DEV-ROOF": 0.18,
        }
        self._refresh_all_adapters()


    def _save_project(self) -> None:
        project = self._context.project_state

        if project.project_dir is None:
            self._save_project_as()
            return

        save_project(project, project.project_dir)

    def _save_project_as(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Save Project As")
        if not directory:
            return

        project_dir = Path(directory)
        self._context.project_state.project_dir = project_dir
        save_project(self._context.project_state, project_dir)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About HVACgooee",
            "HVACgooee\n"
            "© 1989–2026 ian allison\n\n"
            "Phase III Persistence Architecture\n"
            "ProjectState — Sole Authority Model"
        )

    def _rebuild_dev_fabric_for_current_room(self) -> None:

        ps = self._context.project_state
        room_id = self._context.current_room_id

        if not ps or not room_id:
            return

        room = ps.rooms.get(room_id)
        if not room:
            return

        rows = generate_fabric_from_topology(ps, room)
        room._dev_fabric_rows = rows
    # ------------------------------------------------------------------
    # Refresh all GUI adapters
    # ------------------------------------------------------------------

    def _refresh_all(self) -> None:

        if hasattr(self, "_project_panel_adapter"):
            self._project_panel_adapter.refresh()

        if hasattr(self, "_environment_panel_adapter"):
            self._environment_panel_adapter.refresh()

        if hasattr(self, "_room_tree_panel_adapter"):
            self._room_tree_panel_adapter.refresh()

        if hasattr(self, "_heat_loss_panel_adapter"):
            self._heat_loss_panel_adapter.refresh()

    # ------------------------------------------------------------------
    # Dock helpers, menus, persistence, refresh
    # ------------------------------------------------------------------
    def _mk_dock(self, title: str, object_name: str, widget: QWidget) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setObjectName(object_name)
        dock.setWidget(widget)
        return dock

    # (menus, persistence, refresh unchanged from your original)
    def _on_ach_changed(self, value: float) -> None:
        ps = self._context.project_state
        if ps is None:
            return

        ps.mark_heatloss_dirty()
        self._refresh_all_adapters()
    # ------------------------------------------------------------------
    # Phase II-B: Adapter Refresh Hub
    # ------------------------------------------------------------------
    def _refresh_all_adapters(self) -> None:
        """
        Central refresh point for all GUI adapters.

        Phase II-B contract:
        - Readiness adapter refresh
        - Worksheet adapter refresh
        - Any other adapters that reflect current room/project state
        """

        # Heat-Loss panel main adapter (rows + header)
        if hasattr(self, "_heat_loss_panel_adapter"):
            self._heat_loss_panel_adapter.refresh()

        # Heat-Loss worksheet
        if hasattr(self, "_heat_loss_worksheet_adapter"):
            self._heat_loss_worksheet_adapter.refresh()

        # Heat-Loss readiness
        if hasattr(self, "_project_heatloss_readiness_adapter"):
            self._project_heatloss_readiness_adapter.refresh()

        # Environment
        if hasattr(self, "_environment_panel_adapter"):
            self._environment_panel_adapter.refresh()

        # Room readiness (authoritative from ProjectState)
        if self._context.project_state:
            readiness = self._context.project_state.evaluate_heatloss_readiness()
            self._heat_loss_panel.set_readiness(readiness)

        # Room tree
        if hasattr(self, "_room_tree_panel_adapter"):
            self._room_tree_panel_adapter.refresh()