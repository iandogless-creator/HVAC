# ======================================================================
# HVAC/gui_v3/main_window.py
# ======================================================================

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QSettings, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QWidget,
    QFileDialog,
)

# ----------------------------------------------------------------------
# Context
# ----------------------------------------------------------------------
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.context.gui_settings import GuiSettings

# ----------------------------------------------------------------------
# Panels
# ----------------------------------------------------------------------
from HVAC.gui_v3.panels.project_panel import ProjectPanel
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel
from HVAC.gui_v3.panels.construction_panel import ConstructionPanel
from HVAC.gui_v3.panels.uvp_panel import UVPPanel
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.gui_v3.panels.education_panel import EducationPanel
from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel
from HVAC.gui_v3.panels.hlpe_overlay_panel import HLPEOverlayPanel
from HVAC.gui_v3.panels.dev_settings_panel import DevSettingsPanel
from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel
from HVAC.gui_v3.panels.ach_mini_panel import ACHMiniPanel
# ----------------------------------------------------------------------
# Adapters
# ----------------------------------------------------------------------
from HVAC.gui_v3.adapters.environment_panel_adapter import EnvironmentPanelAdapter
from HVAC.gui_v3.adapters.room_tree_panel_adapter import RoomTreePanelAdapter
from HVAC.gui_v3.adapters.heat_loss_panel_adapter import HeatLossPanelAdapter
from HVAC.gui_v3.adapters.project_heatloss_readiness_adapter import (
    ProjectHeatLossReadinessAdapter,
)
from HVAC.gui_v3.adapters.education_panel_adapter import EducationPanelAdapter
from HVAC.gui_v3.adapters.hlpe_overlay_adapter import HLPEOverlayAdapter
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)

from HVAC.gui_v3.adapters.geometry_mini_panel_adapter import GeometryMiniPanelAdapter
from HVAC.gui_v3.adapters.ach_mini_panel_adapter import ACHMiniPanelAdapter

# ----------------------------------------------------------------------
# Controllers / Core
# ----------------------------------------------------------------------
from HVAC.gui_v3.controllers.overlay_editor_controller import OverlayEditorController
from HVAC.gui_v3.common.edit_context import EditContext

from HVAC.heatloss.controller_v4_orchestrator import HeatLossControllerV4
from HVAC.project_v3.persistence.loader import load as load_project
from HVAC.project_v3.persistence.saver import save as save_project
from HVAC.project_v3.project_factory_v3 import ProjectFactoryV3
from HVAC.project.project_state import ProjectState
from HVAC.core.value_resolution import resolve_effective_internal_temp_C
from HVAC.gui_v3.adapters.uvp_panel_adapter import UVPPanelAdapter
from HVAC.dev.bootstrap_dev_project import build_dev_project

# ======================================================================
# Main Window
# ======================================================================
from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication

class MainWindowV3(QMainWindow):

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, *, context: GuiProjectContext) -> None:
        super().__init__()

        # --------------------------------------------------
        # Core
        # --------------------------------------------------
        self._context = context

        self._overlay_editor_controller = OverlayEditorController(
            main_window=self,
            context=self._context,
        )
        self._panels: dict[str, QWidget] = {}
        self._docks: dict[str, QDockWidget] = {}

        # --------------------------------------------------
        # Central widget must exist before docks are arranged
        # --------------------------------------------------
        self.setCentralWidget(QWidget(self))

        # --------------------------------------------------
        # Build UI (creates panels + adapters)
        # --------------------------------------------------
        self._build_ui()

        # --------------------------------------------------
        # Wire DEV panel
        # --------------------------------------------------
        self._dev_panel.mode_changed.connect(self._on_dev_mode_changed)

        # --------------------------------------------------
        # Wire context → adapters (NOW SAFE)
        # --------------------------------------------------
        self._context.project_changed.connect(
            self._heat_loss_panel_adapter.refresh
        )
        self._context.project_changed.connect(
            self._uvp_panel_adapter.refresh
        )

        # --------------------------------------------------
        # Other panel wiring
        # --------------------------------------------------
        self._heat_loss_panel.adjacency_edit_requested.connect(
            self._overlay_editor_controller.show_adjacency_editor
        )

        self._uvp_panel.u_value_changed.connect(self._on_u_changed)
        self._uvp_panel.assign_requested.connect(self._on_assign)

        self._heat_loss_panel.add_room_requested.connect(
            self._on_add_room_requested
        )

        # --------------------------------------------------
        # Window setup
        # --------------------------------------------------
        self.setWindowTitle("HVACgooee")
        self.setMinimumWidth(260)

        # --------------------------------------------------
        # Settings
        # --------------------------------------------------
        self._settings = QSettings("HVACgooee", "GUIv3")
        self._gui_settings = GuiSettings(Path.home() / ".hvacgooee")

        self._context.edit_requested.connect(self._on_edit_requested)

        self._build_menu()
        self._wire_context_fanout()
        self._restore_workspace()

        # --------------------------------------------------
        # ESC handler
        # --------------------------------------------------
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

    # ------------------------------------------------------------------
    # Workspace persistence
    # ------------------------------------------------------------------
    def _restore_workspace(self) -> None:
        if self._gui_settings.window_geometry:
            self.restoreGeometry(self._gui_settings.window_geometry)

        if self._gui_settings.window_state:
            self.restoreState(self._gui_settings.window_state)

    def closeEvent(self, event):
        self._gui_settings.window_geometry = bytes(self.saveGeometry())
        self._gui_settings.window_state = bytes(self.saveState())
        self._gui_settings.save()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # ESC handling
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if getattr(self._context, "hlpe_active", False):
                if hasattr(self._context, "exit_hlpe"):
                    self._context.exit_hlpe()
                return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:

        # --------------------------------------------------
        # Panels (SINGLE-INSTANCE REGISTRY)
        # --------------------------------------------------

        self._project_panel = self._register_panel(
            "project",
            ProjectPanel(self),
        )

        self._environment_panel = self._register_panel(
            "environment",
            EnvironmentPanel(self),
        )

        self._room_tree_panel = self._register_panel(
            "rooms",
            RoomTreePanel(self),
        )

        self._construction_panel = self._register_panel(
            "construction",
            ConstructionPanel(self),
        )

        self._uvp_panel = self._register_panel(
            "uvp",
            UVPPanel(self._context, self),
        )

        self._heat_loss_panel = self._register_panel(
            "heat_loss",
            HeatLossPanelV3(self),
        )

        self._education_panel = self._register_panel(
            "education",
            EducationPanel(self),
        )

        self._hydronics_panel = self._register_panel(
            "hydronics",
            HydronicsSchematicPanel(self),
        )

        self._dev_panel = self._register_panel(
            "dev",
            DevSettingsPanel(self),
        )

        self._geometry_mini_panel = self._register_panel(
            "geometry",
            GeometryMiniPanel(self),
        )

        self._ach_mini_panel = self._register_panel(
            "ach",
            ACHMiniPanel(self),
        )

        # --------------------------------------------------
        # Overlay (NOT docked, still single-instance)
        # --------------------------------------------------

        self._overlay_controller = OverlayEditorController(self, self._context)

        self._hlpe_panel = self._register_panel(
            "hlpe_overlay",
            HLPEOverlayPanel(self),
        )

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
        self._dock_hydronics = self._mk_dock("Hydronics", "dock_hydronics", self._hydronics_panel)
        self._dock_dev = self._mk_dock("Dev", "dock_dev", self._dev_panel)
        self._dock_geometry = self._mk_dock("Geometry", "dock_geometry", self._geometry_mini_panel)
        self._dock_ach = self._mk_dock("ACH", "dock_ach", self._ach_mini_panel)

        for d in (
                self._dock_project,
                self._dock_environment,
                self._dock_rooms,
                self._dock_construction,
                self._dock_uvp,
        ):
            self.addDockWidget(Qt.LeftDockWidgetArea, d)

        for d in (
                self._dock_heat_loss,
                self._dock_education,
                self._dock_hydronics,
                self._dock_dev,
                self._dock_geometry,
                self._dock_ach,
        ):
            self.addDockWidget(Qt.RightDockWidgetArea, d)

            self._dock_dev.show()
            self._dock_dev.raise_()
            self._dev_panel.raise_()
        # --------------------------------------------------
        # --------------------------------------------------
        # Utility / DEV docks as tabs, not vertical clutter
        # --------------------------------------------------

        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_dev)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_geometry)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_ach)

        self.tabifyDockWidget(self._dock_hydronics, self._dock_dev)
        self.tabifyDockWidget(self._dock_hydronics, self._dock_geometry)
        self.tabifyDockWidget(self._dock_hydronics, self._dock_ach)

        # Show DEV tab initially while debugging
        self._dock_dev.show()
        self._dock_dev.raise_()


        # Adapters
        self._environment_panel_adapter = EnvironmentPanelAdapter(self._context, self._environment_panel)
        self._room_tree_panel_adapter = RoomTreePanelAdapter(panel=self._room_tree_panel, context=self._context)
        self._heat_loss_panel_adapter = HeatLossPanelAdapter(panel=self._heat_loss_panel, context=self._context)
        self._readiness_adapter = ProjectHeatLossReadinessAdapter(panel=self._heat_loss_panel, context=self._context)
        self._education_panel_adapter = EducationPanelAdapter(panel=self._education_panel, domain="heatloss", topic="overview", mode="standard")
        self._hydronics_adapter = HydronicsSchematicPanelAdapter(panel=self._hydronics_panel, project_state=self._context.project_state)
        self._geometry_adapter = GeometryMiniPanelAdapter(
            panel=self._geometry_mini_panel,
            context=self._context,
            refresh_all_callback=self._refresh_all_adapters,
        )
        self._heat_loss_panel_adapter = HeatLossPanelAdapter(
            panel=self._heat_loss_panel,
            context=self._context,
        )

        self._uvp_panel_adapter = UVPPanelAdapter(
            panel=self._uvp_panel,
            context=self._context,
        )

        self._readiness_adapter = ProjectHeatLossReadinessAdapter(
            panel=self._heat_loss_panel,
            context=self._context,
        )
        self._ach_adapter = ACHMiniPanelAdapter(
            panel=self._ach_mini_panel,
            context=self._context,
            refresh_all_callback=self._refresh_all_adapters,
        )
        # Wiring
        self._construction_panel.u_values_requested.connect(self._on_uvp_focus_requested)

        # --------------------------------------------------
        # UVP wiring
        # --------------------------------------------------
        self._heat_loss_panel.open_uvalues_requested.connect(
            self._uvp_panel.set_selected_surface
        )

        if hasattr(self._heat_loss_panel, "surface_focus_requested"):
            self._heat_loss_panel.surface_focus_requested.connect(
                self._uvp_panel.set_selected_surface
            )

        self._uvp_panel.construction_selected.connect(
            self._on_uvp_construction_selected
        )

        # initial population
        self._uvp_panel.set_constructions(self._context.project_state.constructions)
        if hasattr(self._heat_loss_panel, "open_uvalues_requested"):
            self._heat_loss_panel.open_uvalues_requested.connect(self._on_uvp_focus_requested)

    # ------------------------------------------------------------------
    # Adapter wiring
    # ------------------------------------------------------------------

    def _on_uvp_construction_selected(self, cid: str) -> None:
        ps = self._context.project_state
        construction = ps.constructions.get(cid)
        if construction is None:
            return

        self._uvp_panel.set_u_value(construction.u_value_W_m2K)

    def _on_edit_requested(self, kind: str, surface_id: str) -> None:
        context = self._context

        if context is None:
            return

        room_id = context.current_room_id
        if not room_id:
            return

        self._overlay_controller.activate(
            EditContext(
                kind=kind,
                room_id=room_id,
                surface_id=surface_id,
            )
        )

    def _on_u_changed(self, cid: str, value: float) -> None:
        ps = self._context.project_state

        construction = ps.constructions.get(cid)
        if construction is None:
            return

        construction.u_value_W_m2K = float(value)
        ps.mark_heatloss_dirty()

        self._uvp_panel.set_u_value(construction.u_value_W_m2K)
        self._refresh_all_adapters()

    def _on_assign(self, surface_id: str, cid: str) -> None:
        ps = self._context.project_state

        from HVAC.gui_v3.wizards.construction_wizard import ConstructionWizard

        ConstructionWizard.set_surface_construction(ps, surface_id, cid)
        ps.mark_heatloss_dirty()

        self._uvp_panel.set_selected_surface(surface_id)
        self._refresh_all_adapters()

    def _on_dev_mode_changed(self, mode: str) -> None:
        ps = build_dev_project(mode)

        self._context.set_project_state(ps, project_dir=None)

        self._uvp_panel.set_constructions(ps.constructions)
        self._refresh_all_adapters()


    def _create_default_room(self, project: ProjectState) -> str:
        room_id = "room-001"

        from HVAC.core.room_state import RoomStateV1, RoomGeometryV1

        room = RoomStateV1(
            room_id=room_id,
            name="Room 1",
            geometry=RoomGeometryV1(
                length_m=4.0,
                width_m=3.0,
                height_m=2.4,
                external_wall_length_m=14.0,
            ),
        )

        # ❌ REMOVE THIS (legacy)
        # room.fabric_elements = []

        project.rooms[room_id] = room
        return room_id

    def _on_add_room_requested(self):

        ps = self._context.project_state
        if ps is None:
            return

        # --------------------------------------------------
        # Create new room ID
        # --------------------------------------------------
        idx = len(ps.rooms) + 1
        room_id = f"room_{idx:03d}"

        # --------------------------------------------------
        # Create room
        # --------------------------------------------------
        from HVAC.core.room_state import RoomStateV1
        from HVAC.core.room_geometry import RoomGeometryV1

        ps.rooms[room_id] = RoomStateV1(
            room_id=room_id,
            name=f"Room {idx}",
            geometry=RoomGeometryV1(
                length_m=4.0,
                width_m=3.0,
                height_m=2.4,
            ),
        )

        # --------------------------------------------------
        # 🔥 THIS IS WHERE YOUR LINES GO
        # --------------------------------------------------
        from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
        from HVAC.topology.topology_symmetry_enforcer_v1 import TopologySymmetryEnforcerV1

        TopologyResolverV1.resolve_project(ps)
        TopologySymmetryEnforcerV1.enforce(ps)

        # --------------------------------------------------
        # Mark dirty
        # --------------------------------------------------
        ps.mark_heatloss_dirty()

        # --------------------------------------------------
        # Refresh UI
        # --------------------------------------------------
        self._context.set_project_state(ps)
        self._context.set_current_room(room_id)

    # ------------------------------------------------------------------
    # Overlay triggers
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Project lifecycle
    # ------------------------------------------------------------------
    def new_project(self) -> None:
        project_state = ProjectFactoryV3.create_default()

        # --------------------------------------------------
        # Create default room
        # --------------------------------------------------
        room_id = self._create_default_room(project_state)

        # --------------------------------------------------
        # Build topology (canonical)
        # --------------------------------------------------
        from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
        from HVAC.topology.topology_symmetry_enforcer_v1 import TopologySymmetryEnforcerV1

        TopologyResolverV1.resolve_project(project_state)
        TopologySymmetryEnforcerV1.enforce(project_state)

        # 🔒 Safety check
        if not project_state.boundary_segments:
            raise RuntimeError("Topology creation failed")

        print(f"[TOPOLOGY] created: {len(project_state.boundary_segments)} segments")

        # --------------------------------------------------
        # Bind project (AFTER complete state)
        # --------------------------------------------------
        self._context.set_project_state(
            project_state,
            project_dir=None,
        )
        self._uvp_panel.set_constructions(project_state.constructions)

        # --------------------------------------------------
        # Select room (signal-safe)
        # --------------------------------------------------
        self._context.set_current_room(room_id)

        # --------------------------------------------------
        # Refresh UI
        # --------------------------------------------------
        self._refresh_all_adapters()

    def _open_project(self) -> None:

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
        ps = load_project(project_dir)

        # --------------------------------------------------
        # 🔥 DROP LEGACY TOPOLOGY
        # --------------------------------------------------
        ps.boundary_segments = {}

        # --------------------------------------------------
        # Ensure constructions (Phase V-A)
        # --------------------------------------------------
        from HVAC.core.construction_v1 import ConstructionV1

        def _ensure_construction(ps, cid, name, u):
            if cid not in ps.constructions:
                ps.constructions[cid] = ConstructionV1(cid, name, u)

        _ensure_construction(ps, "DEV-EXT-WALL", "External Wall", 0.28)
        _ensure_construction(ps, "DEV-ROOF", "Roof", 0.18)
        _ensure_construction(ps, "DEV-WINDOW", "Window", 1.40)
        _ensure_construction(ps, "DEV-INT-WALL", "Internal Wall", 1.50)
        _ensure_construction(ps, "DEV-FLOOR", "Floor", 0.22)


        # --------------------------------------------------
        # Normalise environment
        # --------------------------------------------------
        env = ps.environment

        if env.default_internal_temp_C is None:
            env.default_internal_temp_C = 21.0

        if env.default_room_height_m is None:
            env.default_room_height_m = 2.4

        if env.default_ach is None:
            env.default_ach = 0.5

        # --------------------------------------------------
        # Rebuild topology (canonical)
        # --------------------------------------------------
        from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
        from HVAC.topology.topology_symmetry_enforcer_v1 import TopologySymmetryEnforcerV1

        TopologyResolverV1.resolve_project(ps)
        TopologySymmetryEnforcerV1.enforce(ps)

        print(f"[TOPOLOGY] rebuilt: {len(ps.boundary_segments)} segments")

        # --------------------------------------------------
        # Bind project (AFTER rebuild)
        # --------------------------------------------------
        self._context.set_project_state(
            ps,
            project_dir=project_dir,
        )
        self._uvp_panel.set_constructions(ps.constructions)
        # --------------------------------------------------
        # Select first room
        # --------------------------------------------------
        rooms = list(ps.rooms.keys())
        if rooms:
            self._context.set_current_room(rooms[0])

        # --------------------------------------------------
        # Refresh UI
        # --------------------------------------------------
        self._heat_loss_panel.update_room_totals_from_project(ps)
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

    def _wire_context_fanout(self) -> None:

        # Existing refresh fanout
        if hasattr(self._context, "subscribe_room_selection_changed"):
            self._context.subscribe_room_selection_changed(
                lambda _: self._refresh_all_adapters()
            )


    # ------------------------------------------------------------------
    # Adjacency
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _on_uvp_focus_requested(self, surface_id: str | None) -> None:
        self._dock_uvp.show()
        self._dock_uvp.raise_()
        self._uvp_panel.set_selected_surface(surface_id)
        self._context.set_uvp_focus(surface_id)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
    def _refresh_all_adapters(self) -> None:

        if hasattr(self, "_heat_loss_panel_adapter"):
            self._heat_loss_panel_adapter.refresh()

        if hasattr(self, "_readiness_adapter"):
            self._readiness_adapter.refresh()

        if hasattr(self, "_environment_panel_adapter"):
            self._environment_panel_adapter.refresh()

        if hasattr(self, "_room_tree_panel_adapter"):
            self._room_tree_panel_adapter.refresh()

        if hasattr(self, "_uvp_panel_adapter"):
            self._uvp_panel_adapter.refresh()

        if self._context.project_state:
            readiness = self._context.project_state.evaluate_heatloss_readiness()
            self._heat_loss_panel.set_readiness(readiness)


    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _mk_dock(self, title: str, name: str, widget: QWidget) -> QDockWidget:
        if name in self._docks:
            raise RuntimeError(f"Dock already exists: {name}")

        d = QDockWidget(title, self)
        d.setObjectName(name)
        d.setWidget(widget)

        self._docks[name] = d
        return d

    def _register_panel(self, key: str, widget: QWidget) -> QWidget:
        if key in self._panels:
            raise RuntimeError(f"Panel already exists: {key}")

        self._panels[key] = widget
        print(f"[PANEL REGISTERED] {key} -> {id(widget)}")  # ✅ correct place
        return widget