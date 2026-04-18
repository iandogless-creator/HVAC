# ======================================================================
# HVAC/gui_v3/panels/heat_loss_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional, Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QFrame,
    QGridLayout,
)

DT_COLUMN = 3

# ======================================================================
# ClickableLabel
# ======================================================================

class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)


# ======================================================================
# HeatLossPanelV3
# ======================================================================

class HeatLossPanelV3(QWidget):
    """
    Heat-Loss worksheet panel (GUI v3)

    Authority
    ---------
    • Pure projection / display panel
    • Emits user intent only
    • Does NOT mutate ProjectState
    • Does NOT calculate physics
    """

    # ------------------------------------------------------------------
    # Signals (adapter contracts)
    # ------------------------------------------------------------------
    run_requested = Signal()
    surface_focus_requested = Signal(object)          # surface_id | None
    open_uvalues_requested = Signal(object)          # surface_id | None
    ignore_readiness_changed = Signal(bool)
    cell_selected = Signal(int)                      # row index
    geometry_edit_requested = Signal()
    ach_edit_requested = Signal()
    worksheet_cell_edit_requested = Signal(int, int)
    adjacency_edit_requested = Signal(str)  # surface_id

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_room_id: Optional[str] = None
        self._worksheet_table: Optional[QTableWidget] = None
        self._row_metas: list[WorksheetRowMeta] = []
        self._build_ui()
        self._wire_signals()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # --------------------------------------------------
        # Header
        # --------------------------------------------------
        self._header = QLabel("Heat Loss — No room selected")
        root.addWidget(self._header)
        self._status_label = QLabel("")

        self._ti_label = QLabel("Ti: — °C")
        self._ti_label.setStyleSheet("color: #555;")  # subtle grey like geometry
        root.addWidget(self._ti_label)
        root.addWidget(self._status_label)

        # --------------------------------------------------------------
        # Geometry summary
        # --------------------------------------------------------------
        self._geometry_frame = QFrame(self)
        self._geometry_frame.setFrameShape(QFrame.StyledPanel)

        geometry_layout = QGridLayout(self._geometry_frame)
        geometry_layout.setContentsMargins(8, 6, 8, 6)

        self._geometry_label = ClickableLabel("Geometry: —")
        self._geometry_label.setStyleSheet(
            "background: rgba(80,120,180,0.12); padding: 4px;"
        )

        geometry_layout.addWidget(self._geometry_label, 0, 0)
        root.addWidget(self._geometry_frame)

        # --------------------------------------------------------------
        # Canonical worksheet
        # --------------------------------------------------------------
        self._table = QTableWidget(self)
        self._worksheet_table = self._table
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            [
                "Element",
                "A (m²)",
                "U (W/m²·K)",
                "ΔT (K)",
                "Qf (W)",
            ]
        )

        self._table.setRowCount(0)
        self._table.setMinimumHeight(160)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionResizeMode(0, QHeaderView.Stretch)

        for col in (1, 2, 3, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        root.addWidget(self._table)

        # --------------------------------------------------------------
        # Results frame
        # --------------------------------------------------------------
        self._results_frame = QFrame(self)
        self._results_frame.setFrameShape(QFrame.StyledPanel)

        results_layout = QGridLayout(self._results_frame)
        results_layout.setContentsMargins(12, 8, 12, 8)
        results_layout.setHorizontalSpacing(12)
        results_layout.setVerticalSpacing(6)

        self._label_sum_qf = QLabel("ΣQf")
        self._label_ach = QLabel("ACH")
        self._label_qv = QLabel("Qv")
        self._label_qt = QLabel("Qt")

        self._value_sum_qf = QLabel("—")
        self._value_ach = ClickableLabel("—")
        self._value_qv = QLabel("—")
        self._value_qt = QLabel("—")

        for lbl in (
            self._label_sum_qf,
            self._label_ach,
            self._label_qv,
            self._label_qt,
            self._value_sum_qf,
            self._value_ach,
            self._value_qv,
            self._value_qt,
        ):
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        results_layout.addWidget(self._label_sum_qf, 0, 0)
        results_layout.addWidget(self._value_sum_qf, 0, 1)

        results_layout.addWidget(self._label_ach, 1, 0)
        results_layout.addWidget(self._value_ach, 1, 1)

        results_layout.addWidget(self._label_qv, 2, 0)
        results_layout.addWidget(self._value_qv, 2, 1)

        results_layout.addWidget(self._label_qt, 3, 0)
        results_layout.addWidget(self._value_qt, 3, 1)

        results_layout.setColumnStretch(1, 1)

        root.addWidget(self._results_frame)

        # --------------------------------------------------------------
        # Run button
        # --------------------------------------------------------------
        self._run_button = QPushButton("Run Heat-Loss")
        root.addWidget(self._run_button)

        # --------------------------------------------------------------
        # Fix U-values link
        # --------------------------------------------------------------
        self._fix_uvalues_link = QLabel("")
        self._fix_uvalues_link.setOpenExternalLinks(False)
        self._fix_uvalues_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self._fix_uvalues_link.hide()
        root.addWidget(self._fix_uvalues_link)

        # --------------------------------------------------------------
        # Readiness / warning labels
        # --------------------------------------------------------------
        self._readiness_label = QLabel("")
        root.addWidget(self._readiness_label)

        self._unsafe_warning_label = QLabel("")
        self._unsafe_warning_label.setStyleSheet("color: #c62828;")
        self._unsafe_warning_label.hide()
        root.addWidget(self._unsafe_warning_label)

        root.addStretch(1)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------
    def _wire_signals(self) -> None:
        self._run_button.clicked.connect(self.run_requested.emit)
        self._geometry_label.clicked.connect(self.geometry_edit_requested.emit)
        self._value_ach.clicked.connect(self.ach_edit_requested.emit)

        if self._worksheet_table is not None:
            self._worksheet_table.cellClicked.connect(
                self._on_worksheet_cell_clicked
            )
            self._worksheet_table.cellClicked.connect(self._on_cell_clicked)

        self._fix_uvalues_link.linkActivated.connect(
            lambda _href: self.open_uvalues_requested.emit(None)
        )

    # ------------------------------------------------------------------
    # Compatibility / no-op hooks
    # ------------------------------------------------------------------
    def mouseDoubleClickEvent(self, event) -> None:
        return

    def set_row_meta_lookup(self, lookup: dict) -> None:
        self._row_meta_by_surface = lookup

    def _on_cell_clicked(self, row: int, column: int) -> None:
        print(f"[HLP CLICK] row={row} col={column}")

        item = self._table.item(row, 0)
        print(f"[HLP CLICK] item={item}")

        if item is None:
            return

        surface_id = item.data(Qt.UserRole)
        print(f"[HLP CLICK] surface_id={surface_id}")

        row_meta = getattr(self, "_row_meta_by_surface", {}).get(surface_id)
        print(f"[HLP CLICK] row_meta={row_meta}")

        if column != DT_COLUMN:
            print("[HLP CLICK] not DT column")
            return

        if not row_meta:
            print("[HLP CLICK] no row_meta")
            return

        if not row_meta.adjacency_editable:
            print("[HLP CLICK] row not adjacency editable")
            return

        print(f"[HLP CLICK] EMIT adjacency_edit_requested {surface_id}")
        self.adjacency_edit_requested.emit(surface_id)


    def set_header_context(self, context: dict | None) -> None:
        return

    def set_internal_temperature(self, ti: float | None) -> None:
        if ti is None:
            self._ti_label.setText("Ti: — °C")
        else:
            self._ti_label.setText(f"Ti: {ti:.1f} °C")

    def set_default_internal_temp(self, value: float) -> None:
        return

    # ------------------------------------------------------------------
    # Room / header
    # ------------------------------------------------------------------
    def set_room(self, room_id: str | None) -> None:
        self._current_room_id = room_id

        if room_id:
            self._header.setText(f"Heat Loss — {room_id}")
        else:
            self._header.setText("Heat Loss — No room selected")

    def set_room_header(self, room_name: str, room_id: str) -> None:
        self._current_room_id = room_id
        self._header.setText(f"Heat Loss — {room_name}")

    def clear(self) -> None:
        self._current_room_id = None
        self._header.setText("Heat Loss — No room selected")
        self._status_label.setText("")
        self._geometry_label.setText("Geometry: —")
        self._table.clearContents()
        self._table.setRowCount(0)
        self._value_sum_qf.setText("—")
        self._value_ach.setText("—")
        self._value_qv.setText("—")
        self._value_qt.setText("—")
        self._readiness_label.setText("")
        self._unsafe_warning_label.hide()
        self._fix_uvalues_link.hide()

    # ------------------------------------------------------------------
    # Geometry projection
    # ------------------------------------------------------------------
    def set_geometry_summary(
        self,
        *,
        length_m: Optional[float],
        width_m: Optional[float],
        height_m: Optional[float],
    ) -> None:
        if None in (length_m, width_m, height_m):
            self._geometry_label.setText("Geometry: —")
            return

        self._geometry_label.setText(
            f"Geometry: {length_m:.2f} × {width_m:.2f} × {height_m:.2f} m"
        )

    # ------------------------------------------------------------------
    # Status / readiness
    # ------------------------------------------------------------------
    def set_heatloss_status(self, *, is_valid: bool) -> None:
        if is_valid:
            self._status_label.setText("Status: VALID")
            self._status_label.setStyleSheet("color: #2e7d32; font-size: 11px;")
        else:
            self._status_label.setText("Status: DIRTY (recalculate)")
            self._status_label.setStyleSheet("color: #c62828; font-size: 11px;")

    def set_readiness(self, readiness) -> None:
        if readiness.is_ready:
            text = "Ready"
            ok = True
        else:
            text = "Not ready:\n" + "\n".join(readiness.blocking_reasons)
            ok = False

        self._set_readiness(text, ok)
        self._run_button.setEnabled(ok)

    def set_ready(self) -> None:
        self._set_readiness("Ready", ok=True)

    def set_not_ready(self, reasons: list[str] | None = None) -> None:
        text = "Not ready" if not reasons else "Not ready:\n" + "\n".join(reasons)
        self._set_readiness(text, ok=False)

    def _set_readiness(self, text: str, ok: bool) -> None:
        self._readiness_label.setText(text)
        self._readiness_label.setStyleSheet(
            "color: #2e7d32; font-weight: 600;"
            if ok else
            "color: #c62828; font-weight: 600;"
        )

    # ------------------------------------------------------------------
    # Row meta access (for adapter / overlays)
    # ------------------------------------------------------------------
    def meta_for_row(self, row_index: int):
        if not hasattr(self, "_row_metas"):
            return None

        if 0 <= row_index < len(self._row_metas):
            return self._row_metas[row_index]

        return None

    # ------------------------------------------------------------------
    # Worksheet population
    # ------------------------------------------------------------------
    def set_rows(self, rows: Iterable, metas) -> None:
        table = self._table

        rows = list(rows)
        metas = list(metas or [])

        # --------------------------------------------------
        # Store metadata
        # --------------------------------------------------
        if len(metas) != len(rows):
            self._row_meta = []
        else:
            self._row_meta = metas

        self._row_meta_by_surface = {
            m.surface_id: m
            for m in self._row_meta
            if getattr(m, "surface_id", None)
        }

        table.setUpdatesEnabled(False)
        table.setSortingEnabled(False)
        table.clearContents()
        table.setRowCount(len(rows))
        table.clearSelection()

        # --------------------------------------------------
        # Populate rows
        # --------------------------------------------------
        for r, row in enumerate(rows):

            # support both dict + DTO (future-proof)
            get = row.get if isinstance(row, dict) else lambda k, d=None: getattr(row, k, d)

            surface_id = get("surface_id")

            # --------------------------------------------------
            # Element text
            # --------------------------------------------------
            element_text = str(get("element", ""))

            adjacent_label = get("adjacent_label")
            if adjacent_label:
                element_text = f"{element_text} → {adjacent_label}"

            # --------------------------------------------------
            # Hierarchy (parent/child)
            # --------------------------------------------------
            parent_id = getattr(row, "parent_surface_id", None)
            is_child = parent_id is not None

            if is_child:
                element_text = "    " + element_text

            item = QTableWidgetItem(element_text)
            item.setData(Qt.UserRole, surface_id)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            # --------------------------------------------------
            # Meta styling
            # --------------------------------------------------
            row_meta = self._row_meta[r] if r < len(self._row_meta) else None

            if row_meta is not None and getattr(row_meta, "adjacency_editable", False):
                item.setForeground(QColor("#1565c0"))
                item.setToolTip("Click to assign adjacent room")

            if is_child:
                item.setForeground(QColor("#555555"))

            table.setItem(r, 0, item)

            # --------------------------------------------------
            # Numeric columns
            # --------------------------------------------------

            # Area
            area = get("A") or get("area_m2")
            item_area = self._num_item(
                f"{area:.2f}" if isinstance(area, (int, float)) else "—"
            )
            table.setItem(r, 1, item_area)

            # U-value
            u = get("U") or get("u_value_W_m2K")
            item_u = self._num_item(
                f"{u:.3f}" if isinstance(u, (int, float)) else "—"
            )
            table.setItem(r, 2, item_u)

            # ΔT (with colour)
            dt = get("dT") or get("delta_t_K")
            item_dt = self._num_item(
                f"{dt:.1f}" if isinstance(dt, (int, float)) else "—"
            )
            if isinstance(dt, (int, float)):
                self._apply_value_colour(item_dt, float(dt))
            table.setItem(r, 3, item_dt)

            # Qf (with colour)
            qf = get("Qf") or get("qf_W")
            item_qf = self._num_item(
                f"{qf:.1f}" if isinstance(qf, (int, float)) else "—"
            )
            if isinstance(qf, (int, float)):
                self._apply_value_colour(item_qf, float(qf))
            table.setItem(r, 4, item_qf)

            # --------------------------------------------------
            # Row state colouring
            # --------------------------------------------------
            state = get("state")
            if state:
                self._apply_row_state(r, state)

        # --------------------------------------------------
        # Compact table height (nice UX)
        # --------------------------------------------------
        header_h = table.horizontalHeader().height()
        rows_h = sum(table.rowHeight(i) for i in range(table.rowCount()))
        frame = table.frameWidth() * 2

        target_h = header_h + rows_h + frame
        table.setMinimumHeight(target_h)
        table.setMaximumHeight(target_h)

        table.resizeColumnsToContents()

        table.setUpdatesEnabled(True)
        table.setSortingEnabled(False)

    from PySide6.QtGui import QColor

    @staticmethod
    def _apply_value_colour(item: QTableWidgetItem, value: float | None) -> None:
        if value is None:
            return

        if value < 0:
            item.setForeground(QColor(100, 160, 255))  # soft blue (gain)
        elif value == 0:
            item.setForeground(QColor(150, 150, 150))  # grey (adiabatic)
        # positive → leave default (cleanest)

    def _apply_row_state(self, row: int, state: str) -> None:
        if state == "GREEN":
            return
        if state == "ORANGE":
            color = QColor(255, 243, 205)
        elif state == "RED":
            color = QColor(248, 215, 218)
        else:
            return

        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                item.setBackground(color)

    # ------------------------------------------------------------------
    # Worksheet interaction
    # ------------------------------------------------------------------
    def _on_worksheet_cell_clicked(self, row: int, column: int) -> None:
        table = self._worksheet_table
        if table is None:
            return

        if not hasattr(self, "_row_meta") or row >= len(self._row_meta):
            return

        row_meta = self._row_meta[row]

        element_item = table.item(row, 0)
        if element_item is None:
            return

        surface_id = element_item.data(Qt.UserRole)

        # --------------------------------------------------
        # 🔥 Adjacency click on ΔT column
        # --------------------------------------------------
        if column == 3 and getattr(row_meta, "adjacency_editable", False):
            if surface_id:
                self.adjacency_edit_requested.emit(str(surface_id))
            return

        # --------------------------------------------------
        # Editable cell (future use)
        # --------------------------------------------------
        cell_meta = row_meta.columns.get(column) if row_meta else None
        if cell_meta and cell_meta.editable:
            self.worksheet_cell_edit_requested.emit(row, column)

        # --------------------------------------------------
        # Fallback: focus
        # --------------------------------------------------
        if surface_id:
            self.surface_focus_requested.emit(surface_id)

    # ------------------------------------------------------------------
    # Room-level result display
    # ------------------------------------------------------------------
    def set_room_results(
        self,
        *,
        sum_qf: float | None,
        ach: float | None = None,
        qv: float | None,
        qt: float | None,
    ) -> None:
        def _fmt_w(value: float | None) -> str:
            if isinstance(value, (int, float)):
                return f"{value:,.1f} W"
            return "—"

        def _fmt_plain(value: float | None) -> str:
            if isinstance(value, (int, float)):
                return f"{value:.2f}"
            return "—"

        self._value_sum_qf.setText(_fmt_w(sum_qf))
        self._value_ach.setText(_fmt_plain(ach))
        self._value_qv.setText(_fmt_w(qv))
        self._value_qt.setText(_fmt_w(qt))

    def set_results(
        self,
        *,
        ach: Optional[float],
        qv_W: Optional[float],
        qt_W: Optional[float],
        sum_qf_W: Optional[float] = None,
    ) -> None:
        self.set_room_results(
            sum_qf=sum_qf_W,
            ach=ach,
            qv=qv_W,
            qt=qt_W,
        )

    def update_room_totals_from_project(self, project_state) -> None:
        if self._current_room_id is None:
            self.set_room_results(sum_qf=None, ach=None, qv=None, qt=None)
            return

        qf, qv, qt = project_state.get_room_heatloss_totals(
            self._current_room_id
        )

        self.set_room_results(
            sum_qf=qf,
            ach=None,
            qv=qv,
            qt=qt,
        )

    # ------------------------------------------------------------------
    # Run control
    # ------------------------------------------------------------------
    def set_run_enabled(self, enabled: bool) -> None:
        self._run_button.setEnabled(enabled)
        self._unsafe_warning_label.hide()

    # ------------------------------------------------------------------
    # U-values action
    # ------------------------------------------------------------------
    def show_fix_uvalues_action(self, show: bool) -> None:
        if show:
            self._fix_uvalues_link.setText('<a href="#">Fix U-Values…</a>')
            self._fix_uvalues_link.show()
        else:
            self._fix_uvalues_link.hide()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _num_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item
