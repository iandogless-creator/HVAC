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
            "Preview from committed pipework. Review equipment and valve losses in Duty.", self)
        note.setWordWrap(True)
        layout.addWidget(note)
        self.summary = self._table(("Quantity / basis", "Value"))
        layout.addWidget(self.summary)
        self.routes = self._table(("Route ID", "Route", "Pipework Δp (Pa)"))
        layout.addWidget(self.routes)
        form = QFormLayout()
        self.inputs = {}
        for key, label, help_text in (
            ("density_kg_m3", "Density (kg/m³)", "Inherited from the committed shared water basis; review temperatures in Environment."),
            ("additional_common_loss_Pa", "Additional common loss (Pa)", "Extra loss shared by every route. Exclude losses already counted. 0 means no additional loss."),
            ("head_margin_percent", "Head margin (%)", "Allowance applied to pipework pressure plus additional common loss. 0 means no added margin. Flow is unchanged."),
            ("source_note", "Basis note", "The water source is shown below. Record any additional common loss or head margin here."),
        ):
            editor = QLineEdit(self)
            editor.setToolTip(help_text)
            editor.setPlaceholderText({
                "density_kg_m3": "Hydraulic fluid density",
                "additional_common_loss_Pa": "0 — no additional loss",
                "head_margin_percent": "0 — no added margin",
                "source_note": "Explain any added allowance",
            }[key])
            if key in {"additional_common_loss_Pa", "head_margin_percent"}:
                editor.setText("0")
            form.addRow(label, editor)
            self.inputs[key] = editor
        self.density_source = QLabel(self)
        self.density_source.setWordWrap(True)
        self.density_source.setTextFormat(Qt.PlainText)
        form.addRow("", self.density_source)
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
            {**{key: editor.text() for key, editor in self.inputs.items()},
             "density_kg_m3": self._rendered_defaults.get("density_kg_m3")}
        ))
        self.clear_button.clicked.connect(self.clear_requested.emit)
        self._rendered_defaults = {}
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

    @staticmethod
    def _input_text_v1(value):
        return "" if value is None else str(value)

    def present(self, *, status, summary, routes, basis, owner_token, default_basis=None):
        self.status.setText(status)
        self._rows(self.summary, summary)
        self._rows(self.routes, routes)
        defaults = dict(default_basis or {})
        defaults.setdefault("additional_common_loss_Pa", 0)
        defaults.setdefault("head_margin_percent", 0)
        # Ordinary refreshes preserve unfinished typing. A project swap or an
        # explicit Apply/Clear restores that project's saved basis or defaults.
        if owner_token != self._rendered_owner or basis != self._rendered_basis:
            values = basis if basis is not None else defaults
            for key, editor in self.inputs.items():
                editor.setText(self._input_text_v1(values.get(key)))
            self._rendered_owner = owner_token
            self._rendered_basis = dict(basis) if basis is not None else None
            self.message.clear()
        elif basis is None and defaults != self._rendered_defaults:
            # E.g. a first commit makes density available. Only update fields
            # still displaying the previous suggestion; preserve edited fields.
            for key, editor in self.inputs.items():
                previous = self._input_text_v1(self._rendered_defaults.get(key))
                if editor.text() == previous:
                    editor.setText(self._input_text_v1(defaults.get(key)))
        self._rendered_defaults = defaults
        self.inputs["density_kg_m3"].setReadOnly(True)
        density = defaults.get("density_kg_m3")
        self.inputs["density_kg_m3"].setText("" if density is None else f"{density:.3f}")
        self.inputs["density_kg_m3"].setToolTip(
            "From the committed shared water basis. Change design flow/return in Environment, "
            "then recalculate, review and Recommit Proportioning.")
        self.density_source.setText(defaults.get("fluid_status", "Commit the shared water basis first."))
