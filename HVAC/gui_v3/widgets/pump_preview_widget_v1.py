"""Compact observer/intent editor. No engineering calculation or readiness."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)


class PumpPreviewWidgetV1(QWidget):
    apply_requested = Signal(dict)
    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        heading = QLabel("Pump duty — committed-basis preview", self)
        heading.setStyleSheet("font-weight: bold; font-size: 15px;")
        layout.addWidget(heading)
        self.status = QLabel("Awaiting committed hydraulic evidence", self)
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.PlainText)
        layout.addWidget(self.status)
        note = QLabel(
            "Uses the committed snapshot, not live edits. Pipework and Local K losses "
            "include the shared mains once. This preview does not yet verify route-specific "
            "equipment losses or final Kv/Kvs pressure-loss consequences. A finished "
            "parameter-based design, including Kv/Kvs, does not require a manufacturer or model.", self)
        note.setWordWrap(True)
        layout.addWidget(note)
        self.summary = self._table(("Quantity / basis", "Value"))
        layout.addWidget(self.summary)
        self.routes = self._table(("Route ID", "Route", "Pipework Δp (Pa)"))
        layout.addWidget(self.routes)
        form = QFormLayout()
        self.inputs = {}
        for key, label, help_text in (
            ("density_kg_m3", "Density (kg/m³)", "Density for flow/head conversion at the operating temperature. Must match the reviewed hydraulic fluid basis; existing pipe friction is not recalculated. No water default."),
            ("additional_common_loss_Pa", "Common loss (Pa)", "Additional loss common to every circuit, e.g. a heat source. Exclude losses already in the committed routes. Enter 0 explicitly if none."),
            ("head_margin_percent", "Head margin (%)", "Applied to pipework pressure plus common loss. Enter 0 explicitly for no margin. Flow is not increased."),
            ("source_note", "Basis note", "Record fluid, temperature, density source and what the common loss and margin include."),
        ):
            editor = QLineEdit(self)
            editor.setToolTip(help_text)
            editor.setPlaceholderText(help_text if key == "source_note" else "Required — no default")
            form.addRow(label, editor)
            self.inputs[key] = editor
        layout.addLayout(form)
        actions = QHBoxLayout()
        self.apply_button = QPushButton("Apply basis", self)
        self.apply_button.setToolTip("Save these assumptions against the currently displayed committed snapshot. This does not accept final pump duty.")
        self.clear_button = QPushButton("Clear basis", self)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.clear_button)
        actions.addStretch()
        layout.addLayout(actions)
        self.message = QLabel(self)
        self.message.setTextFormat(Qt.PlainText)
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        for editor in self.inputs.values():
            editor.textEdited.connect(lambda _text: self.message.setText(
                "Unapplied edits — displayed duty still uses the saved basis."
            ))
        self.apply_button.clicked.connect(lambda: self.apply_requested.emit(
            {key: editor.text() for key, editor in self.inputs.items()}
        ))
        self.clear_button.clicked.connect(self.clear_requested.emit)
        self._rendered_owner = None
        self._rendered_basis = object()
        layout.addStretch()

    def _table(self, columns):
        table = QTableWidget(0, len(columns), self)
        table.setHorizontalHeaderLabels(columns)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return table

    @staticmethod
    def _rows(table, rows):
        table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                table.setItem(row, column, item)
        row_height = max(26, table.fontMetrics().height() + 8)
        for row in range(len(rows)):
            table.setRowHeight(row, row_height)
        visible_rows = len(rows) if table.columnCount() == 2 else min(5, max(2, len(rows)))
        table.setFixedHeight(table.horizontalHeader().height() + visible_rows * row_height + 4)

    def present(self, *, status, summary, routes, basis, owner_token):
        self.status.setText(status)
        self._rows(self.summary, summary)
        self._rows(self.routes, routes)
        # Ordinary refreshes must not overwrite the user's unfinished typing.
        if owner_token != self._rendered_owner or basis != self._rendered_basis:
            for key, editor in self.inputs.items():
                value = basis.get(key) if basis else None
                editor.setText("" if value is None else str(value))
            self._rendered_owner = owner_token
            self._rendered_basis = basis
            self.message.clear()
