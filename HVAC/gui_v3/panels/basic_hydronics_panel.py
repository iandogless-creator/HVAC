# ======================================================================
# HVAC/gui_v3/panels/basic_hydronics_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QGroupBox,
)


# ======================================================================
# BasicHydronicsPanel
# ======================================================================

class BasicHydronicsPanel(QWidget):
    """
    GUI v3 — Basic Hydronics Panel

    Role
    ----
    User-editable first-pass hydronic sizing assumptions.

    Authority
    ---------
    • Emits user intent only
    • Does not mutate ProjectState directly
    • Does not perform pipe sizing
    • Does not perform pressure-loss calculation
    • Does not call Colebrook or Darcy-Weisbach

    Basic method
    ------------
    Stores/edit assumptions for:

        nominal pipework dp ≈ index length × nominal pressure gradient

    The adapter owns ProjectState read/write.
    """

    intent_committed = Signal(dict)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_priming = False

        root = QVBoxLayout(self)

        title = QLabel("Basic Hydronics")
        title.setObjectName("BasicHydronicsTitle")
        root.addWidget(title)

        # --------------------------------------------------------------
        # Intent group
        # --------------------------------------------------------------
        intent_box = QGroupBox("First-pass sizing intent")
        intent_layout = QFormLayout(intent_box)

        self._basis_mode = QComboBox()
        self._basis_mode.addItems(
            [
                "INDEX_LENGTH",
                "BASIC_SECTIONS",
                "ADVANCED_PROPORTIONING",
            ]
        )
        intent_layout.addRow("Basis mode:", self._basis_mode)

        self._index_room = QComboBox()
        intent_layout.addRow("Index room:", self._index_room)

        self._index_emitter = QComboBox()
        intent_layout.addRow("Index emitter:", self._index_emitter)

        self._total_index_length = QDoubleSpinBox()
        self._total_index_length.setRange(0.0, 10000.0)
        self._total_index_length.setDecimals(2)
        self._total_index_length.setSuffix(" m")
        intent_layout.addRow("Total index length:", self._total_index_length)

        self._nominal_gradient = QDoubleSpinBox()
        self._nominal_gradient.setRange(0.0, 100000.0)
        self._nominal_gradient.setDecimals(2)
        self._nominal_gradient.setSuffix(" Pa/m")
        intent_layout.addRow("Nominal Δp/m:", self._nominal_gradient)

        self._length_source = QComboBox()
        self._length_source.addItems(["unset", "user", "default", "derived"])
        intent_layout.addRow("Length source:", self._length_source)

        self._pressure_gradient_source = QComboBox()
        self._pressure_gradient_source.addItems(
            ["unset", "user", "default", "derived"]
        )
        intent_layout.addRow("Gradient source:", self._pressure_gradient_source)

        root.addWidget(intent_box)

        # --------------------------------------------------------------
        # Derived display group
        # --------------------------------------------------------------
        derived_box = QGroupBox("Read-only derived allowance")
        derived_layout = QFormLayout(derived_box)

        self._derived_allowance = QLabel("— Pa")
        derived_layout.addRow("Nominal pipework allowance:", self._derived_allowance)

        root.addWidget(derived_box)

        # --------------------------------------------------------------
        # Notes
        # --------------------------------------------------------------
        notes_box = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_box)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText(
            "Basic hydronic sizing notes. No pipe sizing is performed here."
        )
        notes_layout.addWidget(self._notes)

        root.addWidget(notes_box)

        # --------------------------------------------------------------
        # Actions
        # --------------------------------------------------------------
        action_row = QHBoxLayout()
        action_row.addStretch(1)

        self._commit_button = QPushButton("Apply Basic Hydronics Intent")
        action_row.addWidget(self._commit_button)

        root.addLayout(action_row)
        root.addStretch(1)

        # --------------------------------------------------------------
        # Signals
        # --------------------------------------------------------------
        self._commit_button.clicked.connect(self._emit_commit)

        self._total_index_length.valueChanged.connect(
            self._refresh_local_derived_display
        )
        self._nominal_gradient.valueChanged.connect(
            self._refresh_local_derived_display
        )

    # ==================================================================
    # Priming API — called by adapter
    # ==================================================================
    def set_room_options(
        self,
        options: list[tuple[str, str]],
        selected_room_id: Optional[str] = None,
    ) -> None:
        """
        options: [(room_id, display_name), ...]
        """
        self._is_priming = True
        try:
            self._index_room.clear()

            for room_id, display_name in options:
                self._index_room.addItem(display_name, room_id)

            if selected_room_id:
                index = self._index_room.findData(selected_room_id)
                if index >= 0:
                    self._index_room.setCurrentIndex(index)
        finally:
            self._is_priming = False

    def set_emitter_options(
        self,
        options: list[tuple[str, str]],
        selected_emitter_id: Optional[str] = None,
    ) -> None:
        """
        options: [(emitter_id, display_name), ...]
        """
        self._is_priming = True
        try:
            self._index_emitter.clear()

            for emitter_id, display_name in options:
                self._index_emitter.addItem(display_name, emitter_id)

            if selected_emitter_id:
                index = self._index_emitter.findData(selected_emitter_id)
                if index >= 0:
                    self._index_emitter.setCurrentIndex(index)
        finally:
            self._is_priming = False

    def prime_intent(self, intent: Optional[dict]) -> None:
        """
        Prime panel from adapter-owned DTO projection.

        The panel receives a plain dict to avoid owning ProjectState models.
        """
        self._is_priming = True
        try:
            intent = intent or {}

            self._set_combo_text(
                self._basis_mode,
                str(intent.get("basis_mode") or "INDEX_LENGTH"),
            )

            self._set_optional_float(
                self._total_index_length,
                intent.get("total_index_length_m"),
            )
            self._set_optional_float(
                self._nominal_gradient,
                intent.get("nominal_pressure_gradient_Pa_per_m"),
            )

            self._set_combo_text(
                self._length_source,
                str(intent.get("length_source") or "unset"),
            )
            self._set_combo_text(
                self._pressure_gradient_source,
                str(intent.get("pressure_gradient_source") or "unset"),
            )

            self._notes.setPlainText(str(intent.get("notes") or ""))

            index_room_id = intent.get("index_room_id")
            if index_room_id:
                index = self._index_room.findData(index_room_id)
                if index >= 0:
                    self._index_room.setCurrentIndex(index)

            index_emitter_id = intent.get("index_emitter_id")
            if index_emitter_id:
                index = self._index_emitter.findData(index_emitter_id)
                if index >= 0:
                    self._index_emitter.setCurrentIndex(index)

        finally:
            self._is_priming = False

        self._refresh_local_derived_display()

    # ==================================================================
    # Display helpers
    # ==================================================================
    def set_derived_allowance_Pa(self, value: Optional[float]) -> None:
        if value is None:
            self._derived_allowance.setText("— Pa")
            return

        self._derived_allowance.setText(f"{value:.1f} Pa")

    def _refresh_local_derived_display(self) -> None:
        """
        Local display only.

        This is not real pressure-loss calculation.
        It merely previews the basic nominal allowance:
            length × nominal Pa/m
        """
        length = self._total_index_length.value()
        gradient = self._nominal_gradient.value()

        if length <= 0.0 or gradient <= 0.0:
            self.set_derived_allowance_Pa(None)
            return

        self.set_derived_allowance_Pa(length * gradient)

    def current_index_room_id(self) -> str:
        return str(self._index_room.currentData() or "")

    def current_index_emitter_id(self) -> str:
        return str(self._index_emitter.currentData() or "")

    # ==================================================================
    # Intent emission
    # ==================================================================
    def _emit_commit(self) -> None:
        if self._is_priming:
            return

        payload = {
            "basis_mode": self._basis_mode.currentText(),
            "index_room_id": self._index_room.currentData(),
            "index_emitter_id": self._index_emitter.currentData(),
            "total_index_length_m": self._optional_spin_value(
                self._total_index_length
            ),
            "nominal_pressure_gradient_Pa_per_m": self._optional_spin_value(
                self._nominal_gradient
            ),
            "length_source": self._length_source.currentText(),
            "pressure_gradient_source": self._pressure_gradient_source.currentText(),
            "notes": self._notes.toPlainText(),
        }

        self.intent_committed.emit(payload)

    # ==================================================================
    # Small helpers
    # ==================================================================
    @staticmethod
    def _optional_spin_value(spin: QDoubleSpinBox) -> Optional[float]:
        value = float(spin.value())
        if value <= 0.0:
            return None
        return value

    @staticmethod
    def _set_optional_float(spin: QDoubleSpinBox, value: object) -> None:
        try:
            if value is None:
                spin.setValue(0.0)
            else:
                spin.setValue(float(value))
        except (TypeError, ValueError):
            spin.setValue(0.0)

    @staticmethod
    def _set_combo_text(combo: QComboBox, value: str) -> None:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)