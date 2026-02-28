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

# ----------------------------------------------------------------------
# GUI context (authority boundary)
# ----------------------------------------------------------------------
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext

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

        self._build_ui()
        self._wire_context_fanout()

        # Global ESC — SINGLE listener (LOCKED)
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

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

    # ------------------------------------------------------------------
    # Context fan-out
    # ------------------------------------------------------------------
    def _wire_context_fanout(self) -> None:
        if hasattr(self._context, "subscribe_room_selection_changed"):
            self._context.subscribe_room_selection_changed(
                self._on_room_selection_changed
            )

    def _on_room_selection_changed(self, room_id: str | None) -> None:
        if hasattr(self._heat_loss_panel, "set_room"):
            self._heat_loss_panel.set_room(room_id)
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

        for dock in (
            self._dock_project,
            self._dock_environment,
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
        self._project_panel_adapter = ProjectPanelAdapter(self._project_panel, self._context.project_state)
        self._environment_panel_adapter = EnvironmentPanelAdapter(self._environment_panel, self._context.project_state)
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
        self._geometry_mini_panel_adapter = GeometryMiniPanelAdapter(self._geometry_mini_panel, self._context)
        self._ach_mini_panel_adapter = ACHMiniPanelAdapter(
            panel=self._ach_mini_panel,
            context=self._context,
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
        controller = HeatLossControllerV4(
            project_state=self._context.project_state
        )

        ti_C = self._heat_loss_panel._ti_input.value()
        ach = self._heat_loss_panel._ach_input.value()

        print("RUN pressed")
        print("Ti_C =", ti_C)
        print("ACH =", ach)

        controller.run(
            internal_design_temp_C=ti_C,
            ach=ach,  # <-- pass it
        )

        self._refresh_all_adapters()
        self._heat_loss_panel.ach_changed.connect(
        self._on_ach_changed
        )
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
        # Heat-Loss worksheet
        if hasattr(self, "_heat_loss_worksheet_adapter"):
            self._heat_loss_worksheet_adapter.refresh()

        # Heat-Loss readiness
        if hasattr(self, "_project_heatloss_readiness_adapter"):
            self._project_heatloss_readiness_adapter.refresh()

        # Environment (if it has a refresh)
        if hasattr(self, "_environment_panel_adapter"):
            self._environment_panel_adapter.refresh()

        # Room readiness (if exists)
        if hasattr(self, "_room_readiness_adapter"):
            self._room_readiness_adapter.refresh()

        # Room tree
        if hasattr(self, "_room_tree_panel_adapter"):
            self._room_tree_panel_adapter.refresh()