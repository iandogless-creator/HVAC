# ======================================================================
# HVAC/gui_v3/panels/hydronic_control_panel.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QHBoxLayout,
)


# ======================================================================
# HydronicControlPanel
# ======================================================================

class HydronicControlPanel(QWidget):
    """
    Hydronics H-E — Hydronic Control Panel shell.

    Role
    ----
    Intent editor shell only.

    Authority
    ---------
    • No ProjectState access
    • No hydronic calculation
    • No heat-loss calculation
    • No pipe sizing
    • No direct mutation

    Behaviour
    ---------
    Emits intent only.
    Adapter/controller decides what to do with that intent.
    """

    add_emitter_requested = Signal(dict)
    update_emitter_requested = Signal(dict)
    remove_emitter_requested = Signal(str)  # emitter_id
    emitter_selected = Signal(str)  # emitter_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._is_priming = False

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        title = QLabel("Hydronic control")
        title.setStyleSheet("font-weight: 700; padding: 6px;")
        root.addWidget(title)

        form = QFormLayout()

        self._room_combo = QComboBox()
        self._emitter_combo = QComboBox()

        self._emitter_type = QComboBox()

        self._emitter_type.addItem("Radiator", "radiator")
        self._emitter_type.addItem("Towel rail", "towel_rail")
        self._emitter_type.addItem("UFH loop", "ufh_loop")
        self._emitter_type.addItem("Fan convector", "fan_convector")
        self._emitter_type.addItem("Air terminal", "air_terminal")

        self._quantity = QSpinBox()
        self._quantity.setRange(1, 99)
        self._quantity.setValue(1)

        self._design_output_W = QDoubleSpinBox()
        self._design_output_W.setRange(0.0, 100000.0)
        self._design_output_W.setDecimals(1)
        self._design_output_W.setSingleStep(50.0)
        self._design_output_W.setSuffix(" W")
        self._design_output_W.setSpecialValueText("—")

        self._flow_temp_C = QDoubleSpinBox()
        self._flow_temp_C.setRange(0.0, 100.0)
        self._flow_temp_C.setDecimals(1)
        self._flow_temp_C.setSingleStep(1.0)
        self._flow_temp_C.setSuffix(" °C")
        self._flow_temp_C.setValue(70.0)

        self._return_temp_C = QDoubleSpinBox()
        self._return_temp_C.setRange(0.0, 100.0)
        self._return_temp_C.setDecimals(1)
        self._return_temp_C.setSingleStep(1.0)
        self._return_temp_C.setSuffix(" °C")
        self._return_temp_C.setValue(50.0)

        form.addRow("Room:", self._room_combo)
        form.addRow("Existing emitter:", self._emitter_combo)
        form.addRow("Emitter type:", self._emitter_type)
        form.addRow("Quantity:", self._quantity)
        form.addRow("Design output:", self._design_output_W)
        form.addRow("Flow temp:", self._flow_temp_C)
        form.addRow("Return temp:", self._return_temp_C)

        root.addLayout(form)

        button_row = QHBoxLayout()

        self._add_btn = QPushButton("Add emitter")
        self._update_btn = QPushButton("Update selected")
        self._remove_btn = QPushButton("Remove selected")

        button_row.addWidget(self._add_btn)
        button_row.addWidget(self._update_btn)
        button_row.addWidget(self._remove_btn)

        root.addLayout(button_row)

        self._status = QLabel("Hydronic control shell ready.")
        self._status.setStyleSheet("color: #666; padding: 6px;")
        root.addWidget(self._status)

        root.addStretch(1)

        self._add_btn.clicked.connect(self._emit_add_requested)
        self._update_btn.clicked.connect(self._emit_update_requested)
        self._remove_btn.clicked.connect(self._emit_remove_requested)
        self._emitter_combo.currentIndexChanged.connect(
        self._emit_emitter_selected
    )
    # ------------------------------------------------------------------
    # Adapter ingress
    # ------------------------------------------------------------------
    def _emit_emitter_selected(self) -> None:
        if self._is_priming:
            return

        self.emitter_selected.emit(self.current_emitter_id())

    def set_emitter_editor_values(
            self,
            *,
            emitter_type: str,
            design_output_W: float | None,
            flow_temp_C: float | None,
            return_temp_C: float | None,
    ) -> None:
        self._is_priming = True
        try:
            index = self._emitter_type.findData(emitter_type)
            if index >= 0:
                self._emitter_type.setCurrentIndex(index)

            self._design_output_W.setValue(
                0.0 if design_output_W is None else float(design_output_W)
            )

            if flow_temp_C is not None:
                self._flow_temp_C.setValue(float(flow_temp_C))

            if return_temp_C is not None:
                self._return_temp_C.setValue(float(return_temp_C))
        finally:
            self._is_priming = False

    def set_no_existing_emitter(self) -> None:
        """
        Display an honest no-emitter state for the active room.

        The add-emitter editor may still show defaults, but update/remove
        must not imply that an existing emitter is selected.
        """
        self._is_priming = True
        try:
            index = self._emitter_combo.findData("")
            if index >= 0:
                self._emitter_combo.setCurrentIndex(index)
        finally:
            self._is_priming = False

        self._add_btn.setEnabled(True)
        self._update_btn.setEnabled(False)
        self._remove_btn.setEnabled(False)

        self.set_status("No emitter assigned to this room.")

    def set_existing_emitter_available(self) -> None:
        """
        Display edit/remove state for an existing selected emitter.
        """
        self._add_btn.setEnabled(True)
        self._update_btn.setEnabled(True)
        self._remove_btn.setEnabled(True)



    def set_rooms(self, rooms: list[tuple[str, str]]) -> None:
        """
        Observer projection.

        Parameters
        ----------
        rooms:
            list of (room_id, room_label)
        """
        current_room_id = self.current_room_id()

        self._is_priming = True
        self._room_combo.blockSignals(True)
        try:
            self._room_combo.clear()

            for room_id, label in rooms:
                self._room_combo.addItem(label, room_id)

            if current_room_id:
                index = self._room_combo.findData(current_room_id)
                if index >= 0:
                    self._room_combo.setCurrentIndex(index)
        finally:
            self._room_combo.blockSignals(False)
            self._is_priming = False

    def set_active_room(self, room_id: str | None) -> None:
        """
        Select the active/current room without emitting user intent.

        The room_id remains internal authority.
        """
        self._room_combo.blockSignals(True)
        try:
            if not room_id:
                return

            index = self._room_combo.findData(room_id)
            if index >= 0:
                self._room_combo.setCurrentIndex(index)
        finally:
            self._room_combo.blockSignals(False)

    def set_emitters(self, emitters: list[tuple[str, str]]) -> None:
        """
        Observer projection.

        Parameters
        ----------
        emitters:
            list of (emitter_id, label)
        """
        current_emitter_id = self.current_emitter_id()

        self._is_priming = True
        self._emitter_combo.blockSignals(True)
        try:
            self._emitter_combo.clear()

            self._emitter_combo.addItem("—", "")

            for emitter_id, label in emitters:
                self._emitter_combo.addItem(label, emitter_id)

            selected = False

            if current_emitter_id:
                index = self._emitter_combo.findData(current_emitter_id)
                if index >= 0:
                    self._emitter_combo.setCurrentIndex(index)
                    selected = True

            if not selected and emitters:
                self._emitter_combo.setCurrentIndex(1)
        finally:
            self._emitter_combo.blockSignals(False)
            self._is_priming = False

    def set_status(self, message: str) -> None:
        self._status.setText(message or "")

    # ------------------------------------------------------------------
    # Current values
    # ------------------------------------------------------------------

    def current_room_id(self) -> str:
        return str(self._room_combo.currentData() or "")

    def current_emitter_id(self) -> str:
        return str(self._emitter_combo.currentData() or "")

    def _payload(self) -> dict:
        return {
            "room_id": self.current_room_id(),
            "emitter_id": self.current_emitter_id(),
            "emitter_type": str(
            self._emitter_type.currentData()
            or self._emitter_type.currentText()
            or "radiator"
        ),
            "quantity": int(self._quantity.value()),
            "design_output_W": float(self._design_output_W.value()),
            "flow_temp_C": float(self._flow_temp_C.value()),
            "return_temp_C": float(self._return_temp_C.value()),
        }

    # ------------------------------------------------------------------
    # Intent emitters
    # ------------------------------------------------------------------

    def _emit_add_requested(self) -> None:
        if self._is_priming:
            return

        self.add_emitter_requested.emit(self._payload())

    def _emit_update_requested(self) -> None:
        if self._is_priming:
            return

        self.update_emitter_requested.emit(self._payload())

    def _emit_remove_requested(self) -> None:
        if self._is_priming:
            return

        emitter_id = self.current_emitter_id()
        if emitter_id:
            self.remove_emitter_requested.emit(emitter_id)