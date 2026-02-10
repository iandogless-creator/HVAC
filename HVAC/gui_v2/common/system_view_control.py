# ======================================================================
# HVAC/gui_v2/common/system_view_control.py
# ======================================================================

from __future__ import annotations

from enum import Enum
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from HVAC.gui_v2.common.ui_state_badge import apply_badge_state


# ----------------------------------------------------------------------
# View modes (GUI-only, semantic)
# ----------------------------------------------------------------------
class SystemViewMode(Enum):
    PROVISIONAL = "provisional"
    INDEX_ORDER = "index_order"


# ----------------------------------------------------------------------
# System View Control (CANONICAL v1)
# ----------------------------------------------------------------------
class SystemViewControl(QWidget):
    """
    Small, reusable GUI control that expresses *system ordering state*.

    LOCKED:
    • GUI-only
    • Emits intent only
    • No ProjectState access
    • No calculations

    States:
    • PROVISIONAL  — user-entered / room order
    • INDEX_ORDER  — post-estimate index-leg ordering
    """

    mode_changed = Signal(SystemViewMode)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._mode = SystemViewMode.PROVISIONAL

        self._build_ui()
        self._apply_mode(self._mode)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Status badge
        self._badge = QLabel()
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setFixedHeight(22)
        self._badge.setMinimumWidth(140)
        self._badge.setStyleSheet(
            "border-radius: 4px; font-weight: bold;"
        )
        self._badge.setToolTip(
            "Insufficient valve authority — STOP.\n"
            "No valid preset exists.\n"
            "Balancing must not proceed."
        )

        # Toggle button
        self._toggle = QPushButton("⇄")
        self._toggle.setFixedSize(28, 22)
        self._toggle.setToolTip(
            "Toggle between provisional room order and index-leg order"
        )
        self._toggle.clicked.connect(self._on_toggle_clicked)

        layout.addWidget(self._badge)
        layout.addWidget(self._toggle)

        self.setStyleSheet("""
            QToolTip {
            background-color: #2b2b2b;
            color: #f0f0f0;
            border: 1px solid #5fa3ff;
            padding: 6px;
        }
        """)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def set_mode(self, mode: SystemViewMode) -> None:
        """
        External setter (e.g. after estimate or schematic click).
        """
        if mode is self._mode:
            return

        self._mode = mode
        self._apply_mode(mode)
        self.mode_changed.emit(mode)

    def mode(self) -> SystemViewMode:
        return self._mode

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _on_toggle_clicked(self) -> None:
        next_mode = (
            SystemViewMode.INDEX_ORDER
            if self._mode is SystemViewMode.PROVISIONAL
            else SystemViewMode.PROVISIONAL
        )
        self.set_mode(next_mode)

    def _apply_mode(self, mode: SystemViewMode) -> None:
        if mode is SystemViewMode.PROVISIONAL:
            apply_badge_state(
                self._badge,
                text="Provisional order",
                tooltip=(
                    "Room order is provisional.\n"
                    "The index leg will be identified automatically\n"
                    "after pressure-drop estimation."
                ),
                bg="#3a3a3a",
                fg="#cfcfcf",
                border="#666",
            )

        else:  # INDEX_ORDER
            apply_badge_state(
                self._badge,
                text="Index leg order",
                tooltip=(
                    "System is ordered by pressure drop.\n"
                    "Rooms are arranged from index leg\n"
                    "to minimum differential pressure."
                ),
                bg="#2b4f7a",
                fg="#e8f2ff",
                border="#5fa3ff",
            )
