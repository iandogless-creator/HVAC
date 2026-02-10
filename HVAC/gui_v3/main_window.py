# ======================================================================
# HVACgooee — Main Window (GUI v3)
# Phase: GUI v3 — Observer
# Sub-Phase: Phase E/F (Dock Integration + Persistence + Shell Collapse)
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QWidget,
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
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.gui_v3.panels.education_panel import EducationPanel
from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel
from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel
# ----------------------------------------------------------------------
# Adapters (read-only)
# ----------------------------------------------------------------------
from HVAC.gui_v3.adapters.project_panel_adapter import ProjectPanelAdapter
from HVAC.gui_v3.adapters.environment_panel_adapter import EnvironmentPanelAdapter
from HVAC.gui_v3.adapters.heat_loss_panel_adapter import HeatLossPanelAdapter
from HVAC.gui_v3.adapters.education_panel_adapter import EducationPanelAdapter
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.adapters.room_tree_panel_adapter import RoomTreePanelAdapter
# ----------------------------------------------------------------------
# Controllers
# ----------------------------------------------------------------------
from HVAC.heatloss_v3.heatloss_controller_v4 import HeatLossControllerV4

from HVAC.gui_v3.adapters.heat_loss_worksheet_adapter import (
    HeatLossWorksheetAdapter,
)
from HVAC.gui_v3.panels.uvp_panel import UVPPanel
from HVAC.gui_v3.panels.construction_panel import ConstructionPanel

# ======================================================================
# MainWindowV3
# ======================================================================
class MainWindowV3(QMainWindow):
    """
    GUI v3 main window.

    Observer-only shell:
    • Owns docks, panels, adapters, menus
    • Persists installation-level GUI state
    • Never owns engineering authority
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, context: GuiProjectContext) -> None:
        super().__init__()

        # --------------------------------------------------------------
        # GUI-facing context (authoritative boundary)
        # --------------------------------------------------------------
        self._gui_context = context
        self._context = context
        self._gui_settings = context.gui_settings

        # --------------------------------------------------------------
        # Controllers (exist before adapters)
        # --------------------------------------------------------------
        self._heatloss_controller = HeatLossControllerV4(
            project_state=self._context.project_state
        )
        # Docks (Phase E invariant)
        self._dock_project = None
        self._dock_environment = None
        self._dock_heat_loss = None
        self._dock_room_tree = None
        self._dock_construction = None
        self._dock_uvp = None
        self._dock_education = None
        self._dock_hydronics = None

        # --------------------------------------------------------------
        # Panels (MUST exist before adapters)
        # --------------------------------------------------------------
        self._project_panel: ProjectPanel | None = ProjectPanel(self)
        self._environment_panel: EnvironmentPanel | None = EnvironmentPanel(self)
        self._heat_loss_panel: HeatLossPanelV3 | None = HeatLossPanelV3(self)
        self._construction_panel: ConstructionPanel | None = None
        self._uvp_panel: UVPPanel | None = None
        self._education_panel: EducationPanel | None = EducationPanel(self)
        self._hydronics_schematic_panel: HydronicsSchematicPanel | None = (
            HydronicsSchematicPanel(self)
        )

        # Room tree panel
        self._room_tree_panel: RoomTreePanel | None = RoomTreePanel(self)

        # --------------------------------------------------------------
        # Adapters (AFTER panels exist)
        # --------------------------------------------------------------
        # --------------------------------------------------------------
        # Adapters (AFTER panels exist)
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Adapters (AFTER panels exist)
        # --------------------------------------------------------------

        self._project_panel_adapter = ProjectPanelAdapter(
            panel=self._project_panel,
            project_state=self._context.project_state,
        )

        self._environment_panel_adapter = EnvironmentPanelAdapter(
            panel=self._environment_panel,
            project_state=self._context.project_state,
        )

        self._heat_loss_panel_adapter = HeatLossPanelAdapter(
            panel=self._heat_loss_panel,
            project_state=context.project_state,
            gui_context=self._gui_context,
        )

        self._heat_loss_worksheet_adapter = HeatLossWorksheetAdapter(
            panel=self._heat_loss_panel,
            context=self._gui_context,
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

        self._room_tree_panel_adapter = RoomTreePanelAdapter(
            panel=self._room_tree_panel,
            context=self._gui_context,
        )

        # --------------------------------------------------------------
        # Central placeholder (keeps menu bar alive)
        # --------------------------------------------------------------
        self._central_placeholder = QWidget(self)
        self.setCentralWidget(self._central_placeholder)

        self.setWindowTitle("HVACgooee")
        self.setMinimumWidth(260)

        # --------------------------------------------------------------
        # Build + restore + refresh
        # --------------------------------------------------------------
        self._has_shown_once = False
        self._build_ui()
        self._restore_gui_state()

        self._initial_refresh()
        self._refresh_all_adapters()
        self._update_main_window_visibility()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # --------------------------------------------------------------
        # Project panel
        # --------------------------------------------------------------
        self._project_panel = ProjectPanel(self)
        self._dock_project = QDockWidget("Project", self)
        self._dock_project.setObjectName("dock_project")
        self._dock_project.setWidget(self._project_panel)
        self._dock_project.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_project)

        # --------------------------------------------------------------
        # Environment panel
        # --------------------------------------------------------------
        self._environment_panel = EnvironmentPanel(self)
        self._dock_environment = QDockWidget("Environment", self)
        self._dock_environment.setObjectName("dock_environment")
        self._dock_environment.setWidget(self._environment_panel)
        self._dock_environment.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_environment)

        self._environment_panel_adapter = EnvironmentPanelAdapter(
            panel=self._environment_panel,
            project_state=self._context.project_state,
        )

        # --------------------------------------------------------------
        # Heat-loss panel
        # --------------------------------------------------------------
        self._heat_loss_panel = HeatLossPanelV3(self)
        self._dock_heat_loss = QDockWidget("Heat-Loss", self)
        self._dock_heat_loss.setObjectName("dock_heat_loss")
        self._dock_heat_loss.setWidget(self._heat_loss_panel)
        self._dock_heat_loss.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_heat_loss)

        self._heat_loss_panel_adapter = HeatLossPanelAdapter(
            panel=self._heat_loss_panel,
            context=self._context,
            controller=self._heatloss_controller,
        )

        # --------------------------------------------------------------
        # Education panel
        # --------------------------------------------------------------
        self._education_panel = EducationPanel(self)
        self._dock_education = QDockWidget("Education", self)
        self._dock_education.setObjectName("dock_education")
        self._dock_education.setWidget(self._education_panel)
        self._dock_education.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_education)

        self._education_panel_adapter = EducationPanelAdapter(
            panel=self._education_panel,
            domain="heatloss",
            topic="overview",
            mode="standard",
        )

        # --------------------------------------------------------------
        # Hydronics schematic panel
        # --------------------------------------------------------------
        self._hydronics_schematic_panel = HydronicsSchematicPanel(self)
        self._dock_hydronics = QDockWidget("Hydronics Schematic", self)
        self._dock_hydronics.setObjectName("dock_hydronics")
        self._dock_hydronics.setWidget(self._hydronics_schematic_panel)
        self._dock_hydronics.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_hydronics)

        self._hydronics_schematic_panel_adapter = (
            HydronicsSchematicPanelAdapter(
                panel=self._hydronics_schematic_panel,
                project_state=self._context.project_state,
            )
        )
        # --------------------------------------------------------------
        # Room tree panel
        # --------------------------------------------------------------
        self._room_tree_panel = RoomTreePanel(self)
        self._dock_room_tree = QDockWidget("Rooms", self)
        self._dock_room_tree.setObjectName("dock_rooms")
        self._dock_room_tree.setWidget(self._room_tree_panel)
        self._dock_room_tree.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )

        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_room_tree)

        self._room_tree_panel_adapter = RoomTreePanelAdapter(
            panel=self._room_tree_panel,
            context=self._context,
        )
        self._dock_construction: QDockWidget | None = None
        self._dock_uvp: QDockWidget | None = None

    # ------------------------------------------------------------------
    # UI construction (CANONICAL)
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # --------------------------------------------------------------
        # Project panel
        # --------------------------------------------------------------
        self._project_panel = ProjectPanel(self)
        self._dock_project = QDockWidget("Project", self)
        self._dock_project.setObjectName("dock_project")
        self._dock_project.setWidget(self._project_panel)
        self._dock_project.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_project)

        self._project_panel_adapter = ProjectPanelAdapter(
            panel=self._project_panel,
            project_state=self._context.project_state,
        )

        # --------------------------------------------------------------
        # Environment panel
        # --------------------------------------------------------------
        self._environment_panel = EnvironmentPanel(self)
        self._dock_environment = QDockWidget("Environment", self)
        self._dock_environment.setObjectName("dock_environment")
        self._dock_environment.setWidget(self._environment_panel)
        self._dock_environment.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_environment)

        self._environment_panel_adapter = EnvironmentPanelAdapter(
            panel=self._environment_panel,
            project_state=self._context.project_state,
        )

        # --------------------------------------------------------------
        # Rooms panel
        # --------------------------------------------------------------
        self._room_tree_panel = RoomTreePanel(self)
        self._dock_room_tree = QDockWidget("Rooms", self)
        self._dock_room_tree.setObjectName("dock_rooms")
        self._dock_room_tree.setWidget(self._room_tree_panel)
        self._dock_room_tree.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_room_tree)

        self._room_tree_panel_adapter = RoomTreePanelAdapter(
            panel=self._room_tree_panel,
            context=self._context,
        )

        # --------------------------------------------------------------
        # Construction panel (Phase B)
        # --------------------------------------------------------------
        self._construction_panel = ConstructionPanel(self)
        self._dock_construction = QDockWidget("Construction", self)
        self._dock_construction.setObjectName("dock_construction")
        self._dock_construction.setWidget(self._construction_panel)
        self._dock_construction.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_construction)

        # --------------------------------------------------------------
        # UVP panel (Phase B)
        # --------------------------------------------------------------
        self._uvp_panel = UVPPanel(self)
        self._dock_uvp = QDockWidget("U-Values", self)
        self._dock_uvp.setObjectName("dock_uvp")
        self._dock_uvp.setWidget(self._uvp_panel)
        self._dock_uvp.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_uvp)

        # --------------------------------------------------------------
        # Heat-loss panel
        # --------------------------------------------------------------
        self._heat_loss_panel = HeatLossPanelV3(self)
        self._dock_heat_loss = QDockWidget("Heat-Loss", self)
        self._dock_heat_loss.setObjectName("dock_heat_loss")
        self._dock_heat_loss.setWidget(self._heat_loss_panel)
        self._dock_heat_loss.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_heat_loss)

        self._heat_loss_panel_adapter = HeatLossPanelAdapter(
            panel=self._heat_loss_panel,
            project_state=self._context.project_state,
            gui_context=self._gui_context,
        )

        self._heat_loss_worksheet_adapter = HeatLossWorksheetAdapter(
            panel=self._heat_loss_panel,
            context=self._gui_context,
        )

        # --------------------------------------------------------------
        # Education panel
        # --------------------------------------------------------------
        self._education_panel = EducationPanel(self)
        self._dock_education = QDockWidget("Education", self)
        self._dock_education.setObjectName("dock_education")
        self._dock_education.setWidget(self._education_panel)
        self._dock_education.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_education)

        self._education_panel_adapter = EducationPanelAdapter(
            panel=self._education_panel,
            domain="heatloss",
            topic="overview",
            mode="standard",
        )

        # --------------------------------------------------------------
        # Hydronics schematic panel
        # --------------------------------------------------------------
        self._hydronics_schematic_panel = HydronicsSchematicPanel(self)
        self._dock_hydronics = QDockWidget("Hydronics Schematic", self)
        self._dock_hydronics.setObjectName("dock_hydronics")
        self._dock_hydronics.setWidget(self._hydronics_schematic_panel)
        self._dock_hydronics.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_hydronics)

        self._hydronics_schematic_panel_adapter = HydronicsSchematicPanelAdapter(
            panel=self._hydronics_schematic_panel,
            project_state=self._context.project_state,
        )

        # --------------------------------------------------------------
        # Dock topology tracking (CANONICAL)
        # --------------------------------------------------------------
        for dock in (
                self._dock_project,
                self._dock_environment,
                self._dock_room_tree,
                self._dock_construction,
                self._dock_uvp,
                self._dock_heat_loss,
                self._dock_education,
                self._dock_hydronics,
        ):
            if dock is None:
                continue

            dock.visibilityChanged.connect(
                lambda _=None, self=self: self._update_main_window_visibility()
            )
            dock.topLevelChanged.connect(
                lambda _=None, self=self: self._update_main_window_visibility()
            )
            dock.dockLocationChanged.connect(
                lambda _=None, self=self: self._update_main_window_visibility()
            )
        # ------------------------------------------------------------------
        # Phase F — Development-safe inspector visibility
        # ------------------------------------------------------------------
        self._dock_construction.show()
        self._dock_uvp.show()

        # --------------------------------------------------------------
        # Menus (MUST exist in same _build_ui)
        # --------------------------------------------------------------
        self._build_file_menu()
        self._build_view_menu()
        self._build_help_menu()

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------
    def _build_file_menu(self) -> None:
        menu = self.menuBar().addMenu("File")
        menu.addAction("New Project").triggered.connect(self._new_project)
        menu.addAction("Open Project…").triggered.connect(self._open_project_dialog)
        menu.addSeparator()
        menu.addAction("Exit").triggered.connect(self.close)

    def _build_view_menu(self) -> None:
        menu = self.menuBar().addMenu("View")
        menu.addAction(self._dock_project.toggleViewAction())      # type: ignore
        menu.addAction(self._dock_environment.toggleViewAction())  # type: ignore
        menu.addAction(self._dock_room_tree.toggleViewAction())
        menu.addAction(self._dock_heat_loss.toggleViewAction())    # type: ignore
        menu.addAction(self._dock_education.toggleViewAction())    # type: ignore
        menu.addAction(self._dock_hydronics.toggleViewAction())    # type: ignore


    def _build_help_menu(self) -> None:
        menu = self.menuBar().addMenu("Help")
        menu.addAction("About HVACgooee").triggered.connect(self._show_about_dialog)

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------
    def _show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            "About HVACgooee",
            (
                "<b>HVACgooee</b><br><br>"
                "© 1989–2026 HVACgooee Project<br>"
                "Author & Lead Architect: Ian Allison<br><br>"
                "GPL-v3 licensed core.<br>"
                "GUI is non-authoritative.<br><br>"
                "github.com/iandogless-creator/HVAC<br>"
                "<i>gooee.online (planned)</i>"
            ),
        )

    # ------------------------------------------------------------------
    # Refresh & persistence
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Qt lifecycle
    # ------------------------------------------------------------------
    def showEvent(self, event) -> None:
        super().showEvent(event)

        if not self._has_shown_once:
            self._has_shown_once = True

            # Ensure at least one dock is visible on first show
            if self._dock_project:
                self._dock_project.show()

    def _initial_refresh(self) -> None:
        if self._heat_loss_panel_adapter:
            self._heat_loss_panel_adapter.refresh()

    def _refresh_all_adapters(self) -> None:
        for adapter in (
            self._project_panel_adapter,
            self._environment_panel_adapter,
            self._room_tree_panel_adapter,
            self._heat_loss_panel_adapter,
            self._education_panel_adapter,
            self._hydronics_schematic_panel_adapter,
        ):
            if adapter:
                adapter.refresh()

    def _restore_gui_state(self) -> None:
        try:
            if self._gui_settings.window_geometry:
                self.restoreGeometry(self._gui_settings.window_geometry)
            if self._gui_settings.window_state:
                self.restoreState(self._gui_settings.window_state)
        except Exception:
            pass

    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self._gui_settings.window_geometry = bytes(self.saveGeometry())
            self._gui_settings.window_state = bytes(self.saveState())
            self._gui_settings.save()
        except Exception:
            pass
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Shell collapse behaviour
    # ------------------------------------------------------------------
    def _update_main_window_visibility(self) -> None:
        docks = (
            self._dock_project,
            self._dock_environment,
            self._dock_room_tree,
            self._dock_construction,
            self._dock_uvp,
            self._dock_heat_loss,
            self._dock_education,
            self._dock_hydronics,
        )

        any_docked = any(
            dock is not None
            and dock.isVisible()
            and not dock.isFloating()
            for dock in docks
        )

        # NEVER hide the central widget (menus depend on it)
        self._central_placeholder.setVisible(True)

        if not any_docked:
            self.adjustSize()

    # ------------------------------------------------------------------
    # Project lifecycle
    # ------------------------------------------------------------------
    def _open_project_dialog(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        hvac_root = Path(__file__).resolve().parents[1]
        start_dir = hvac_root / "HVACprojects" / "examples"

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open HVAC Project",
            str(start_dir),
            "HVAC project (project.json)",
        )

        if path:
            print(f"Selected project: {path}")

    def _new_project(self) -> None:
        from HVAC.project_v3.project_factory_v3 import ProjectFactoryV3

        project = ProjectFactoryV3.create_empty()
        self._context.set_project_state(project)
        self._refresh_all_adapters()
