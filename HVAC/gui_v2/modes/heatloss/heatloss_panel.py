# ======================================================================
# HVAC/gui_v2/modes/heatloss/heatloss_panel.py
# ======================================================================

"""
HVACgooee — Heat-Loss Panel v3 (MINIMAL CANONICAL)

LOCKED INTENT
-------------
HeatLossPanel v3 is:
• A GUI shell for heat-loss intent
• A read-only inspector (future)
• A pure signal emitter

It does NOT:
• Own room navigation
• Own preview tables
• Touch geometry
• Touch constructions
• Mutate ProjectState
• Run engines

Anything beyond this file is an *explicit later step*.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,   # 👈 THIS ONE
    QLabel,
    QPushButton,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)


from HVAC.project.project_state import ProjectState

from HVAC.gui_v2.common.system_view_control import (
    SystemViewControl,
    SystemViewMode,
)

class HeatLossPanel(QWidget):
    # ------------------------------------------------------------------
    # LOCKED signals
    # ------------------------------------------------------------------
    room_selected = Signal(str)        # reserved for future
    run_heatloss_requested = Signal()  # authoritative intent only

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.project_state: Optional[ProjectState] = None

        self._build_ui()
        self._wire_ui()

        self._set_enabled(False)

        self.setStyleSheet("background-color: #303030;")

    # ------------------------------------------------------------------
    # Public API (LOCKED)
    # ------------------------------------------------------------------
    def bind_project_state(self, project_state: ProjectState) -> None:
        """
        Bind the authoritative ProjectState.

        This panel:
        • May read ProjectState later
        • Must never mutate validity
        • Must never run engines
        """
        self.project_state = project_state
        self._set_enabled(True)

    def refresh_from_state(self) -> None:
        self._refresh_room_list()
        self._refresh_room_views

        # Until estimate exists, ordering is provisional
        self.system_view_control.set_mode(SystemViewMode.PROVISIONAL)
    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # --------------------------------------------------
        # Header row
        # --------------------------------------------------
        header = QHBoxLayout()
        header.setSpacing(12)

        lbl_title = QLabel("Heat-Loss")
        lbl_title.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;"
        )

        header.addWidget(lbl_title)
        header.addStretch(1)

        # System view / ordering control (NEW)
        self.system_view_control = SystemViewControl()
        header.addWidget(self.system_view_control)

        layout.addLayout(header)

        # --------------------------------------------------
        # Info text
        # --------------------------------------------------
        lbl_info = QLabel(
            "Authoritative heat-loss is run from the menu or button below.\n"
            "Room order is provisional until pressure-drop estimation."
        )
        lbl_info.setStyleSheet("color: #b0b0b0;")
        lbl_info.setWordWrap(True)

        layout.addWidget(lbl_info)

        # --------------------------------------------------
        # Run button
        # --------------------------------------------------
        self._btn_run = QPushButton("Run Heat-Loss (Authoritative)")
        layout.addWidget(self._btn_run)

        layout.addStretch(1)

    def _wire_ui(self) -> None:
        self._btn_run.clicked.connect(self.run_heatloss_requested.emit)

        # System view toggle (GUI intent only)
        self.system_view_control.mode_changed.connect(
            self._on_system_view_mode_changed
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _set_enabled(self, enabled: bool) -> None:
        self._btn_run.setEnabled(enabled)

    def _on_system_view_mode_changed(self, mode: SystemViewMode) -> None:
        """
        GUI-only signal.

        • PROVISIONAL: room order as entered
        • INDEX_ORDER: post-estimate interpretation

        No engines. No state mutation.
        """
        # For now, this is purely explanatory.
        # Later:
        # - sync room ordering visuals
        # - sync schematic highlighting
        pass


