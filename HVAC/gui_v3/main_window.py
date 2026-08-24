# ======================================================================
# HVAC/gui_v3/main_window.py
# ======================================================================

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QSettings, QTimer, Signal, QObject
from PySide6.QtGui import QAction, QActionGroup, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QWidget,
    QFileDialog,
)
from typing import TypeVar

# ----------------------------------------------------------------------
# Context
# ----------------------------------------------------------------------
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.context.appearance_scheme_v1 import (
    application_palette_v1,
    application_stylesheet_v1,
)
from HVAC.gui_v3.context.panel_category_v1 import (
    panel_category_for_dock_id_v1,
)
from HVAC.gui_v3.context.workspace_view_geometry_v1 import (
    WorkspaceScreenGeometryV1,
    resolve_exploded_dock_geometry_v1,
    resolve_user_workspace_dock_geometry_v1,
)
from HVAC.education.workspace_guidance_v1 import (
    education_topic_for_dock_id_v1,
)

# ----------------------------------------------------------------------
# Panels
# ----------------------------------------------------------------------
from HVAC.gui_v3.panels.project_panel import ProjectPanel
from HVAC.gui_v3.adapters.project_panel_adapter import ProjectPanelAdapter
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
from HVAC.gui_v3.common.wheel_input_safety_v1 import (
    redirect_unsafe_input_wheel_event_v1,
)

from HVAC.heatloss.controller_v4_orchestrator import HeatLossControllerV4
from HVAC.project_v3.persistence.loader import load as load_project
from HVAC.project_v3.persistence.saver import save as save_project
from HVAC.project_v3.project_factory_v3 import ProjectFactoryV3
from HVAC.project.project_state import ProjectState
from HVAC.core.value_resolution import resolve_effective_internal_temp_C
from HVAC.gui_v3.adapters.uvp_panel_adapter import UVPPanelAdapter
from HVAC.dev.bootstrap_dev_project import build_dev_project
from HVAC.gui_v3.adapters.construction_panel_adapter import ConstructionPanelAdapter
from HVAC.gui_v3.adapters.wall_wizard_adapter import WallWizardAdapter
from HVAC.gui_v3.panels.hydronic_control_panel import HydronicControlPanel
from HVAC.gui_v3.adapters.hydronic_control_panel_adapter import (
    HydronicControlPanelAdapter,
)
from HVAC.gui_v3.panels.local_k_panel import LocalKPanel
from HVAC.gui_v3.adapters.local_k_panel_adapter import LocalKPanelAdapter
from HVAC.gui_v3.panels.basic_hydronics_panel import BasicHydronicsPanel
from HVAC.gui_v3.adapters.basic_hydronics_panel_adapter import (
    BasicHydronicsPanelAdapter,
)
from HVAC.gui_v3.panels.topology_arranger_panel import TopologyArrangerPanel
from HVAC.gui_v3.adapters.topology_arranger_panel_adapter import (
    TopologyArrangerPanelAdapter,
)
# ======================================================================
# Main Window
# ======================================================================
PanelT = TypeVar("PanelT", bound=QWidget)

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
            self._refresh_all_adapters
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
        self._heat_loss_panel.remove_room_requested.connect(
            lambda room_id: (
                self._room_tree_panel_adapter.request_room_removal_v1(
                    room_id,
                    parent=self._heat_loss_panel,
                )
            )
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
        self._context.construction_focus_changed.connect(
            self._on_construction_focus_changed
        )
        self._build_menu()
        self._apply_appearance_scheme_v1(
            self._gui_settings.appearance_scheme_v1(),
            persist=False,
        )
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
        # H-S69-B3A — never feed an opaque, potentially obsolete dock-state
        # blob back into Qt. Named exploded-view geometry is restored by the
        # owning view preset in H-S69-B3B.
        # Restore the selected named presentation only after Qt has entered
        # its event loop, so screen and floating-window geometry are ready.
        QTimer.singleShot(0, self._restore_last_workspace_presentation_v1)

    def _restore_last_workspace_presentation_v1(self) -> None:
        presentation = (
            self._gui_settings.last_workspace_presentation_v1()
        )
        if presentation is None:
            return

        view_id = presentation["view_id"]
        mode = presentation["mode"]
        handlers = {
            ("heat_loss", "docked"): self._apply_heat_loss_view_v1,
            ("building_edit", "docked"): self._apply_building_edit_view_v1,
            ("openings", "docked"): self._apply_openings_view_v1,
            ("hydronics_setup", "docked"): self._apply_hydronics_setup_view_v1,
            ("basic_sizing", "docked"): self._apply_basic_sizing_view_v1,
            ("proportioning", "docked"): self._apply_proportioning_view_v1,
            ("results", "docked"): self._apply_hydronics_results_view_v1,
            ("heat_loss", "exploded"): self._apply_heat_loss_exploded_view_v1,
            ("building_edit", "exploded"): self._apply_building_edit_exploded_view_v1,
            ("openings", "exploded"): self._apply_openings_exploded_view_v1,
            ("hydronics_setup", "exploded"): self._apply_hydronics_setup_exploded_view_v1,
            ("basic_sizing", "exploded"): self._apply_basic_sizing_exploded_view_v1,
            ("proportioning", "exploded"): self._apply_proportioning_exploded_view_v1,
            ("results", "exploded"): self._apply_hydronics_results_exploded_view_v1,
            ("user", "exploded"): self._apply_user_workspace_v1,
        }
        handler = handlers.get((view_id, mode))
        if handler is not None:
            handler()

    def closeEvent(self, event):
        self._save_active_exploded_workspace_layout_v1()
        self._gui_settings.window_geometry = bytes(self.saveGeometry())
        self._gui_settings.window_state = None
        self._gui_settings.save()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # H-S69-B3J1B — global active dock-panel focus
    # ------------------------------------------------------------------
    @staticmethod
    def _refresh_dock_focus_style_v1(dock: QDockWidget) -> None:
        style = dock.style()
        if style is not None:
            style.unpolish(dock)
            style.polish(dock)
        dock.update()

    def _update_active_dock_focus_v1(self, obj: object) -> None:
        current = obj if isinstance(obj, QObject) else None
        seen: set[int] = set()
        dock: QDockWidget | None = None
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            if isinstance(current, QDockWidget):
                dock = current
                break
            current = current.parent()

        if dock is None or dock.objectName() not in self._docks:
            return

        previous = getattr(self, "_active_focus_dock_v1", None)
        if previous is dock:
            return
        if isinstance(previous, QDockWidget):
            previous.setProperty("hvacPanelFocus", "")
            self._refresh_dock_focus_style_v1(previous)

        self._active_focus_dock_v1 = dock
        dock.setProperty("hvacPanelFocus", "active")
        self._refresh_dock_focus_style_v1(dock)

    # ------------------------------------------------------------------
    # ESC handling
    # ------------------------------------------------------------------
    def _update_education_from_event_object_v1(self, obj) -> None:
        current = obj
        for _depth in range(32):
            if current is None:
                return
            if isinstance(current, QDockWidget):
                topic = education_topic_for_dock_id_v1(
                    str(current.objectName() or "")
                )
                if topic:
                    education = getattr(
                        self, "_education_panel_adapter", None
                    )
                    if education is not None:
                        education.set_topic(
                            domain="workspace",
                            topic=topic,
                        )
                return
            try:
                current = current.parent()
            except (AttributeError, RuntimeError):
                return

    def eventFilter(self, obj, event) -> bool:
        if event.type() in (
            QEvent.FocusIn,
            QEvent.MouseButtonPress,
            QEvent.WindowActivate,
        ):
            self._update_active_dock_focus_v1(obj)
        if event.type() in (
            QEvent.FocusIn,
            QEvent.MouseButtonPress,
            QEvent.WindowActivate,
        ):
            self._update_education_from_event_object_v1(obj)
        if redirect_unsafe_input_wheel_event_v1(obj, event):
            return True
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if getattr(self._context, "hlpe_active", False):
                if hasattr(self._context, "exit_hlpe"):
                    self._context.exit_hlpe()
                return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # H-S69-B3C — GUI-only appearance
    # ------------------------------------------------------------------
    def _apply_appearance_scheme_v1(
            self,
            scheme: str,
            *,
            persist: bool = True,
    ) -> None:
        if not self._gui_settings.set_appearance_scheme_v1(scheme):
            return
        stable_scheme = self._gui_settings.appearance_scheme_v1()
        app = QApplication.instance()
        if app is not None:
            app.setPalette(application_palette_v1(stable_scheme))
            app.setStyleSheet(application_stylesheet_v1(stable_scheme))
        action = getattr(
            self, "_appearance_actions_v1", {}
        ).get(stable_scheme)
        if action is not None:
            action.setChecked(True)
        if persist:
            self._gui_settings.save()

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

        self._hydronic_control_panel = self._register_panel(
            "hydronic_control",
            HydronicControlPanel(self),
        )

        self._basic_hydronics_panel = self._register_panel(
            "basic_hydronics",
            BasicHydronicsPanel(self),
        )
        self._local_k_panel = self._register_panel(
            "local_k",
            LocalKPanel(self),
        )
        self._topology_arranger_panel = self._register_panel(
            "topology_arranger",
            TopologyArrangerPanel(),
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
        self._dock_local_k = self._mk_dock(
            "Local K / Fittings",
            "dock_local_k",
            self._local_k_panel,
        )
        self._dock_topology_arranger = self._mk_dock(
            "Topology Arranger",
            "dock_topology_arranger",
            self._topology_arranger_panel,
        )
        self._dock_hydronic_control = self._mk_dock(
            "Hydronic Emitters",
            "dock_hydronic_control",
            self._hydronic_control_panel,
        )
        self._dock_basic_hydronics = self._mk_dock(
            "Basic Hydronics",
            "dock_basic_hydronics",
            self._basic_hydronics_panel,
        )
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
                self._dock_hydronic_control,
                self._dock_basic_hydronics,
                self._dock_local_k,
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

        self.tabifyDockWidget(self._dock_hydronics, self._dock_geometry)
        self.tabifyDockWidget(self._dock_hydronics, self._dock_ach)
        self.tabifyDockWidget(self._dock_hydronics, self._dock_hydronic_control)
        self.tabifyDockWidget(self._dock_hydronics, self._dock_basic_hydronics)
        self.tabifyDockWidget(self._dock_basic_hydronics, self._dock_local_k)
        self.tabifyDockWidget(
            self._dock_hydronics,
            self._dock_topology_arranger,
        )
        self.tabifyDockWidget(self._dock_hydronics, self._dock_dev)
        self.tabifyDockWidget(self._dock_hydronics, self._dock_geometry)
        self.tabifyDockWidget(self._dock_hydronics, self._dock_ach)

        # Show DEV tab initially while debugging
        self._dock_dev.show()
        self._dock_dev.raise_()

        # Adapters
        self._project_panel_adapter = ProjectPanelAdapter(
            panel=self._project_panel,
            context=self._context,
        )
        self._environment_panel_adapter = EnvironmentPanelAdapter(self._context, self._environment_panel)
        self._room_tree_panel_adapter = RoomTreePanelAdapter(panel=self._room_tree_panel, context=self._context)
        self._readiness_adapter = ProjectHeatLossReadinessAdapter(panel=self._heat_loss_panel, context=self._context)
        self._education_panel_adapter = EducationPanelAdapter(
            panel=self._education_panel,
            domain="workspace",
            topic="heat_loss",
            mode="standard",
        )
        self._hydronic_control_adapter = HydronicControlPanelAdapter(
            panel=self._hydronic_control_panel,
            project_state=self._context.project_state,
            context=self._context,
            refresh_all=self._refresh_all_adapters,
        )

        self._basic_hydronics_adapter = BasicHydronicsPanelAdapter(
            panel=self._basic_hydronics_panel,
            context=self._context,
        )
        self._local_k_adapter = LocalKPanelAdapter(
            panel=self._local_k_panel,
            context=self._context,
        )

        if hasattr(self._context, "pass_to_proportioning_requested"):
            self._context.pass_to_proportioning_requested.connect(
                self._on_pass_to_proportioning_requested
            )
        self._topology_arranger_adapter = TopologyArrangerPanelAdapter(
            panel=self._topology_arranger_panel,
            context=self._context,
        )
        self._hydronics_adapter = HydronicsSchematicPanelAdapter(
            panel=self._hydronics_panel,
            project_state=self._context.project_state,
            context=self._context,
        )
        self._geometry_adapter = GeometryMiniPanelAdapter(
            panel=self._geometry_mini_panel,
            context=self._context,
            refresh_all_callback=self._refresh_all_adapters,
        )
        self._heat_loss_panel_adapter = HeatLossPanelAdapter(
            panel=self._heat_loss_panel,
            context=self._context,
            refresh_all_callback=self._refresh_all_adapters,
        )

        self._construction_panel_adapter = ConstructionPanelAdapter(
            panel=self._construction_panel,
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

        self.wall_wizard_adapter = WallWizardAdapter(
            context=self._context,
            parent=self,
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

    def _run_heatloss_for_current_project(self) -> None:
        """
        Shared project-level heat-loss execution path.

        Delegates to HeatLossPanelAdapter so Project → Run Heat-Loss and
        the Heat-Loss panel button use the same calculation path.
        """
        adapter = getattr(self, "_heat_loss_panel_adapter", None)
        if adapter is None:
            return

        adapter.run_heatloss()

    def _run_heatloss_project_action(self) -> None:
        """
        Project-level Run Heat-Loss action.

        This must not depend on the Heat-Loss panel being visible.
        It reuses the same calculation path as the Heat-Loss worksheet button.
        """
        ps = self._context.project_state
        if ps is None:
            return

        self._run_heatloss_for_current_project()

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
        # Create stable new room ID
        # --------------------------------------------------
        idx = len(ps.rooms) + 1
        room_id = f"room-{idx:03d}"

        while room_id in ps.rooms:
            idx += 1
            room_id = f"room-{idx:03d}"

        # --------------------------------------------------
        # Create room
        # --------------------------------------------------
        from HVAC.core.room_state import RoomStateV1
        from HVAC.core.room_geometry import RoomGeometryV1

        ps.rooms[room_id] = RoomStateV1(
            room_id=room_id,
            name=f"Room {idx}",
            storey_index=0,
            storey_label="Ground Floor",
            geometry=RoomGeometryV1(
                length_m=4.0,
                width_m=3.0,
                height_m=2.4,
                external_wall_length_m=14.0,
            ),
        )

        # --------------------------------------------------
        # Ensure new room has default topology
        # --------------------------------------------------
        from HVAC.topology.topology_resolver_v1 import TopologyResolverV1

        TopologyResolverV1.ensure_room_topology(ps, room_id)

        # --------------------------------------------------
        # Mark dirty
        # --------------------------------------------------
        ps.mark_heatloss_dirty()

        # --------------------------------------------------
        # Notify + select new room
        # --------------------------------------------------
        self._context.notify_project_changed()
        self._context.set_current_room(room_id)

    # ------------------------------------------------------------------
    # Overlay triggers
    # ------------------------------------------------------------------
    def _build_menu(self) -> None:
        menubar = self.menuBar()
        # H-S69-B3H — the duplicate top-level Project menu was removed.
        # Project files remain under File; Heat-Loss runs from Calculate.

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
        # View Menu — H-S69-B3B
        # ---------------------------
        view_menu = menubar.addMenu("View")

        appearance_menu = view_menu.addMenu("Appearance")
        self._appearance_action_group_v1 = QActionGroup(self)
        self._appearance_action_group_v1.setExclusive(True)
        self._appearance_actions_v1: dict[str, QAction] = {}
        for scheme, label in (("light", "Light"), ("dark", "Dark")):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda _checked=False, selected=scheme: (
                    self._apply_appearance_scheme_v1(selected)
                )
            )
            self._appearance_action_group_v1.addAction(action)
            self._appearance_actions_v1[scheme] = action
            appearance_menu.addAction(action)

        view_menu.addSeparator()
        main_views_menu = view_menu.addMenu("Main Window Views")
        docked_view_actions = (
            ("Heat Loss", self._apply_heat_loss_view_v1),
            ("Building Edit", self._apply_building_edit_view_v1),
            ("Openings", self._apply_openings_view_v1),
            ("Hydronics Setup", self._apply_hydronics_setup_view_v1),
            ("Basic Sizing", self._apply_basic_sizing_view_v1),
            ("Proportioning", self._apply_proportioning_view_v1),
            ("Results", self._apply_hydronics_results_view_v1),
        )
        for label, handler in docked_view_actions:
            action = QAction(label, self)
            action.triggered.connect(handler)
            main_views_menu.addAction(action)

        # H-S69-B3F — editable membership; factory docking stays authoritative.
        main_views_menu.addSeparator()
        choose_current_main_view_panels_action = QAction(
            "Choose Current View Panels…", self
        )
        choose_current_main_view_panels_action.triggered.connect(
            self._choose_current_docked_view_panels_v1
        )
        main_views_menu.addAction(choose_current_main_view_panels_action)

        reset_current_main_view_panels_action = QAction(
            "Reset Current View Panels", self
        )
        reset_current_main_view_panels_action.triggered.connect(
            self._reset_current_docked_view_panels_v1
        )
        main_views_menu.addAction(reset_current_main_view_panels_action)

        exploded_views_menu = view_menu.addMenu("Exploded Views")
        exploded_view_actions = (
            ("Heat Loss", self._apply_heat_loss_exploded_view_v1),
            ("Building Edit", self._apply_building_edit_exploded_view_v1),
            ("Openings", self._apply_openings_exploded_view_v1),
            ("Hydronics Setup", self._apply_hydronics_setup_exploded_view_v1),
            ("Basic Sizing", self._apply_basic_sizing_exploded_view_v1),
            ("Proportioning", self._apply_proportioning_exploded_view_v1),
            ("Results", self._apply_hydronics_results_exploded_view_v1),
        )
        for label, handler in exploded_view_actions:
            action = QAction(label, self)
            action.triggered.connect(handler)
            exploded_views_menu.addAction(action)

        # H-S69-B3E/B3E1 — edit and explicitly save the active view.
        exploded_views_menu.addSeparator()
        save_current_view_action = QAction("Save Current View", self)
        save_current_view_action.triggered.connect(
            self._save_current_exploded_view_v1
        )
        exploded_views_menu.addAction(save_current_view_action)

        choose_current_view_panels_action = QAction(
            "Choose Current View Panels…", self
        )
        choose_current_view_panels_action.triggered.connect(
            self._choose_current_exploded_view_panels_v1
        )
        exploded_views_menu.addAction(choose_current_view_panels_action)

        reset_current_view_panels_action = QAction(
            "Reset Current View Panels", self
        )
        reset_current_view_panels_action.triggered.connect(
            self._reset_current_exploded_view_panels_v1
        )
        exploded_views_menu.addAction(reset_current_view_panels_action)

        # H-S69-B3D — one user-selected safe exploded setout.
        view_menu.addSeparator()
        self._user_workspace_action_v1 = QAction("User Workspace", self)
        self._user_workspace_action_v1.setCheckable(True)
        self._user_workspace_action_v1.setEnabled(
            self._gui_settings.named_workspace_layout_v1(
                "user:exploded"
            ) is not None
        )
        self._user_workspace_action_v1.triggered.connect(
            self._apply_user_workspace_v1
        )
        view_menu.addAction(self._user_workspace_action_v1)

        choose_user_workspace_action = QAction(
            "Choose User Workspace Panels…", self
        )
        choose_user_workspace_action.triggered.connect(
            self._choose_user_workspace_panels_v1
        )
        view_menu.addAction(choose_user_workspace_action)

        view_menu.addSeparator()
        project_panels_menu = view_menu.addMenu("Project & Heat-Loss Panels")
        for dock in (
            self._dock_project,
            self._dock_environment,
            self._dock_rooms,
            self._dock_construction,
            self._dock_uvp,
            self._dock_heat_loss,
            self._dock_education,
            self._dock_geometry,
            self._dock_ach,
        ):
            project_panels_menu.addAction(dock.toggleViewAction())

        hydronics_panels_menu = view_menu.addMenu("Hydronics Panels")
        for dock in (
            self._dock_hydronics,
            self._dock_hydronic_control,
            self._dock_basic_hydronics,
            self._dock_local_k,
            self._dock_topology_arranger,
        ):
            hydronics_panels_menu.addAction(dock.toggleViewAction())

        utility_panels_menu = view_menu.addMenu("Utility Panels")
        utility_panels_menu.addAction(self._dock_dev.toggleViewAction())

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

        _ensure_construction(ps, "DEV-EXT-WALL", "External Wall", 0.26)
        _ensure_construction(ps, "DEV-ROOF", "Roof / Ceiling", 0.16)
        _ensure_construction(ps, "DEV-WINDOW", "Window / Door", 1.60)
        _ensure_construction(ps, "DEV-INT-WALL", "Internal Wall", 1.50)
        _ensure_construction(ps, "DEV-FLOOR", "Floor", 0.18)


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

        QMessageBox.information(
            self,
            "Project Saved",
            f"Saved project to:\n{project.project_dir / 'project.json'}",
        )

    def _save_project_as(self) -> None:
        """Save into the final project folder selected by the user."""

        hvac_root = Path(__file__).resolve().parents[1]
        default_dir = hvac_root / "HVACprojects"

        directory = QFileDialog.getExistingDirectory(
            self,
            "Choose or create project folder",
            str(default_dir),
        )
        if not directory:
            return

        project_dir = Path(directory).resolve()
        project = self._context.project_state

        project.project_dir = project_dir
        project.name = project_dir.name

        save_project(project, project_dir)
        self._project_panel_adapter.refresh()

        QMessageBox.information(
            self,
            "Project Saved As",
            f"Saved project as:\n{project_dir / 'project.json'}",
        )

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

    def _on_construction_focus_changed(self, cid: str) -> None:
        """
        GUI shell response to construction focus.

        Rules
        -----
        • Does not mutate ProjectState
        • Does not calculate
        • Shows/raises the Construction dock
        • Content update remains owned by construction/UVP adapters
        """

        dock = self._docks.get("dock_construction")
        if dock is None:
            return

        dock.show()
        dock.raise_()
        dock.setFocus()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _on_uvp_focus_requested(self, surface_id: str | None) -> None:
        self._dock_uvp.show()
        self._dock_uvp.raise_()
        self._uvp_panel.set_selected_surface(surface_id)
        self._context.set_uvp_focus(surface_id)

    def current_index_room_id(self) -> str:
        return str(self._index_room.currentData() or "")

    def current_index_emitter_id(self) -> str:
        return str(self._index_emitter.currentData() or "")

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
    def _refresh_all_adapters(self) -> None:

        if hasattr(self, "_project_panel_adapter"):
            self._project_panel_adapter.refresh()

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

        if hasattr(self, "_hydronic_control_adapter"):
            self._hydronic_control_adapter.set_project_state(
                self._context.project_state
            )
            self._hydronic_control_adapter.refresh()

        if hasattr(self, "_hydronics_adapter"):
            self._hydronics_adapter.set_project_state(
                self._context.project_state
            )
            self._hydronics_adapter.refresh()

        if hasattr(self, "_basic_hydronics_adapter"):
            self._basic_hydronics_adapter.refresh()

        if hasattr(self, "_local_k_adapter"):
            self._local_k_adapter.refresh()

        if hasattr(self, "_hydronic_control_adapter"):
            self._hydronic_control_adapter.refresh()

    # ------------------------------------------------------------------
    # H-S69-B1/B3B — navigation-only workspace presets
    # ------------------------------------------------------------------
    def _workspace_docks_v1(
            self,
            view_id: str,
    ) -> tuple[QDockWidget, ...]:
        views = {
            "heat_loss": (
                self._dock_heat_loss,
                self._dock_environment,
                self._dock_rooms,
                self._dock_geometry,
                self._dock_ach,
            ),
            "building_edit": (
                self._dock_uvp,
                self._dock_construction,
                self._dock_rooms,
                self._dock_geometry,
            ),
            "openings": (
                self._dock_uvp,
                self._dock_heat_loss,
                self._dock_rooms,
                self._dock_construction,
            ),
            "hydronics_setup": (
                self._dock_topology_arranger,
                self._dock_environment,
                self._dock_hydronic_control,
                self._dock_rooms,
            ),
            "basic_sizing": (
                self._dock_basic_hydronics,
                self._dock_local_k,
                self._dock_rooms,
            ),
            "proportioning": (
                self._dock_hydronics,
                self._dock_local_k,
            ),
            "results": (
                self._dock_hydronics,
                self._dock_project,
                self._dock_rooms,
            ),
        }
        try:
            return views[str(view_id)]
        except KeyError as exc:
            raise ValueError(f"Unknown workspace view: {view_id!r}") from exc

    def _set_user_workspace_checked_v1(self, checked: bool) -> None:
        action = getattr(self, "_user_workspace_action_v1", None)
        if action is not None:
            action.setChecked(bool(checked))

    def _choose_workspace_panels_v1(
            self,
            *,
            title: str,
            selected_ids: set[str],
    ) -> tuple[QDockWidget, ...] | None:
        """Return a checked dock set without showing or resizing any panel."""
        docks = tuple(sorted(
            (
                dock
                for dock in self.findChildren(QDockWidget)
                if str(dock.objectName() or "")
            ),
            key=lambda dock: str(dock.windowTitle() or "").casefold(),
        ))
        if not docks:
            return None

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(460)
        layout = QGridLayout(dialog)
        layout.addWidget(
            QLabel("Select the panels for this workspace."),
            0, 0, 1, 2,
        )

        choices: list[tuple[QCheckBox, QDockWidget]] = []
        for index, dock in enumerate(docks):
            dock_id = str(dock.objectName() or "")
            checkbox = QCheckBox(str(dock.windowTitle() or dock_id))
            checkbox.setChecked(dock_id in selected_ids)
            layout.addWidget(checkbox, 1 + index // 2, index % 2)
            choices.append((checkbox, dock))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        apply_button = buttons.button(
            QDialogButtonBox.StandardButton.Ok
        )
        if apply_button is not None:
            apply_button.setText("Apply")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons, 2 + (len(docks) - 1) // 2, 0, 1, 2)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        selected_docks = tuple(
            dock for checkbox, dock in choices if checkbox.isChecked()
        )
        if not selected_docks:
            QMessageBox.information(
                self,
                title,
                "Select at least one panel.",
            )
            return None
        return selected_docks

    def _choose_user_workspace_panels_v1(self) -> None:
        stored = (
            self._gui_settings.named_workspace_layout_v1(
                "user:exploded"
            )
            or {}
        )
        selected_docks = self._choose_workspace_panels_v1(
            title="User Workspace",
            selected_ids=set((stored.get("docks") or {}).keys()),
        )
        if selected_docks is not None:
            self._create_user_workspace_v1(selected_docks)

    def _create_user_workspace_v1(
            self,
            docks: tuple[QDockWidget, ...],
    ) -> None:
        """Create a bounded initial setout, then use normal remembered geometry."""
        self._save_active_exploded_workspace_layout_v1()
        screens = self._qt_workspace_screens_v1()
        saved_docks: dict[str, dict] = {}
        for index, dock in enumerate(docks):
            dock_id = str(dock.objectName() or "")
            if not dock_id:
                continue
            resolved = resolve_user_workspace_dock_geometry_v1(
                screens=screens,
                dock_index=index,
                dock_count=len(docks),
            )
            if resolved is None:
                continue
            saved_docks[dock_id] = {
                "x": resolved.x,
                "y": resolved.y,
                "width": resolved.width,
                "height": resolved.height,
                "screen_name": resolved.screen_name,
            }

        if not saved_docks:
            return
        if not self._gui_settings.set_named_workspace_layout_v1(
            "user:exploded",
            {"docks": saved_docks},
        ):
            return

        action = getattr(self, "_user_workspace_action_v1", None)
        if action is not None:
            action.setEnabled(True)
        self._apply_user_workspace_v1()

    def _active_factory_docked_view_id_v1(self) -> str:
        view_id = str(
            getattr(self, "_active_docked_workspace_view_id_v1", "")
            or ""
        )
        if not view_id:
            return ""
        try:
            self._workspace_docks_v1(view_id)
        except ValueError:
            return ""
        return view_id

    def _apply_factory_docked_view_by_id_v1(self, view_id: str) -> None:
        handlers = {
            "heat_loss": self._apply_heat_loss_view_v1,
            "building_edit": self._apply_building_edit_view_v1,
            "openings": self._apply_openings_view_v1,
            "hydronics_setup": self._apply_hydronics_setup_view_v1,
            "basic_sizing": self._apply_basic_sizing_view_v1,
            "proportioning": self._apply_proportioning_view_v1,
            "results": self._apply_hydronics_results_view_v1,
        }
        handler = handlers.get(str(view_id or ""))
        if handler is not None:
            handler()

    def _choose_current_docked_view_panels_v1(self) -> None:
        view_id = self._active_factory_docked_view_id_v1()
        if not view_id:
            QMessageBox.information(
                self,
                "Main Window Views",
                "Open one of the seven Main Window Views first.",
            )
            return
        storage_id = f"{view_id}:docked"
        factory_docks = self._workspace_docks_v1(view_id)
        stored_ids = self._gui_settings.workspace_panel_set_v1(storage_id)
        selected_ids = (
            set(stored_ids)
            if stored_ids
            else {str(dock.objectName() or "") for dock in factory_docks}
        )
        selected_docks = self._choose_workspace_panels_v1(
            title="Main Window View Panels",
            selected_ids=selected_ids,
        )
        if selected_docks is None:
            return
        panel_ids = [str(dock.objectName() or "") for dock in selected_docks]
        if not self._gui_settings.set_workspace_panel_set_v1(
            storage_id, panel_ids
        ):
            return
        self._gui_settings.save()
        self._apply_factory_docked_view_by_id_v1(view_id)

    def _reset_current_docked_view_panels_v1(self) -> None:
        view_id = self._active_factory_docked_view_id_v1()
        if not view_id:
            QMessageBox.information(
                self,
                "Main Window Views",
                "Open one of the seven Main Window Views first.",
            )
            return
        self._gui_settings.clear_workspace_panel_set_v1(
            f"{view_id}:docked"
        )
        self._gui_settings.save()
        self._apply_factory_docked_view_by_id_v1(view_id)

    def _save_current_exploded_view_v1(self) -> None:
        """Explicitly persist the active user or factory exploded setout."""
        storage_id = str(
            getattr(self, "_active_exploded_workspace_view_id_v1", "")
            or ""
        )
        docks = tuple(
            getattr(self, "_active_exploded_workspace_docks_v1", ())
            or ()
        )
        if not storage_id.endswith(":exploded") or not docks:
            QMessageBox.information(
                self,
                "Exploded Views",
                "Open an Exploded View or User Workspace first.",
            )
            return
        self._save_active_exploded_workspace_layout_v1()

    def _active_factory_exploded_view_id_v1(self) -> str:
        storage_id = str(
            getattr(self, "_active_exploded_workspace_view_id_v1", "")
            or ""
        )
        suffix = ":exploded"
        if not storage_id.endswith(suffix):
            return ""
        view_id = storage_id[:-len(suffix)]
        if not view_id or view_id == "user":
            return ""
        try:
            self._workspace_docks_v1(view_id)
        except ValueError:
            return ""
        return view_id

    def _choose_current_exploded_view_panels_v1(self) -> None:
        view_id = self._active_factory_exploded_view_id_v1()
        if not view_id:
            QMessageBox.information(
                self,
                "Exploded Views",
                "Open one of the seven Exploded Views first.",
            )
            return

        storage_id = f"{view_id}:exploded"
        stored = self._gui_settings.named_workspace_layout_v1(storage_id) or {}
        factory_docks = self._workspace_docks_v1(view_id)
        panel_ids = tuple(stored.get("panel_ids") or ())
        selected_ids = (
            set(panel_ids)
            if panel_ids
            else {str(dock.objectName() or "") for dock in factory_docks}
        )
        selected_docks = self._choose_workspace_panels_v1(
            title="Exploded View Panels",
            selected_ids=selected_ids,
        )
        if selected_docks is None:
            return

        self._save_active_exploded_workspace_layout_v1()
        stored = self._gui_settings.named_workspace_layout_v1(storage_id) or {}
        saved_docks = dict(stored.get("docks") or {})
        selected_panel_ids = [
            str(dock.objectName() or "") for dock in selected_docks
        ]
        if not self._gui_settings.set_named_workspace_layout_v1(
            storage_id,
            {
                "docks": saved_docks,
                "panel_ids": selected_panel_ids,
            },
        ):
            return
        self._apply_exploded_workspace_view_v1(view_id, factory_docks)

    def _reset_current_exploded_view_panels_v1(self) -> None:
        view_id = self._active_factory_exploded_view_id_v1()
        if not view_id:
            QMessageBox.information(
                self,
                "Exploded Views",
                "Open one of the seven Exploded Views first.",
            )
            return

        storage_id = f"{view_id}:exploded"
        factory_docks = self._workspace_docks_v1(view_id)
        self._save_active_exploded_workspace_layout_v1()
        stored = self._gui_settings.named_workspace_layout_v1(storage_id) or {}
        saved_docks = dict(stored.get("docks") or {})
        if not self._gui_settings.set_named_workspace_layout_v1(
            storage_id,
            {"docks": saved_docks},
        ):
            return
        self._apply_exploded_workspace_view_v1(view_id, factory_docks)

    def _apply_user_workspace_v1(self, _checked: bool = False) -> None:
        stored = (
            self._gui_settings.named_workspace_layout_v1(
                "user:exploded"
            )
            or {}
        )
        stored_docks = dict(stored.get("docks") or {})
        docks_by_id = {
            str(dock.objectName() or ""): dock
            for dock in self.findChildren(QDockWidget)
            if str(dock.objectName() or "")
        }
        docks = tuple(
            docks_by_id[dock_id]
            for dock_id in stored_docks
            if dock_id in docks_by_id
        )
        if not docks:
            self._set_user_workspace_checked_v1(False)
            return
        self._apply_exploded_workspace_view_v1("user", docks)

    def _save_active_exploded_workspace_layout_v1(self) -> None:
        view_id = str(
            getattr(self, "_active_exploded_workspace_view_id_v1", "") or ""
        )
        docks = tuple(
            getattr(self, "_active_exploded_workspace_docks_v1", ()) or ()
        )
        if not view_id or not docks:
            return

        existing = self._gui_settings.named_workspace_layout_v1(view_id) or {}
        saved_docks = dict(existing.get("docks") or {})
        temporarily_clamped = set(
            getattr(self, "_temporarily_clamped_workspace_docks_v1", set())
            or set()
        )
        for dock in docks:
            dock_id = str(dock.objectName() or "")
            if not dock_id:
                continue
            # If a remembered monitor is temporarily absent, retain its
            # original placement rather than overwriting it with fallback.
            if dock_id in temporarily_clamped and dock_id in saved_docks:
                continue
            geometry = dock.geometry()
            screen = dock.screen()
            saved_docks[dock_id] = {
                "x": int(geometry.x()),
                "y": int(geometry.y()),
                "width": int(geometry.width()),
                "height": int(geometry.height()),
                "screen_name": str(screen.name() if screen else ""),
            }
        if saved_docks:
            layout = {"docks": saved_docks}
            panel_ids = tuple(existing.get("panel_ids") or ())
            if panel_ids:
                layout["panel_ids"] = list(panel_ids)
            self._gui_settings.set_named_workspace_layout_v1(
                view_id,
                layout,
            )
            self._gui_settings.save()

    def _finish_active_exploded_workspace_v1(self) -> None:
        docks = tuple(
            getattr(self, "_active_exploded_workspace_docks_v1", ()) or ()
        )
        self._save_active_exploded_workspace_layout_v1()
        for dock in docks:
            dock.hide()
            if dock.isFloating():
                dock.setFloating(False)
        self._active_exploded_workspace_view_id_v1 = ""
        self._active_exploded_workspace_docks_v1 = ()
        self._temporarily_clamped_workspace_docks_v1 = set()

    @staticmethod
    def _workspace_window_title_v1(view_id: str, mode: str) -> str:
        labels = {
            "heat_loss": "Heat-Loss",
            "building_edit": "Building Edit",
            "openings": "Openings",
            "hydronics_setup": "Hydronics Setup",
            "basic_sizing": "Basic Sizing",
            "proportioning": "Proportioning",
            "results": "Proportioned Results",
            "user": "User Workspace",
        }
        view_label = labels.get(str(view_id or ""), "Workspace")
        if view_id == "user":
            mode_label = "Floating"
        elif mode == "exploded":
            mode_label = "Exploded"
        else:
            mode_label = "Main Window"
        return f"HVACgooee — {view_label} — {mode_label}"

    def _set_workspace_window_title_v1(
            self,
            view_id: str,
            mode: str,
    ) -> None:
        self.setWindowTitle(
            self._workspace_window_title_v1(view_id, mode)
        )
        education = getattr(self, "_education_panel_adapter", None)
        if education is not None:
            education.set_topic(domain="workspace", topic=view_id)

    def _prepare_hydronics_workspace_view_v1(
            self,
            view_id: str,
            visible_docks: tuple[QDockWidget, ...],
    ) -> None:
        """Reset only dock presentation for one user-selected view."""
        self._finish_active_exploded_workspace_v1()
        self._set_user_workspace_checked_v1(False)
        previous_docks = tuple(
            getattr(self, "_active_docked_workspace_docks_v1", ()) or ()
        )
        for dock in previous_docks:
            dock.hide()
            if dock.isFloating():
                dock.setFloating(False)
            self.removeDockWidget(dock)
        self._active_docked_workspace_docks_v1 = ()
        self._active_docked_workspace_view_id_v1 = str(view_id)
        self._set_workspace_window_title_v1(view_id, "docked")
        self._gui_settings.set_last_workspace_presentation_v1(
            view_id, "docked"
        )
        self._gui_settings.save()
        self.showMaximized()
        self.setDockNestingEnabled(True)

        central_widget = self.centralWidget()
        if central_widget is not None:
            central_widget.hide()

        for dock in self.findChildren(QDockWidget):
            dock.hide()

        for dock in visible_docks:
            dock.setFloating(False)
            self.removeDockWidget(dock)

    def _show_hydronics_workspace_docks_v1(
            self,
            docks: tuple[QDockWidget, ...],
    ) -> None:
        view_id = str(
            getattr(self, "_active_docked_workspace_view_id_v1", "")
            or ""
        )
        stored_ids = self._gui_settings.workspace_panel_set_v1(
            f"{view_id}:docked"
        )
        visible_docks = tuple(docks)
        if stored_ids:
            docks_by_id = {
                str(dock.objectName() or ""): dock
                for dock in self.findChildren(QDockWidget)
                if str(dock.objectName() or "")
            }
            override_docks = tuple(
                docks_by_id[panel_id]
                for panel_id in stored_ids
                if panel_id in docks_by_id
            )
            if override_docks:
                visible_docks = override_docks

        factory_docks = set(docks)
        anchor = next((
            dock
            for dock in visible_docks
            if dock in factory_docks
            and self.dockWidgetArea(dock) == Qt.RightDockWidgetArea
        ), None)
        for dock in visible_docks:
            if dock not in factory_docks:
                dock.hide()
                if dock.isFloating():
                    dock.setFloating(False)
                self.removeDockWidget(dock)
                self.addDockWidget(Qt.RightDockWidgetArea, dock)
                if anchor is not None:
                    self.tabifyDockWidget(anchor, dock)
                else:
                    anchor = dock
            dock.show()
        self._active_docked_workspace_docks_v1 = visible_docks

    def _qt_workspace_screens_v1(self) -> tuple[WorkspaceScreenGeometryV1, ...]:
        app = QApplication.instance()
        screens = list(app.screens()) if app is not None else []
        primary = app.primaryScreen() if app is not None else None
        if primary in screens:
            screens.remove(primary)
            screens.insert(0, primary)
        result: list[WorkspaceScreenGeometryV1] = []
        for screen in screens:
            available = screen.availableGeometry()
            result.append(WorkspaceScreenGeometryV1(
                name=str(screen.name() or ""),
                x=int(available.x()),
                y=int(available.y()),
                width=int(available.width()),
                height=int(available.height()),
            ))
        return tuple(result)

    def _apply_exploded_workspace_view_v1(
            self,
            view_id: str,
            docks: tuple[QDockWidget, ...],
    ) -> None:
        self._finish_active_exploded_workspace_v1()
        self._active_docked_workspace_view_id_v1 = ""
        self._active_docked_workspace_docks_v1 = ()
        self._set_workspace_window_title_v1(view_id, "exploded")
        self._set_user_workspace_checked_v1(view_id == "user")
        self.showNormal()
        central_widget = self.centralWidget()
        if central_widget is not None:
            central_widget.hide()
        for dock in self.findChildren(QDockWidget):
            dock.hide()

        storage_id = f"{view_id}:exploded"
        stored = self._gui_settings.named_workspace_layout_v1(storage_id) or {}
        stored_docks = dict(stored.get("docks") or {})
        panel_ids = tuple(stored.get("panel_ids") or ())
        if view_id != "user" and panel_ids:
            docks_by_id = {
                str(dock.objectName() or ""): dock
                for dock in self.findChildren(QDockWidget)
                if str(dock.objectName() or "")
            }
            override_docks = tuple(
                docks_by_id[panel_id]
                for panel_id in panel_ids
                if panel_id in docks_by_id
            )
            if override_docks:
                docks = override_docks
        screens = self._qt_workspace_screens_v1()
        clamped: set[str] = set()

        for index, dock in enumerate(docks):
            dock_id = str(dock.objectName() or "")
            saved_geometry = stored_docks.get(dock_id)
            resolved = resolve_exploded_dock_geometry_v1(
                saved_geometry=saved_geometry,
                screens=screens,
                dock_index=index,
                dock_count=len(docks),
            )
            target_geometry = None
            if resolved is not None:
                target_geometry = (
                    resolved.x,
                    resolved.y,
                    resolved.width,
                    resolved.height,
                )
                if resolved.used_fallback_screen:
                    clamped.add(dock_id)

            # Some Linux window managers replace a floating dock's requested
            # rectangle while its native window is first being shown. Apply
            # the validated rectangle after show(), then once more when Qt
            # returns to the event loop.
            dock.setFloating(True)
            dock.show()
            if target_geometry is not None:
                dock.setGeometry(*target_geometry)
                QTimer.singleShot(
                    0,
                    lambda dock=dock, geometry=target_geometry: (
                        dock.setGeometry(*geometry)
                    ),
                )
            dock.raise_()

        self._active_exploded_workspace_view_id_v1 = storage_id
        self._active_exploded_workspace_docks_v1 = tuple(docks)
        self._temporarily_clamped_workspace_docks_v1 = clamped
        self._gui_settings.set_last_workspace_presentation_v1(
            view_id, "exploded"
        )
        self._gui_settings.save()
        # With every working panel floating, retain a compact menu
        # shell rather than a maximised or full-height empty window.
        self.resize(360, 96)
        QTimer.singleShot(0, lambda: self.resize(360, 96))

    def _apply_heat_loss_view_v1(self) -> None:
        docks = self._workspace_docks_v1("heat_loss")
        self._prepare_hydronics_workspace_view_v1(
            "heat_loss", docks
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_heat_loss)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_environment)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_rooms)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_geometry)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_ach)
        self.splitDockWidget(self._dock_environment, self._dock_rooms, Qt.Vertical)
        self.tabifyDockWidget(self._dock_rooms, self._dock_geometry)
        self.tabifyDockWidget(self._dock_rooms, self._dock_ach)
        self._show_hydronics_workspace_docks_v1(docks)
        self._dock_rooms.raise_()
        self._dock_heat_loss.raise_()
        self.resizeDocks(
            [self._dock_heat_loss, self._dock_environment],
            [1200, 480],
            Qt.Horizontal,
        )

    def _apply_building_edit_view_v1(self) -> None:
        docks = self._workspace_docks_v1("building_edit")
        self._prepare_hydronics_workspace_view_v1(
            "building_edit", docks
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_uvp)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_construction)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_rooms)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_geometry)
        self.splitDockWidget(self._dock_construction, self._dock_rooms, Qt.Vertical)
        self.tabifyDockWidget(self._dock_rooms, self._dock_geometry)
        self._show_hydronics_workspace_docks_v1(docks)
        self._dock_rooms.raise_()
        self._dock_uvp.raise_()
        self.resizeDocks(
            [self._dock_uvp, self._dock_construction],
            [1200, 480],
            Qt.Horizontal,
        )

    def _apply_openings_view_v1(self) -> None:
        docks = self._workspace_docks_v1("openings")
        self._prepare_hydronics_workspace_view_v1(
            "openings", docks
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_uvp)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_construction)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_heat_loss)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_rooms)
        self.tabifyDockWidget(self._dock_uvp, self._dock_construction)
        self.tabifyDockWidget(self._dock_heat_loss, self._dock_rooms)
        self._show_hydronics_workspace_docks_v1(docks)
        self._dock_uvp.raise_()
        self._dock_heat_loss.raise_()
        self.resizeDocks(
            [self._dock_uvp, self._dock_heat_loss],
            [1050, 600],
            Qt.Horizontal,
        )

    def _apply_hydronics_setup_view_v1(self) -> None:
        docks = (
            self._dock_environment,
            self._dock_topology_arranger,
            self._dock_rooms,
            self._dock_hydronic_control,
        )
        self._prepare_hydronics_workspace_view_v1(
            "hydronics_setup", docks
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_environment)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_hydronic_control)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_rooms)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_topology_arranger)
        self.splitDockWidget(
            self._dock_environment,
            self._dock_hydronic_control,
            Qt.Vertical,
        )
        self.tabifyDockWidget(self._dock_hydronic_control, self._dock_rooms)
        self._show_hydronics_workspace_docks_v1(docks)
        self._dock_hydronic_control.raise_()
        self._dock_topology_arranger.raise_()
        self.resizeDocks(
            [self._dock_environment, self._dock_topology_arranger],
            [420, 1200],
            Qt.Horizontal,
        )

    def _apply_basic_sizing_view_v1(self) -> None:
        docks = (
            self._dock_basic_hydronics,
            self._dock_local_k,
            self._dock_rooms,
        )
        self._prepare_hydronics_workspace_view_v1(
            "basic_sizing", docks
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_basic_hydronics)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_local_k)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_rooms)
        self.tabifyDockWidget(self._dock_local_k, self._dock_rooms)
        self._show_hydronics_workspace_docks_v1(docks)
        self._dock_local_k.raise_()
        self._dock_basic_hydronics.raise_()
        self.resizeDocks(
            [self._dock_basic_hydronics, self._dock_local_k],
            [1100, 500],
            Qt.Horizontal,
        )

    def _apply_proportioning_view_v1(self) -> None:
        docks = (self._dock_hydronics, self._dock_local_k)
        self._prepare_hydronics_workspace_view_v1(
            "proportioning", docks
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_hydronics)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_local_k)
        self._show_hydronics_workspace_docks_v1(docks)
        self._hydronics_panel.select_proportioning_tab()
        self._dock_hydronics.raise_()
        self.resizeDocks(
            [self._dock_hydronics, self._dock_local_k],
            [1250, 400],
            Qt.Horizontal,
        )

    def _apply_hydronics_results_view_v1(self) -> None:
        docks = (
            self._dock_hydronics,
            self._dock_project,
            self._dock_rooms,
        )
        self._prepare_hydronics_workspace_view_v1(
            "results", docks
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_hydronics)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_project)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_rooms)
        self.tabifyDockWidget(self._dock_project, self._dock_rooms)
        self._show_hydronics_workspace_docks_v1(docks)
        self._hydronics_panel.select_proportioned_tab()
        self._dock_project.raise_()
        self._dock_hydronics.raise_()
        self.resizeDocks(
            [self._dock_hydronics, self._dock_project],
            [1250, 350],
            Qt.Horizontal,
        )

    def _apply_heat_loss_exploded_view_v1(self) -> None:
        self._apply_exploded_workspace_view_v1(
            "heat_loss", self._workspace_docks_v1("heat_loss")
        )

    def _apply_building_edit_exploded_view_v1(self) -> None:
        self._apply_exploded_workspace_view_v1(
            "building_edit", self._workspace_docks_v1("building_edit")
        )

    def _apply_openings_exploded_view_v1(self) -> None:
        self._apply_exploded_workspace_view_v1(
            "openings", self._workspace_docks_v1("openings")
        )

    def _apply_hydronics_setup_exploded_view_v1(self) -> None:
        self._apply_exploded_workspace_view_v1(
            "hydronics_setup", self._workspace_docks_v1("hydronics_setup")
        )

    def _apply_basic_sizing_exploded_view_v1(self) -> None:
        self._apply_exploded_workspace_view_v1(
            "basic_sizing", self._workspace_docks_v1("basic_sizing")
        )

    def _apply_proportioning_exploded_view_v1(self) -> None:
        self._hydronics_panel.select_proportioning_tab()
        self._apply_exploded_workspace_view_v1(
            "proportioning", self._workspace_docks_v1("proportioning")
        )

    def _apply_hydronics_results_exploded_view_v1(self) -> None:
        self._hydronics_panel.select_proportioned_tab()
        self._apply_exploded_workspace_view_v1(
            "results", self._workspace_docks_v1("results")
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _on_pass_to_proportioning_requested(self, payload: dict) -> None:
        """
        H-S8-L-C:
        Navigation-only handoff from Basic Hydronics to the read-only
        Hydronics Schematic > Proportioning view.

        This does not run proportioning, mutate topology, or perform
        second-pass pressure calculations.
        """
        if hasattr(self, "_dock_basic_hydronics"):
            self._dock_basic_hydronics.hide()

        if hasattr(self, "_dock_hydronics"):
            self._dock_hydronics.show()
            self._dock_hydronics.raise_()

        if hasattr(self, "_hydronics_panel"):
            panel = self._hydronics_panel

            if hasattr(panel, "select_proportioning_tab"):
                panel.select_proportioning_tab()

            panel.raise_()

    def _mk_dock(self, title: str, name: str, widget: QWidget) -> QDockWidget:
        if name in self._docks:
            raise RuntimeError(f"Dock already exists: {name}")

        d = QDockWidget(title, self)
        d.setObjectName(name)
        d.setProperty("hvacPanelFocus", "")
        category = panel_category_for_dock_id_v1(name)
        if category is not None:
            d.setProperty("hvacPanelCategory", category)
            widget.setProperty("hvacPanelCategory", category)
        d.setWidget(widget)

        self._docks[name] = d
        return d

    def _register_panel(self, key: str, panel: PanelT) -> PanelT:

        if key in self._panels:
            raise RuntimeError(f"Panel already exists: {key}")

        self._panels[key] = panel
        print(f"[PANEL REGISTERED] {key} -> {id(panel)}")
        return panel