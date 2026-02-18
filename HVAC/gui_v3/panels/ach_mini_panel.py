# ======================================================================
# HVAC/gui_v3/panels/ach_mini_panel.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
)


class ACHMiniPanel(QWidget):
    """
    GUI v3 — ACH Mini Panel (Ventilation intent)

    Phase I-B:
    • ACH input only
    • Emits intent
    • No calculations
    • No authority
    """

    ach_changed = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)

        header = QLabel("Ventilation")
        header.setStyleSheet("font-weight: 600;")
        root.addWidget(header)

        self._spin_ach = QDoubleSpinBox()
        self._spin_ach.setRange(0.0, 20.0)
        self._spin_ach.setDecimals(2)
        self._spin_ach.setSingleStep(0.1)
        self._spin_ach.setSuffix(" ACH")

        row = QHBoxLayout()
        row.addWidget(QLabel("Air changes per hour:"))
        row.addStretch()
        row.addWidget(self._spin_ach)
        root.addLayout(row)

        self._spin_ach.valueChanged.connect(self.ach_changed.emit)

    # ------------------------------------------------------------------
    # Presentation (observer-only)
    # ------------------------------------------------------------------

    def set_ach(self, ach: float) -> None:
        self._spin_ach.blockSignals(True)
        self._spin_ach.setValue(ach)
        self._spin_ach.blockSignals(False)

    def clear(self) -> None:
        self.set_ach(0.0)
