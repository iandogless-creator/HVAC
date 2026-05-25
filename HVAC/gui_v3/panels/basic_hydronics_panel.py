# ======================================================================
# HVAC/gui_v3/panels/basic_hydronics_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional, Any

from PySide6.QtCore import Qt, Signal
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
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
        # Basic PS topology section projection
        # --------------------------------------------------------------
        self._ps_sections_table = QTableWidget(0, 7)
        self._ps_sections_table.setMinimumHeight(160)
        self._ps_sections_table.setHorizontalHeaderLabels(
            [
                "Order",
                "From",
                "To",
                "Q carried",
                "Flow kg/s",
                "Index",
                "Terminal",
            ]
        )

        self._ps_sections_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._ps_sections_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._ps_sections_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._ps_sections_table.verticalHeader().setVisible(False)
        self._ps_sections_table.setAlternatingRowColors(True)

        ps_header = self._ps_sections_table.horizontalHeader()
        ps_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(1, QHeaderView.Stretch)
        ps_header.setSectionResizeMode(2, QHeaderView.Stretch)
        ps_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        root.addWidget(QLabel("Basic PS topology sections"))
        root.addWidget(self._ps_sections_table)

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

    def set_basic_ps_sections(self, rows: list[dict[str, Any]]) -> None:
        """
        Replace read-only Basic PS topology section rows.

        Expected row keys:
        - order
        - from_label
        - to_room_label
        - carried_heat_W
        - carried_flow_kg_s
        - is_index_room
        - is_terminal
        """

        self._ps_sections_table.setRowCount(0)

        for row_data in rows:
            row_index = self._ps_sections_table.rowCount()
            self._ps_sections_table.insertRow(row_index)

            order = row_data.get("order", "")
            from_label = str(row_data.get("from_label", "") or "")
            to_room_label = str(row_data.get("to_room_label", "") or "")
            carried_heat_W = float(row_data.get("carried_heat_W") or 0.0)
            carried_flow_kg_s = float(row_data.get("carried_flow_kg_s") or 0.0)
            is_index_room = bool(row_data.get("is_index_room", False))
            is_terminal = bool(row_data.get("is_terminal", False))

            values = [
                str(order),
                from_label,
                to_room_label,
                f"{carried_heat_W:.1f} W",
                f"{carried_flow_kg_s:.4f}",
                "⚑" if is_index_room else "",
                "Terminal" if is_terminal else "",
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col in (0, 3, 4, 5, 6):
                    item.setTextAlignment(Qt.AlignCenter)

                self._ps_sections_table.setItem(row_index, col, item)

        self._ps_sections_table.resizeRowsToContents()

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

    def clear_basic_ps_sections(self) -> None:
        self._ps_sections_table.setRowCount(0)

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