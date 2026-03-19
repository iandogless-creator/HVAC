# ======================================================================
# HVAC/gui_v3/panels/environment_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
)

# ======================================================================
# EnvironmentPanel
# ======================================================================


class EnvironmentPanel(QWidget):
    """
    GUI v3 — Environment Panel

    Authority
    ---------
    • Emits intent only
    • Does NOT mutate ProjectState
    • Displays and edits environmental defaults

    Contract
    --------
    • Te (external design temp)
    • Default internal temperature (Ti default)
    • Default room height
    • Default ACH
    """

    # ------------------------------------------------------------------
    # Signals (intent only)
    # ------------------------------------------------------------------
    external_temp_changed = Signal(float)
    default_internal_temp_changed = Signal(float)
    default_height_changed = Signal(float)
    default_ach_changed = Signal(float)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        header = QLabel("Environment")
        header.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(header)

        # --------------------------------------------------
        # Widgets first (so we can safely add them to forms)
        # --------------------------------------------------

        # External design temperature (Te)
        self._te_input = QDoubleSpinBox(self)
        self._te_input.setRange(-50.0, 50.0)
        self._te_input.setDecimals(1)
        self._te_input.setSingleStep(0.5)
        self._te_input.setMinimumWidth(110)
        self._te_input.valueChanged.connect(self.external_temp_changed.emit)

        # Default internal temperature (Ti default)
        self._ti_input = QDoubleSpinBox(self)
        self._ti_input.setRange(0.0, 40.0)
        self._ti_input.setDecimals(1)
        self._ti_input.setSingleStep(0.5)
        self._ti_input.setMinimumWidth(110)
        self._ti_input.valueChanged.connect(self.default_internal_temp_changed.emit)

        # Default room height
        self._height_input = QDoubleSpinBox(self)
        self._height_input.setRange(0.0, 10.0)
        self._height_input.setDecimals(2)
        self._height_input.setSingleStep(0.1)
        self._height_input.setMinimumWidth(110)
        self._height_input.valueChanged.connect(self.default_height_changed.emit)

        # Default ACH
        self._ach_input = QDoubleSpinBox(self)
        self._ach_input.setRange(0.0, 20.0)
        self._ach_input.setDecimals(2)
        self._ach_input.setSingleStep(0.1)
        self._ach_input.setMinimumWidth(110)
        self._ach_input.valueChanged.connect(self.default_ach_changed.emit)

        # --------------------------------------------------
        # Top form (Te only)
        # --------------------------------------------------
        form_te = QFormLayout()
        form_te.setLabelAlignment(Qt.AlignLeft)
        form_te.addRow("External design temperature (°C)", self._te_input)
        root.addLayout(form_te)

        # --------------------------------------------------
        # Separator line
        # --------------------------------------------------
        sep = QFrame(self)
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        root.addWidget(sep)

        # --------------------------------------------------
        # Defaults form (Ti/Height/ACH)
        # --------------------------------------------------
        form_defaults = QFormLayout()
        form_defaults.setLabelAlignment(Qt.AlignLeft)
        form_defaults.addRow("Default internal temperature (°C)", self._ti_input)
        form_defaults.addRow("Default room height (m)", self._height_input)
        form_defaults.addRow("Default ACH", self._ach_input)
        root.addLayout(form_defaults)

        root.addStretch(1)

    # ------------------------------------------------------------------
    # Adapter-facing setters (observer only)
    # ------------------------------------------------------------------
    def set_external_temp(self, value: Optional[float]) -> None:
        self._te_input.blockSignals(True)
        self._te_input.setValue(value if value is not None else 0.0)
        self._te_input.blockSignals(False)

    def set_default_internal_temp(self, value: Optional[float]) -> None:
        self._ti_input.blockSignals(True)
        self._ti_input.setValue(value if value is not None else 0.0)
        self._ti_input.blockSignals(False)

    def set_default_height(self, value: Optional[float]) -> None:
        self._height_input.blockSignals(True)
        self._height_input.setValue(value if value is not None else 0.0)
        self._height_input.blockSignals(False)

    def set_default_ach(self, value: Optional[float]) -> None:
        self._ach_input.blockSignals(True)
        self._ach_input.setValue(value if value is not None else 0.0)
        self._ach_input.blockSignals(False)