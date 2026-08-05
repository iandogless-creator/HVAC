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
    QComboBox,
    QFormLayout,
    QFrame,
)


_PIPE_EMISSIVITY_PRESETS_V1 = (
    ("Not set", None),
    ("Painted/coated pipe — 0.95", 0.95),
    ("Dull/oxidised metal — 0.80", 0.80),
    ("Lightly oxidised metal — 0.20", 0.20),
    ("Bright/polished metal — 0.05", 0.05),
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

    # H-S21-A — Hydronic design source inputs
    design_flow_temp_changed = Signal(float)
    design_return_temp_changed = Signal(float)

    # H-S37-B1 — Environment-owned Basic PS default intent
    basic_ps_max_velocity_changed = Signal(float)

    # H-S66-K — Environment-owned universal bare-pipe emissivity.
    # A negative sentinel means explicitly unresolved; 0..1 are valid.
    bare_pipe_emissivity_changed = Signal(float)

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

        # H-S21-A — Hydronic design flow temperature
        self._design_flow_temp_input = QDoubleSpinBox(self)
        self._design_flow_temp_input.setRange(20.0, 95.0)
        self._design_flow_temp_input.setDecimals(1)
        self._design_flow_temp_input.setSingleStep(0.5)
        self._design_flow_temp_input.setMinimumWidth(110)
        self._design_flow_temp_input.setValue(75.0)
        self._design_flow_temp_input.valueChanged.connect(
            self.design_flow_temp_changed.emit
        )

        # H-S21-A — Hydronic design return temperature
        self._design_return_temp_input = QDoubleSpinBox(self)
        self._design_return_temp_input.setRange(20.0, 90.0)
        self._design_return_temp_input.setDecimals(1)
        self._design_return_temp_input.setSingleStep(0.5)
        self._design_return_temp_input.setMinimumWidth(110)
        self._design_return_temp_input.setValue(65.0)
        self._design_return_temp_input.valueChanged.connect(
            self.design_return_temp_changed.emit
        )

        # H-S37-B1 — Basic PS inherited maximum pipe velocity
        self._basic_ps_max_velocity_input = QDoubleSpinBox(self)
        self._basic_ps_max_velocity_input.setRange(0.10, 5.00)
        self._basic_ps_max_velocity_input.setDecimals(2)
        self._basic_ps_max_velocity_input.setSingleStep(0.05)
        self._basic_ps_max_velocity_input.setMinimumWidth(110)
        self._basic_ps_max_velocity_input.setValue(1.00)
        self._basic_ps_max_velocity_input.valueChanged.connect(
            self.basic_ps_max_velocity_changed.emit
        )

        self._bare_pipe_emissivity_input = QComboBox(self)
        self._bare_pipe_emissivity_input.setEditable(True)
        self._bare_pipe_emissivity_input.setMinimumWidth(110)
        for label, emissivity in _PIPE_EMISSIVITY_PRESETS_V1:
            self._bare_pipe_emissivity_input.addItem(label, emissivity)
        self._bare_pipe_emissivity_input.currentIndexChanged.connect(
            self._emit_bare_pipe_emissivity_v1
        )
        line_edit = self._bare_pipe_emissivity_input.lineEdit()
        if line_edit is not None:
            line_edit.editingFinished.connect(
                self._emit_bare_pipe_emissivity_v1
            )

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

        # --------------------------------------------------
        # Hydronic design defaults
        # --------------------------------------------------
        sep_hydronic = QFrame(self)
        sep_hydronic.setFrameShape(QFrame.HLine)
        sep_hydronic.setFrameShadow(QFrame.Sunken)
        root.addWidget(sep_hydronic)

        hydronic_header = QLabel("Hydronic design defaults")
        hydronic_header.setStyleSheet("font-weight: 600;")
        root.addWidget(hydronic_header)

        form_hydronic = QFormLayout()
        form_hydronic.setLabelAlignment(Qt.AlignLeft)
        form_hydronic.addRow(
            "Design flow temperature (°C)",
            self._design_flow_temp_input,
        )
        form_hydronic.addRow(
            "Design return temperature (°C)",
            self._design_return_temp_input,
        )
        form_hydronic.addRow(
            "Basic PS maximum pipe velocity (m/s)",
            self._basic_ps_max_velocity_input,
        )
        root.addLayout(form_hydronic)

        sep_pipe_heat_loss = QFrame(self)
        sep_pipe_heat_loss.setFrameShape(QFrame.HLine)
        sep_pipe_heat_loss.setFrameShadow(QFrame.Sunken)
        root.addWidget(sep_pipe_heat_loss)

        pipe_heat_loss_header = QLabel("Pipe heat-loss defaults")
        pipe_heat_loss_header.setStyleSheet("font-weight: 600;")
        root.addWidget(pipe_heat_loss_header)

        pipe_heat_loss_note = QLabel(
            "Project default for bare-pipe surface radiation. It is not an "
            "air property; committed sections may override it locally. "
            "Choose a representative finish or type an explicit value."
        )
        pipe_heat_loss_note.setWordWrap(True)
        root.addWidget(pipe_heat_loss_note)

        form_pipe_heat_loss = QFormLayout()
        form_pipe_heat_loss.setLabelAlignment(Qt.AlignLeft)
        form_pipe_heat_loss.addRow(
            "Universal bare-pipe emissivity (0–1)",
            self._bare_pipe_emissivity_input,
        )
        root.addLayout(form_pipe_heat_loss)

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

    def set_design_flow_temp(self, value: Optional[float]) -> None:
        self._design_flow_temp_input.blockSignals(True)
        self._design_flow_temp_input.setValue(value if value is not None else 75.0)
        self._design_flow_temp_input.blockSignals(False)

    def set_design_return_temp(self, value: Optional[float]) -> None:
        self._design_return_temp_input.blockSignals(True)
        self._design_return_temp_input.setValue(value if value is not None else 65.0)
        self._design_return_temp_input.blockSignals(False)

    def set_basic_ps_max_velocity(self, value: Optional[float]) -> None:
        self._basic_ps_max_velocity_input.blockSignals(True)
        self._basic_ps_max_velocity_input.setValue(
            value if value is not None else 1.0
        )
        self._basic_ps_max_velocity_input.blockSignals(False)

    def set_bare_pipe_emissivity(self, value: Optional[float]) -> None:
        self._bare_pipe_emissivity_input.blockSignals(True)
        target = None if value is None else float(value)
        matched_index = -1
        for index in range(self._bare_pipe_emissivity_input.count()):
            candidate = self._bare_pipe_emissivity_input.itemData(index)
            if candidate is None and target is None:
                matched_index = index
                break
            if candidate is not None and target is not None:
                if abs(float(candidate) - target) < 1.0e-12:
                    matched_index = index
                    break
        if matched_index >= 0:
            self._bare_pipe_emissivity_input.setCurrentIndex(matched_index)
        else:
            self._bare_pipe_emissivity_input.setCurrentIndex(-1)
            self._bare_pipe_emissivity_input.setEditText(f"{target:g}")
        self._bare_pipe_emissivity_input.blockSignals(False)

    def _emit_bare_pipe_emissivity_v1(self, *_args) -> None:
        combo = self._bare_pipe_emissivity_input
        index = combo.currentIndex()
        if index >= 0:
            value = combo.itemData(index)
            self.bare_pipe_emissivity_changed.emit(
                -0.01 if value is None else float(value)
            )
            return
        try:
            value = float(str(combo.currentText() or "").strip())
        except ValueError:
            return
        if 0.0 <= value <= 1.0:
            self.bare_pipe_emissivity_changed.emit(value)
