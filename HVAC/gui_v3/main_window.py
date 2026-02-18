# ======================================================================
# HVACgooee — Main Window (GUI v3)
# Phase: GUI v3 — Observer
# Sub-Phase: Phase E/F + HLPE (Edit Overlay)
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QWidget,
    QMessageBox,
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
from HVAC.gui_v3.panels.heat_loss_edit_overlay_panel import HeatLossEditOverlayPanel
from HVAC.gui_v3.panels.education_panel import EducationPanel
from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel

# ----------------------------------------------------------------------
# Adapters (read-only)
# ----------------------------------------------------------------------
from HVAC.gui_v3.adapters.project_panel_adapter import ProjectPanelAdapter
from HVAC.gui_v3.adapters.environment_panel_adapter import EnvironmentPanelAdapter
from HVAC.gui_v3.adapters.room_tree_panel_adapter import RoomTreePanelAdapter
from HVAC.gui_v3.adapters.heat_loss_panel_adapter import HeatLossPanelAdapter
from HVAC.gui_v3.adapters.heat_loss_worksheet_adapter import HeatLossWorksheetAdapter
from HVAC.gui_v3.adapters.education_panel_adapter import EducationPanelAdapter
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.adapters.geometry_mini_panel_adapter import GeometryMiniPanelAdapter
from HVAC.gui_v3.adapters.ach_mini_panel_adapter import ACHMiniPanelAdapter
from HVAC.gui_v3.adapters.project_heatloss_readiness_adapter import (
    ProjectHeatLossReadinessAdapter,
)

# ----------------------------------------------------------------------
# Controllers
# ----------------------------------------------------------------------
from HVAC.heatloss_v3.heatloss_controller_v4 import HeatLossControllerV4


class MainWindowV3(QMainWindow):
    """
    GUI v3 main window.

    Observer-only shell:
    • Owns docks, panels, adapters, menus
    • Hosts HLPE (edit overlay)
    • Persists installation-level GUI state
    • Never owns engineering authority
    """

    def __init__(self, context: GuiProjectContext) -> None:
        super().__init__()

        # ---------------- Context ----------------
        self._context = context
        self._gui_settings = context.gui_settings

        # ---------------- Controllers ----------------
        self._heatloss_controller = HeatLossControllerV4(gui_context=self._context)

        # ---------------- Central placeholder ----------------
        self._central_placeholder = QWidget(self)
        self.setCentralWidget(self._central_placeholder)

        self.setWindowTitle("HVACgooee")
        self.setMinimumWidth(260)
        self._settings = QSettings("HVACgooee", "GUIv3")

        # ---------------- Lifecycle ----------------
        self._has_shown_once = False
        self._build_ui()
        self._restore_gui_state()
        if not self._has_shown_once:
            self._apply_default_layout()
            self._has_shown_once = True

        self._refresh_all_adapters()
        self._update_main_window_visibility()

        # ------------------------------------------------------------------
        # Room selection wiring (GuiProjectContext → MainWindow fan-out)
        # ------------------------------------------------------------------
        self._context.subscribe_room_selection_changed(self._on_room_selection_changed)

        # ------------------------------------------------------------------
        # HLPE state wiring (GuiProjectContext → overlay visibility)
        # ------------------------------------------------------------------
        self._context.subscribe_hlpe_changed(self._sync_hlpe_visibility)

        # ------------------------------------------------------------------
        # HLP cell-click edit wiring (HLP → MainWindow → HLPE)
        # ------------------------------------------------------------------
        self._heat_loss_panel.edit_requested.connect(self._on_hlp_edit_requested)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # ==============================================================
        # Project
        # ==============================================================
        self._project_panel = ProjectPanel(self)
        self._dock_project = QDockWidget("Project", self)
        self._dock_project.setObjectName("dock_project")
        self._dock_project.setWidget(self._project_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_project)

        self._project_panel_adapter = ProjectPanelAdapter(
            panel=self._project_panel,
            project_state=self._context.project_state,
        )

        # ==============================================================
        # Environment
        # ==============================================================
        self._environment_panel = EnvironmentPanel(self)
        self._dock_environment = QDockWidget("Environment", self)
        self._dock_environment.setObjectName("dock_environment")
        self._dock_environment.setWidget(self._environment_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_environment)

        self._environment_panel_adapter = EnvironmentPanelAdapter(
            panel=self._environment_panel,
            project_state=self._context.project_state,
        )

        # ==============================================================
        # Rooms
        # ==============================================================
        self._room_tree_panel = RoomTreePanel(self)
        self._dock_room_tree = QDockWidget("Rooms", self)
        self._dock_room_tree.setObjectName("dock_rooms")
        self._dock_room_tree.setWidget(self._room_tree_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_room_tree)

        self._room_tree_panel_adapter = RoomTreePanelAdapter(
            panel=self._room_tree_panel,
            context=self._context,
        )

        # ==============================================================
        # Construction
        # ==============================================================
        self._construction_panel = ConstructionPanel(self)
        self._dock_construction = QDockWidget("Construction", self)
        self._dock_construction.setObjectName("dock_construction")
        self._dock_construction.setWidget(self._construction_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_construction)

        # ==============================================================
        # U-Values
        # ==============================================================
        self._uvp_panel = UVPPanel(self)
        self._dock_uvp = QDockWidget("U-Values", self)
        self._dock_uvp.setObjectName("dock_uvp")
        self._dock_uvp.setWidget(self._uvp_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_uvp)

        # ==============================================================
        # Heat-Loss
        # ==============================================================
        self._heat_loss_panel = HeatLossPanelV3(self)
        self._dock_heat_loss = QDockWidget("Heat-Loss", self)
        self._dock_heat_loss.setObjectName("dock_heat_loss")
        self._dock_heat_loss.setWidget(self._heat_loss_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_heat_loss)

        # ---- Heat-loss adapters ----
        self._heat_loss_panel_adapter = HeatLossPanelAdapter(
            panel=self._heat_loss_panel,
            context=self._context,
        )

        self._geometry_mini_panel_adapter = GeometryMiniPanelAdapter(
            panel=self._heat_loss_panel._geometry_panel,
            context=self._context,
        )

        self._ach_mini_panel_adapter = ACHMiniPanelAdapter(
            panel=self._heat_loss_panel._ach_panel,
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

        # ---- Run wiring ----
        self._heat_loss_panel.run_requested.connect(self._on_run_heat_loss_requested)

        # ==============================================================
        # Heat-Loss Edit Overlay (HLPE)
        # ==============================================================
        self._hlpe = HeatLossEditOverlayPanel(self._heat_loss_panel)
        self._hlpe.hide()

        self._hlpe.apply_requested.connect(self._on_hlpe_apply)
        self._hlpe.cancel_requested.connect(self._on_hlpe_cancel)

        # ==============================================================
        # Education
        # ==============================================================
        self._education_panel = EducationPanel(self)
        self._dock_education = QDockWidget("Education", self)
        self._dock_education.setObjectName("dock_education")
        self._dock_education.setWidget(self._education_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_education)

        self._education_panel_adapter = EducationPanelAdapter(
            panel=self._education_panel,
            domain="heatloss",
            topic="overview",
            mode="standard",
        )

        # ==============================================================
        # Hydronics
        # ==============================================================
        self._hydronics_schematic_panel = HydronicsSchematicPanel(self)
        self._dock_hydronics = QDockWidget("Hydronics Schematic", self)
        self._dock_hydronics.setObjectName("dock_hydronics")
        self._dock_hydronics.setWidget(self._hydronics_schematic_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_hydronics)

        self._hydronics_schematic_panel_adapter = HydronicsSchematicPanelAdapter(
            panel=self._hydronics_schematic_panel,
            project_state=self._context.project_state,
        )

        # ==============================================================
        # Menus
        # ==============================================================
        self._build_file_menu()
        self._build_view_menu()
        self._build_help_menu()

    # ------------------------------------------------------------------
    # GUI persistence
    # ------------------------------------------------------------------
    def _restore_gui_state(self) -> None:
        geometry = self._settings.value("main_window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        state = self._settings.value("main_window/state")
        if state is not None:
            self.restoreState(state)

    # ------------------------------------------------------------------
    # HLP → HLPE entry (cell click)
    # ------------------------------------------------------------------
    def _on_hlp_edit_requested(self, room_id: str, element_id: str, attribute: str) -> None:
        """
        Receive HLP edit intent and enter HLPE.

        attribute: "area" | "u_value" | "delta_t"
        """

        # Guard: must target the currently selected room
        if room_id != self._context.current_room_id:
            return

        # Guard: one HLPE session at a time (v1 rule)
        if self._context.hlpe_active:
            return

        if attribute == "area":
            scope = "geometry"
        elif attribute == "u_value":
            scope = "construction"
        elif attribute == "delta_t":
            scope = "assumptions"
        else:
            return

        # Open HLPE session in context (GUI-only state)
        self._context.open_hlpe(scope=scope, room_id=room_id, surface_id=element_id)

        # Configure overlay heading (and keep it simple for v1)
        self._hlpe.set_heading(f"EDIT — {scope.upper()}")

        # If your overlay panel supports setting a target, use it.
        # This call is guarded so it won't crash if not present yet.
        if hasattr(self._hlpe, "set_target"):
            try:
                self._hlpe.set_target(room_id=room_id, surface_id=element_id, attribute=attribute)
            except TypeError:
                # Older signature
                self._hlpe.set_target(room_id=room_id, surface_id=element_id)

        self._sync_hlpe_visibility()

    # ------------------------------------------------------------------
    # HLPE control (buttons / ESC)
    # ------------------------------------------------------------------
    def _on_hlpe_cancel(self) -> None:
        self._context.close_hlpe()
        self._refresh_all_adapters()

    def _on_hlpe_apply(self) -> None:
        # Phase G: apply pathway is handled by HLPE internals later.
        # For now: close + refresh.
        self._context.close_hlpe()
        self._refresh_all_adapters()

    def _sync_hlpe_visibility(self) -> None:
        if self._context.hlpe_active:
            self._hlpe.show()
            self._hlpe.raise_()
        else:
            self._hlpe.hide()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape and self._context.hlpe_active:
            self._on_hlpe_cancel()
            return
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Room selection fan-out
    # ------------------------------------------------------------------
    def _on_room_selection_changed(self, room_id: str | None) -> None:
        """
        MainWindow fan-out for room selection.
        Panels/adapters observe context; MainWindow binds per-room panels.
        """

        # Tell HLP which room is current (for intent emission safety)
        self._heat_loss_panel.set_room(room_id)

        # Changing rooms invalidates HLPE in v1 (context already closes it),
        # but we still refresh.
        self._refresh_all_adapters()

    # ------------------------------------------------------------------
    # Project lifecycle
    # ------------------------------------------------------------------
    def _on_run_heat_loss_requested(self) -> None:
        self._heatloss_controller.run_project()
        self._refresh_all_adapters()

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------
    def _build_file_menu(self) -> None:
        menu = self.menuBar().addMenu("&File")

        act_new = QAction("New Project", self)
        act_new.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "New Project",
                "Project creation is not implemented yet.",
            )
        )
        menu.addAction(act_new)

        menu.addSeparator()

        def _stub(msg: str) -> None:
            QMessageBox.information(self, "Not implemented", msg)

        act_open = QAction("Open Project…", self)
        act_open.triggered.connect(lambda: _stub("Project loading is not implemented yet."))
        menu.addAction(act_open)

        act_save = QAction("Save Project", self)
        act_save.triggered.connect(lambda: _stub("Project saving is not implemented yet."))
        menu.addAction(act_save)

        act_save_as = QAction("Save Project As…", self)
        act_save_as.triggered.connect(lambda: _stub("Project saving is not implemented yet."))
        menu.addAction(act_save_as)

        menu.addSeparator()

        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close)
        menu.addAction(act_exit)

    def _build_view_menu(self) -> None:
        menu = self.menuBar().addMenu("&View")

        def add_toggle(label: str, dock: QDockWidget) -> None:
            action = QAction(label, self, checkable=True)
            action.setChecked(dock.isVisible())
            action.toggled.connect(dock.setVisible)
            dock.visibilityChanged.connect(action.setChecked)
            menu.addAction(action)

        act_reset = QAction("Reset Dock Layout", self)
        act_reset.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "Reset layout",
                "Dock layout reset is not implemented yet.",
            )
        )
        menu.addAction(act_reset)
        menu.addSeparator()

        add_toggle("Project", self._dock_project)
        add_toggle("Environment", self._dock_environment)
        add_toggle("Rooms", self._dock_room_tree)
        add_toggle("Construction", self._dock_construction)
        add_toggle("U-Values", self._dock_uvp)
        add_toggle("Heat-Loss", self._dock_heat_loss)
        add_toggle("Education", self._dock_education)
        add_toggle("Hydronics Schematic", self._dock_hydronics)

    def _build_help_menu(self) -> None:
        menu = self.menuBar().addMenu("&Help")
        act_about = QAction("About HVACgooee", self)
        act_about.triggered.connect(self._show_about)
        menu.addAction(act_about)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About HVACgooee",
            "HVACgooee\n\n"
            "Open-source HVAC engineering toolkit\n\n"
            "GUI v3 — Observer architecture\n"
            "Heat-Loss v3 — Manual recalculation\n\n"
            "© 1989–2026 HVACgooee Project\n"
            "GPLv3 Core",
        )

    # ------------------------------------------------------------------
    # Adapter refresh + visibility
    # ------------------------------------------------------------------
    def _refresh_all_adapters(self) -> None:
        if self._project_panel_adapter:
            self._project_panel_adapter.refresh()

        if self._environment_panel_adapter:
            self._environment_panel_adapter.refresh()

        if self._room_tree_panel_adapter:
            self._room_tree_panel_adapter.refresh()

        if self._geometry_mini_panel_adapter:
            self._geometry_mini_panel_adapter.refresh()

        if self._ach_mini_panel_adapter:
            self._ach_mini_panel_adapter.refresh()

        if self._heat_loss_panel_adapter:
            self._heat_loss_panel_adapter.refresh()

        if self._heat_loss_worksheet_adapter:
            self._heat_loss_worksheet_adapter.refresh()

        if self._education_panel_adapter:
            self._education_panel_adapter.refresh()

        if self._hydronics_schematic_panel_adapter:
            self._hydronics_schematic_panel_adapter.refresh()

    def _update_main_window_visibility(self) -> None:
        # Phase G stub
        pass

    def closeEvent(self, event) -> None:  # noqa: N802
        self._settings.setValue("main_window/geometry", self.saveGeometry())
        self._settings.setValue("main_window/state", self.saveState())
        super().closeEvent(event)

    def _apply_default_layout(self) -> None:
        # Left column — primary workflow
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_project)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_environment)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_room_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_construction)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_uvp)

        # Centre — Heat-Loss as primary worksheet
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_heat_loss)
        self._dock_heat_loss.raise_()

        # Right — reference / learning
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_education)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_hydronics)

        self._dock_heat_loss.show()
