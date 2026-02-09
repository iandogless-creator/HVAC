# ======================================================================
# HVAC/gui_v2/main_window_v2.py
# ======================================================================

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QDockWidget,
    QTextBrowser,
    QMessageBox,
    QMenuBar,
    QMenu,
    QFileDialog,
)

from HVAC_legacy.gui_v2.header.top_mode_bar import TopModeBar
from HVAC_legacy.gui_v2.common.gui_view_state import GuiViewState
from HVAC_legacy.gui_v2.common.project_structure_viewer import ProjectStructureViewer

from HVAC_legacy.gui_v2.modes.comfort.comfort_panel import ComfortPanel
from HVAC_legacy.gui_v2.modes.heatloss.heatloss_panel import HeatLossPanel
from HVAC_legacy.gui_v2.modes.hydronics.hydronics_panel import HydronicsPanel
from HVAC_legacy.gui_v2.modes.fenestration.fenestration_panel import FenestrationPanel
from HVAC_legacy.gui_v2.modes.about.about_panel import AboutPanel
from HVAC_legacy.gui_v2.modes.heatloss.construction_panel import ConstructionPanel

from HVAC_legacy.project.project_state import ProjectState
from HVAC_legacy.project_v3.project_factory_v3 import ProjectFactoryV3

from HVAC_legacy.heatloss_v3.heatloss_runner_v3 import HeatLossRunnerV3
from HVAC_legacy.project_v3.run.hydronics_estimate_runner_v3 import HydronicsEstimateRunnerV3

from HVAC_legacy.education.resolver import resolve_education
from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)
from HVAC_legacy.constructions.construction_preset import SurfaceClass


# ======================================================================
# Education dock (passive)
# ======================================================================

class EducationDock(QDockWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__("Education", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )

        self._browser = QTextBrowser()
        self._browser.setReadOnly(True)
        self._browser.setOpenExternalLinks(False)
        self.setWidget(self._browser)

        self.set_context("comfort")

    def set_context(self, mode: str) -> None:
        self._browser.setPlainText(resolve_education(domain=mode))


# ======================================================================
# Main Window (v3 Orchestrator)
# ======================================================================

class MainWindowV2(QMainWindow):
    """
    HVACgooee — MainWindowV2 (v3 CANONICAL)

    LOCKS:
    • MainWindow owns all AUTHORITATIVE engine runs
    • GUI preview never mutates ProjectState authority
    • QStackedWidget is created ONCE
    """

    def __init__(
        self,
        view_state: GuiViewState,
        theme_manager: Any,
        paths: Any,
        project_meta: Any,
    ):
        super().__init__()

        # ------------------------------------------------------------
        # Store collaborators
        # ------------------------------------------------------------
        self.view_state = view_state
        self.theme_manager = theme_manager
        self.paths = paths
        self.project_meta = project_meta

        # ------------------------------------------------------------
        # ProjectState (GUI-owned, SINGLE SOURCE OF TRUTH)
        # ------------------------------------------------------------
        if self.view_state.project_state is None:
            self.project_state = ProjectState()
            self.view_state.project_state = self.project_state
        else:
            self.project_state = self.view_state.project_state

        # ------------------------------------------------------------
        # Build window chrome FIRST (creates self.stack)
        # ------------------------------------------------------------
        self._build_ui()

        # ------------------------------------------------------------
        # Panels (created ONCE)
        # ------------------------------------------------------------
        self._heatloss_panel = HeatLossPanel()
        self._construction_panel = ConstructionPanel()
        self._hydronics_panel = HydronicsPanel(self.view_state)
        self._project_structure_viewer = ProjectStructureViewer()

        # ------------------------------------------------------------
        # Bind ProjectState
        # ------------------------------------------------------------
        self._heatloss_panel.bind_project_state(self.project_state)
        self._construction_panel.bind_project_state(self.project_state)

        # ------------------------------------------------------------
        # Intent wiring (GUI → MainWindow)
        # ------------------------------------------------------------
        self._construction_panel.construction_committed.connect(
            self._on_construction_committed
        )

        self._heatloss_panel.run_heatloss_requested.connect(
            self._on_run_heatloss_authoritative_requested
        )

        self._hydronics_panel.run_hydronics_requested.connect(
            self._on_run_hydronics_requested
        )

        # ------------------------------------------------------------
        # Heat-loss container
        # ------------------------------------------------------------
        heatloss_container = QWidget()
        hl_layout = QVBoxLayout(heatloss_container)
        hl_layout.setContentsMargins(0, 0, 0, 0)
        hl_layout.setSpacing(8)
        hl_layout.addWidget(self._heatloss_panel, 1)

        # ------------------------------------------------------------
        # Panels registry
        # ------------------------------------------------------------
        self.panels: Dict[str, QWidget] = {
            "comfort": ComfortPanel(),
            "heatloss": heatloss_container,
            "hydronics": self._hydronics_panel,
            "fenestration": FenestrationPanel(),
            "structure": self._project_structure_viewer,
            "about": AboutPanel(),
        }

        for panel in self.panels.values():
            self.stack.addWidget(panel)

        # ------------------------------------------------------------
        # Initial panel (LOCKED)
        # ------------------------------------------------------------
        self.stack.setCurrentWidget(self.panels["heatloss"])
        self.view_state.mode = "heatloss"

        # ------------------------------------------------------------
        # Education dock
        # ------------------------------------------------------------
        self.education_dock = EducationDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.education_dock)
        self.education_dock.visibilityChanged.connect(
            self._on_education_visibility_changed
        )

        # ------------------------------------------------------------
        # Menu + initial view
        # ------------------------------------------------------------
        self._init_menu()
        self._apply_view_state()

        # ------------------------------------------------------------
        # Active project (v3)
        # ------------------------------------------------------------
        self._active_project_v3: Optional[Any] = None

        # ------------------------------------------------------------
        # Final invariant check
        # ------------------------------------------------------------
        self._assert_project_state_invariant("init")

    # ------------------------------------------------------------------
    # UI chrome
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """
        Creates the central stacked widget ONCE.
        """
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------

    def _assert_project_state_invariant(self, where: str = "") -> None:
        if self.project_state is None:
            raise AssertionError(f"[{where}] project_state is None")

        if self.view_state.project_state is not self.project_state:
            raise AssertionError(
                f"[{where}] view_state.project_state mismatch:\n"
                f"  view_state id={id(self.view_state.project_state)}\n"
                f"  self.project_state id={id(self.project_state)}"
            )

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _init_menu(self) -> None:
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = QMenu("File", self)
        menubar.addMenu(file_menu)

        file_menu.addAction("Open Project…").triggered.connect(
            self._on_open_project
        )

        run_menu = QMenu("Run", self)
        menubar.addMenu(run_menu)

        run_menu.addAction(
            "Run Heat-Loss (Authoritative)"
        ).triggered.connect(self._on_run_heatloss_authoritative_requested)

    # ------------------------------------------------------------------
    # Project loading
    # ------------------------------------------------------------------

    def _on_open_project(self) -> None:
        base_dir = Path(
            "//HVACprojects"
        )

        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Open HVACgooee Project",
            str(base_dir),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if project_dir:
            self._load_project(project_dir)

    def _load_project(self, project_dir: str | Path) -> None:
        try:
            project = ProjectFactoryV3.load(project_dir)
        except Exception as exc:
            QMessageBox.critical(self, "Project Load Failed", str(exc))
            return

        self._active_project_v3 = project

        loaded = project.project_state
        for field in loaded.__slots__:
            setattr(self.project_state, field, getattr(loaded, field))

        project.project_state = self.project_state
        self.view_state.project_state = self.project_state

        self._project_structure_viewer.set_project(project)
        self._hydronics_panel.refresh_from_project_state()

        self._assert_project_state_invariant("after project load")

    # ------------------------------------------------------------------
    # Heat-loss (AUTHORITATIVE)
    # ------------------------------------------------------------------

    def _on_run_heatloss_authoritative_requested(self) -> None:
        project = self._active_project_v3
        if project is None:
            QMessageBox.warning(self, "Heat-Loss", "Load a project first.")
            return

        ps = self.project_state

        # v3: constructions are per-room, not project-level
        rooms = getattr(ps, "rooms", {}) or {}

        rooms_with_constructions = [
            r for r in rooms.values()
            if getattr(r, "constructions", None)
        ]

        if not rooms_with_constructions:
            QMessageBox.information(
                self,
                "Heat-Loss blocked",
                "No constructions declared yet.\n\n"
                "Commit constructions for at least one room\n"
                "(Construction panel → Commit)."
            )
            return

        try:
            qt_w = HeatLossRunnerV3.run_authoritative_qt(project)
        except Exception as exc:
            QMessageBox.critical(self, "Heat-Loss Failed", str(exc))
            return

        ps.heatloss_qt_w = float(qt_w)
        ps.heatloss_valid = True
        ps.hydronics_valid = False

        self._hydronics_panel.refresh_from_project_state()
        self._assert_project_state_invariant("after heatloss run")

    # ------------------------------------------------------------------
    # Constructions
    # ------------------------------------------------------------------

    def _on_construction_committed(
        self,
        room_id: str,
        surface: SurfaceClass,
        dto: ConstructionUValueResultDTO,
    ) -> None:
        room = self.project_state.rooms[room_id]
        room.constructions[surface] = dto
        room.heatloss_preview_qt_w = None
        self.project_state.heatloss_valid = False
        self._heatloss_panel.refresh_from_state()

    # ------------------------------------------------------------------
    # Hydronics (AUTHORITATIVE)
    # ------------------------------------------------------------------

    def _on_run_hydronics_requested(self) -> None:
        project = self._active_project_v3
        if project is None:
            QMessageBox.warning(self, "Hydronics", "Load a project first.")
            return

        if not self.project_state.heatloss_valid:
            QMessageBox.warning(
                self,
                "Hydronics",
                "Run Heat-Loss (Authoritative) first."
            )
            return

        HydronicsEstimateRunnerV3.run(project)
        self._hydronics_panel.refresh_from_project_state()
        self._assert_project_state_invariant("after hydronics run")

        from HVAC_legacy.project_v3.run.hydronics_qt_sanity_engine import (
        run_hydronics_qt_sanity,
    )
        qt = run_hydronics_qt_sanity(project)
        print(f"[GUI] Hydronics received Qt = {qt:.2f} W")

    # ------------------------------------------------------------------
    # View state
    # ------------------------------------------------------------------

    def _apply_view_state(self) -> None:
        try:
            self.education_dock.setVisible(
                self.view_state.education_visible
            )
        except Exception:
            pass

    def _on_education_visibility_changed(self, visible: bool) -> None:
        self.view_state.education_visible = visible
