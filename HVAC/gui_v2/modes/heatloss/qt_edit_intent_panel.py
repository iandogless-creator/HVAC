"""
qt_edit_intent_panel.py
-----------------------

HVACgooee — QT Edit / Design Intent Panel (v1)

• GUI-only
• DTO-driven
• No calculations
• Explicit user intent only
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
)

from HVAC_legacy.heatloss.dto.room_heatloss_row_dto import RoomHeatLossRowDTO


class QtEditIntentPanel(QWidget):
    """
    Panel allowing explicit editing of effective QT (override),
    while always showing calculated QT.
    """

    # Emitted when user intent changes (override / notes)
    intent_changed = Signal(str)  # room_id

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._row: Optional[RoomHeatLossRowDTO] = None

        self._build_ui()
        self._wire_signals()
        self._set_enabled(False)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.setWindowTitle("Design Intent")

        title = QLabel("Design Intent (QT)")
        title.setStyleSheet("font-weight: bold;")

        # Calculated QT (read-only)
        self.calc_qt_label = QLabel("— W")
        self.calc_qt_label.setStyleSheet("color: #666;")

        # Effective QT (editable)
        self.override_qt_edit = QLineEdit()
        self.override_qt_edit.setPlaceholderText("No override")
        self.override_qt_edit.setClearButtonEnabled(True)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Design intent / rationale…")
        self.notes_edit.setFixedHeight(60)

        # Clear override button
        self.clear_btn = QPushButton("Clear Override")

        # Layout
        form = QFormLayout()
        form.addRow("Calculated QT:", self.calc_qt_label)
        form.addRow("Effective QT:", self.override_qt_edit)
        form.addRow("Notes:", self.notes_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.clear_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addLayout(btn_row)
        layout.addStretch()

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------

    def _wire_signals(self):
        self.override_qt_edit.editingFinished.connect(
            self._on_override_changed
        )
        self.notes_edit.textChanged.connect(
            self._on_notes_changed
        )
        self.clear_btn.clicked.connect(self._on_clear_override)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def bind_row(self, row: Optional[RoomHeatLossRowDTO]):
        """
        Bind panel to a room row.
        Pass None to clear / disable.
        """
        self._row = row

        if row is None:
            self._set_enabled(False)
            self._clear_fields()
            return

        self._set_enabled(True)
        self._refresh_from_row()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh_from_row(self):
        assert self._row is not None

        self.calc_qt_label.setText(f"{self._row.qt_calc_w:.0f} W")

        if self._row.qt_override_w is None:
            self.override_qt_edit.setText("")
        else:
            self.override_qt_edit.setText(
                f"{self._row.qt_override_w:.0f}"
            )

        self.notes_edit.blockSignals(True)
        self.notes_edit.setPlainText(self._row.notes)
        self.notes_edit.blockSignals(False)

    def _clear_fields(self):
        self.calc_qt_label.setText("— W")
        self.override_qt_edit.setText("")
        self.notes_edit.setPlainText("")

    def _set_enabled(self, enabled: bool):
        self.override_qt_edit.setEnabled(enabled)
        self.notes_edit.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_override_changed(self):
        if self._row is None:
            return

        text = self.override_qt_edit.text().strip()

        if text == "":
            self._row.qt_override_w = None
        else:
            try:
                self._row.qt_override_w = float(text)
            except ValueError:
                # Revert to previous value if invalid
                self._refresh_from_row()
                return

        self.intent_changed.emit(self._row.room_id)

    def _on_notes_changed(self):
        if self._row is None:
            return

        self._row.notes = self.notes_edit.toPlainText()
        self.intent_changed.emit(self._row.room_id)

    def _on_clear_override(self):
        if self._row is None:
            return

        self._row.qt_override_w = None
        self._refresh_from_row()
        self.intent_changed.emit(self._row.room_id)
