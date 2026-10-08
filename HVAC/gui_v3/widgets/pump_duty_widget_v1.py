"""H-S73-B observer and input editor; all readiness/calculation lives downstream."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


class PumpDutyWidgetV1(QWidget):
    apply_requested = Signal(dict)
    accept_requested = Signal(str)
    clear_requested = Signal()
    withdraw_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rendering = False
        self._dirty = False
        self._owner = None
        self._basis = object()
        self._route_ids = []
        self._point_ids = []
        self._fingerprint = ""
        root = QVBoxLayout(self)
        self.status = QLabel("Apply the preliminary fluid/common-loss basis first.", self)
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.PlainText)
        root.addWidget(self.status)
        note = QLabel("Enter additional equipment losses and operating Kv, then Apply. "
                      "Accept duty after reviewing the complete result.", self)
        note.setWordWrap(True)
        root.addWidget(note)
        self.routes = self._table(("Route", "Pipe Pa", "Equipment Pa", "Valve Pa", "Total Pa", "Residual Pa", "Equipment basis"))
        self.routes.setToolTip("Enter additional equipment loss at design flow for EVERY route, including 0 if none. "
                               "Exclude pipework, Local K, valves shown below and the preliminary common-loss allowance. "
                               "Shared additional equipment belongs once in each affected route. Residual is unallocated resistance to the highest route total.")
        self.routes.itemChanged.connect(self._edited)
        root.addWidget(self.routes)
        self.points = self._table(("Valve point", "kg/s", "Kvs", "Operating Kv", "Kvs Pa", "Valve Pa", "Old allocation Pa"))
        self.points.setToolTip("Committed Kvs is a rated capacity, not an operating setting. Enter a reviewed operating Kv ≤ Kvs. "
                               "A blank uses Kvs for preview only. Shared valves use total committed point flow, once per governed route. "
                               "Old allocation is comparison evidence and is NOT added to pump pressure.")
        self.points.itemChanged.connect(self._edited)
        root.addWidget(self.points)
        self.review_note = QLineEdit(self)
        self.review_note.setPlaceholderText("Review note")
        self.review_note.setToolTip("Record the additional equipment, operating Kv, control assumptions and fluid basis reviewed. "
                                    "No valve setting, pump product or pump curve is selected here.")
        self.review_note.textEdited.connect(self._edited)
        root.addWidget(self.review_note)
        self.reviewed = QCheckBox("Basis reviewed", self)
        self.reviewed.setToolTip("Confirm equipment coverage, no duplicated losses, operating Kv/control requirements and the liquid density basis. "
                                 "Kv arithmetic assumes non-cavitating liquid flow; upstream pipe friction is not recalculated.")
        self.reviewed.toggled.connect(self._edited)
        root.addWidget(self.reviewed)
        actions = QHBoxLayout()
        self.apply_button = QPushButton("Apply", self)
        self.apply_button.setToolTip("Save the route/valve inputs and invalidate previous duty acceptance")
        self.accept_button = QPushButton("Accept duty", self)
        self.accept_button.setToolTip("Explicitly accept the displayed required flow and head, including the reviewed common loss and head margin. "
                                      "This is a design requirement; no manufacturer pump curve, efficiency, NPSH or product is verified.")
        self.withdraw_button = QPushButton("Withdraw", self)
        self.withdraw_button.setToolTip("Withdraw final duty acceptance, retaining the input basis")
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.setToolTip("Clear the detailed duty basis and its acceptance")
        for button in (self.apply_button, self.accept_button, self.withdraw_button, self.clear_button):
            actions.addWidget(button)
        actions.addStretch()
        root.addLayout(actions)
        self.message = QLabel(self)
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.PlainText)
        root.addWidget(self.message)
        root.addStretch()
        self.apply_button.clicked.connect(lambda: self.apply_requested.emit(self.payload_v1()))
        self.accept_button.clicked.connect(lambda: self.accept_requested.emit(self._fingerprint))
        self.clear_button.clicked.connect(self.clear_requested.emit)
        self.withdraw_button.clicked.connect(self.withdraw_requested.emit)
        self.accept_button.setEnabled(False)

    def _table(self, columns):
        table = QTableWidget(0, len(columns), self)
        table.setHorizontalHeaderLabels(columns)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setStretchLastSection(True)
        table.setMinimumWidth(0)
        table.setMinimumHeight(125)
        return table

    def _edited(self, *_):
        if not self._rendering:
            self._dirty = True
            self.accept_button.setEnabled(False)
            self.message.setText("Unapplied edits — saved duty is unchanged. Apply before accepting.")

    @staticmethod
    def _number(value):
        return "—" if value is None else f"{value:.6g}"

    @staticmethod
    def _put(table, row, column, text, *, editable=False, tooltip=""):
        item = QTableWidgetItem(str(text))
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setToolTip(tooltip or str(text))
        table.setItem(row, column, item)

    def payload_v1(self):
        return {
            "routes": [{"route_id": key, "pressure_Pa": self.routes.item(i, 2).text(),
                        "source_note": self.routes.item(i, 6).text()} for i, key in enumerate(self._route_ids)],
            "points": [{"point_id": key, "operating_kv": self.points.item(i, 3).text()}
                       for i, key in enumerate(self._point_ids)],
            "review_note": self.review_note.text(), "reviewed": self.reviewed.isChecked(),
        }

    def reload_basis_v1(self):
        self._basis = object()

    def present(self, *, result, basis, owner_token, has_acceptance):
        reset = owner_token != self._owner or basis != self._basis
        old = self.payload_v1() if not reset else {"routes": [], "points": []}
        saved = basis or {}
        route_inputs = {r["route_id"]: r for r in (saved.get("routes", []) if reset else old["routes"])}
        point_inputs = {p["point_id"]: p for p in (saved.get("points", []) if reset else old["points"])}
        self._rendering = True
        try:
            self._route_ids = [r.route_id for r in result.routes]
            self._point_ids = [p.point_id for p in result.points]
            self.routes.setRowCount(len(result.routes))
            for i, row in enumerate(result.routes):
                inputs = route_inputs.get(row.route_id, {})
                values = (row.label, self._number(row.pipework_Pa), inputs.get("pressure_Pa", ""),
                          self._number(row.valve_Pa), self._number(row.total_Pa),
                          "—" if row.residual_Pa is None else f"{row.residual_Pa:.3f}",
                          inputs.get("source_note", ""))
                for col, value in enumerate(values):
                    self._put(self.routes, i, col, value, editable=col in (2, 6),
                              tooltip=row.route_id if col == 0 else "")
            self.points.setRowCount(len(result.points))
            for i, row in enumerate(result.points):
                kv = point_inputs.get(row.point_id, {}).get("operating_kv")
                values = (row.label, self._number(row.mass_flow_kg_s), self._number(row.kvs),
                          "" if kv is None else str(kv), self._number(row.rated_loss_Pa),
                          self._number(row.operating_loss_Pa), self._number(row.allocated_Pa))
                for col, value in enumerate(values):
                    self._put(self.points, i, col, value, editable=col == 3,
                              tooltip=f"{row.point_id}\nRoutes: {', '.join(row.route_ids)}" if col == 0 else "")
            if reset:
                self.review_note.setText(saved.get("review_note", ""))
                self.reviewed.setChecked(saved.get("reviewed") is True)
                self._dirty = False
                self.message.clear()
            self._owner, self._basis = owner_token, basis
            self._fingerprint = result.basis_fingerprint
            self.accept_button.setEnabled(result.acceptance_ready and not self._dirty and not result.accepted)
            self.withdraw_button.setEnabled(has_acceptance)
            if result.ready:
                n = result.numbers
                label = "Accepted required design duty" if result.accepted else "Required duty preview"
                status = f"{label}: {n.flow_m3_h:.6g} m³/h · {n.pressure_Pa:.6g} Pa · {n.head_m:.6g} m"
                if has_acceptance and not result.accepted:
                    status += "\nPrevious duty acceptance is stale."
                if result.acceptance_blockers:
                    status += "\n" + "\n".join(result.acceptance_blockers)
            else:
                messages = (
                    "Review and apply the basis in Preliminary first."
                    if message == "Enter and apply an explicit preview basis; no density or allowances are assumed."
                    else message for message in result.blockers
                )
                status = "Duty blocked:\n" + "\n".join(messages)
                if has_acceptance:
                    status += "\nPrevious duty acceptance is not current."
            self.status.setText(status)
        finally:
            self._rendering = False
