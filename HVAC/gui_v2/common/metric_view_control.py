# ======================================================================
# HVAC/gui_v2/common/metric_view_control.py
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


# ----------------------------------------------------------------------
# Metric view modes (GUI-only)
# ----------------------------------------------------------------------
class MetricViewMode(Enum):
    NONE = "none"
    VELOCITY = "velocity"
    PRESSURE_DROP = "pressure_drop"
    FLOW_RATE = "flow_rate"


# ----------------------------------------------------------------------
# Metric View Control (CANONICAL v1)
# ----------------------------------------------------------------------
class MetricViewControl(QWidget):
    """
    Small, reusable GUI control that expresses *displayed metric intent*.

    LOCKED:
    • GUI-only
    • Emits intent only
    • No ProjectState access
    • No physics
    • No colour logic beyond badge hinting

    Intended use:
    • Schematics
    • Pipe highlighting
    • Legends / overlays
    """

    metric_changed = Signal(MetricViewMode)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._mode = MetricViewMode.NONE

        self._build_ui()
        self._apply_mode(self._mode)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Badge
        self._badge = QLabel()
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setFixedHeight(22)
        self._badge.setMinimumWidth(120)
        self._badge.setStyleSheet("border-radius: 4px; font-weight: bold;")

        # Toggle button
        self._toggle = QPushButton("⇄")
        self._toggle.setFixedSize(28, 22)
        self._toggle.setToolTip("Cycle display metric")
        self._toggle.clicked.connect(self._on_toggle_clicked)

        layout.addWidget(self._badge)
        layout.addWidget(self._toggle)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def set_mode(self, mode: MetricViewMode) -> None:
        if mode is self._mode:
            return

        self._mode = mode
        self._apply_mode(mode)
        self.metric_changed.emit(mode)

    def mode(self) -> MetricViewMode:
        return self._mode

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _on_toggle_clicked(self) -> None:
        order = [
            MetricViewMode.NONE,
            MetricViewMode.VELOCITY,
            MetricViewMode.PRESSURE_DROP,
            MetricViewMode.FLOW_RATE,
        ]
        idx = order.index(self._mode)
        self.set_mode(order[(idx + 1) % len(order)])

    def _apply_mode(self, mode: MetricViewMode) -> None:
        if mode is MetricViewMode.NONE:
            self._badge.setText("No metric")
            self._badge.setToolTip(
                "No metric overlay.\n"
                "Schematic is shown without quantitative colouring."
            )
            self._badge.setStyleSheet(
                """
                QLabel {
                    background-color: #3a3a3a;
                    color: #cfcfcf;
                    border: 1px solid #666;
                }
                """
            )

        elif mode is MetricViewMode.VELOCITY:
            self._badge.setText("Velocity")
            self._badge.setToolTip(
                "Pipe velocity view.\n"
                "Colours indicate flow velocity magnitude."
            )
            self._badge.setStyleSheet(
                """
                QLabel {
                    background-color: #355f3b;
                    color: #e6ffe8;
                    border: 1px solid #6fcf8e;
                }
                """
            )

        elif mode is MetricViewMode.PRESSURE_DROP:
            self._badge.setText("ΔP")
            self._badge.setToolTip(
                "Pressure-drop view.\n"
                "Colours indicate differential pressure along paths."
            )
            self._badge.setStyleSheet(
                """
                QLabel {
                    background-color: #5b2d2d;
                    color: #ffecec;
                    border: 1px solid #e07a7a;
                }
                """
            )

        elif mode is MetricViewMode.FLOW_RATE:
            self._badge.setText("Flow")
            self._badge.setToolTip(
                "Flow-rate view.\n"
                "Colours indicate volumetric or mass flow rate."
            )
            self._badge.setStyleSheet(
                """
                QLabel {
                    background-color: #2d4660;
                    color: #eaf4ff;
                    border: 1px solid #7aa7e0;
                }
                """
            )
