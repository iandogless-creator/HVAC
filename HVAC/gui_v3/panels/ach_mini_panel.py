# ======================================================================
# HVAC/gui_v3/panels/ach_mini_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
)

# ======================================================================
# ACHMiniPanel
# ======================================================================

class ACHMiniPanel(QWidget):
    """
    ACH Editor (overlay panel)

    Authority
    ---------
    • Edits ACH only
    • Emits committed value only
    • Does NOT mutate ProjectState
    • Does NOT perform calculations

    Lifecycle
    ---------
    • Created by OverlayController
    • Primed by adapter
    • Emits commit → adapter writes → refresh
    """

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    ach_committed = Signal(float)
    value_changed = Signal(float)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._last_value: Optional[float] = None

        self._build_ui()
        self._wire_signals()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Header
        self._header = QLabel("Ventilation")
        self._header.setStyleSheet("font-weight: 600;")
        root.addWidget(self._header)

        # Spinbox
        self._spin_ach = QDoubleSpinBox(self)
        self._spin_ach.setRange(0.0, 20.0)
        self._spin_ach.setDecimals(2)
        self._spin_ach.setSingleStep(0.10)
        self._spin_ach.setSuffix(" ACH")
        self._spin_ach.setFixedWidth(100)
        self._spin_ach.editingFinished.connect(
            lambda: self.value_changed.emit(self._spin_ach.value())
        )
        row = QHBoxLayout()
        row.addWidget(QLabel("Air changes per hour:"))
        row.addStretch()
        row.addWidget(self._spin_ach)

        root.addLayout(row)

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _wire_signals(self) -> None:
        # Commit only when user finishes editing (not every tick)
        self._spin_ach.editingFinished.connect(
            lambda: self.value_changed.emit(self._spin_ach.value())
        )

    def set_value(self, value: float) -> None:
        self._spin_ach.blockSignals(True)
        self._spin_ach.setValue(value)
        self._spin_ach.blockSignals(False)
    # ------------------------------------------------------------------
    # Public API (adapter calls)
    # ------------------------------------------------------------------
    def set_room_header(self, room_name: str) -> None:
        self._header.setText(f"Ventilation — {room_name}")

    def set_ach(self, ach: float) -> None:
        self._spin_ach.blockSignals(True)
        self._spin_ach.setValue(float(ach))
        self._spin_ach.blockSignals(False)

        self._last_value = float(ach)

    def clear(self) -> None:
        self.set_ach(0.0)
        self._last_value = None

    # ------------------------------------------------------------------
    # Commit logic
    # ------------------------------------------------------------------
    def _on_edit_finished(self) -> None:
        value = float(self._spin_ach.value())

        # Prevent duplicate commits
        if self._last_value is not None and value == self._last_value:
            return

        self._last_value = value

        self.ach_committed.emit(value)