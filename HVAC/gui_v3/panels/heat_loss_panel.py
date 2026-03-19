# ======================================================================
# HVAC/gui_v3/panels/heat_loss_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional, Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QDoubleSpinBox,
    QHeaderView,
    QCheckBox,
    QFrame,
    QGridLayout,
)

# ======================================================================
# HeatLossPanelV3
# ======================================================================

class HeatLossPanelV3(QWidget):
    """
    Heat-Loss worksheet panel (GUI v3)

    Authority
    ---------
    • Owns Ti user input
    • Displays worksheet rows
    • Emits intent only
    • Does NOT touch ProjectState
    """

    # ------------------------------------------------------------------
    # Signals (adapter contracts)
    # ------------------------------------------------------------------
    run_requested = Signal()
    internal_design_temp_changed = Signal(float)
    surface_focus_requested = Signal(object)  # surface_id | None
    open_uvalues_requested = Signal(object)  # surface_id | None
    ach_changed = Signal(float)
    ignore_readiness_changed = Signal(bool)  # NEW
    geometry_edit_requested = Signal()
    ach_edit_requested = Signal()


    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._room_id: Optional[str] = None
        self._worksheet_table: Optional[QTableWidget] = None

        self._build_ui()

        if self._worksheet_table is not None:
            self._worksheet_table.cellClicked.connect(
                self._on_worksheet_cell_clicked
            )

        self._ach_input.valueChanged.connect(
        self.ach_changed.emit
        )

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
        self._header.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(self._header)

        # --------------------------------------------------
        # Hook anchors (Geometry / ACH mini panels)
        # --------------------------------------------------

        def _build_hook() -> QWidget:
            w = QWidget(self)
            layout = QVBoxLayout(w)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            w.setStyleSheet("border:1px dashed #444; border-radius:4px;")
            return w

        # --------------------------------------------------
        # --------------------------------------------------
        # Heat-loss worksheet
        # --------------------------------------------------

        self._table = QTableWidget(self)
        self._worksheet_table = self._table

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

        header = self._table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)

        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1, 2, 3, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        header.sectionResized.connect(
            lambda *_: self._align_totals_with_qf()
        )

        root.addWidget(self._table)

        # --------------------------------------------------
        # Results frame
        # --------------------------------------------------

        self._results_frame = QFrame(self)
        self._results_frame.setFrameShape(QFrame.StyledPanel)

        results_layout = QGridLayout(self._results_frame)
        results_layout.setContentsMargins(12, 8, 12, 8)
        results_layout.setHorizontalSpacing(12)

        # Labels
        self._label_sum_qf = QLabel("ΣQf")
        self._label_qv = QLabel("Qv")
        self._label_qt = QLabel("Qt")
        self._label_ach = QLabel("ACH")

        for lbl in (self._label_sum_qf, self._label_qv, self._label_qt):
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Values
        self._value_sum_qf = QLabel("—")
        self._value_qv = QLabel("—")
        self._value_qt = QLabel("—")

        for lbl in (self._value_sum_qf, self._value_qv, self._value_qt):
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ACH input
        self._ach_input = QDoubleSpinBox(self)
        self._ach_input.setRange(0.0, 20.0)
        self._ach_input.setDecimals(2)
        self._ach_input.setSingleStep(0.1)
        self._ach_input.setFixedWidth(80)

        # Layout rows
        results_layout.addWidget(self._label_sum_qf, 0, 2)
        results_layout.addWidget(self._value_sum_qf, 0, 3)

        results_layout.addWidget(self._ach_input, 1, 0)
        results_layout.addWidget(self._label_ach, 1, 1)
        results_layout.addWidget(self._label_qv, 1, 2)
        results_layout.addWidget(self._value_qv, 1, 3)

        results_layout.addWidget(self._label_qt, 2, 2)
        results_layout.addWidget(self._value_qt, 2, 3)

        results_layout.setColumnStretch(3, 1)

        root.addWidget(self._results_frame)

        # --------------------------------------------------
        # Run button
        # --------------------------------------------------

        self._run_button = QPushButton("Run Heat-Loss")
        self._run_button.clicked.connect(self.run_requested.emit)
        root.addWidget(self._run_button)

        # --------------------------------------------------
        # Fix U-values link
        # --------------------------------------------------

        self._fix_uvalues_link = QLabel("")
        self._fix_uvalues_link.setOpenExternalLinks(False)
        self._fix_uvalues_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self._fix_uvalues_link.linkActivated.connect(
            lambda _href: self.open_uvalues_requested.emit(None)
        )
        self._fix_uvalues_link.hide()

        root.addWidget(self._fix_uvalues_link)

        # --------------------------------------------------
        # Readiness label
        # --------------------------------------------------

        self._readiness_label = QLabel("")
        root.addWidget(self._readiness_label)

        # --------------------------------------------------
        # Final alignment
        # --------------------------------------------------

        self._align_totals_with_qf()
        root.addStretch(1)

    def mouseDoubleClickEvent(self, event):
        # Overlay editing not enabled yet
        return

    def set_readiness(self, readiness) -> None:

        if readiness.is_ready:
            text = "Ready"
            ok = True
        else:
            text = "Not ready:\n" + "\n".join(readiness.blocking_reasons)
            ok = False

        self._set_readiness(text, ok)
        self._run_button.setEnabled(ok)

    def set_internal_temperature(self, value, source):

        self._ti_spinbox.setValue(float(value) if value is not None else 0.0)

        if source == "environment":
            self._apply_inherited_style(self._ti_spinbox)
        else:
            self._clear_style(self._ti_spinbox)

    def _apply_inherited_style(widget):

        font = widget.font()
        font.setItalic(True)
        font.setPointSize(font.pointSize() - 1)

        widget.setFont(font)
        widget.setStyleSheet("color:#666;")

    def _clear_style(self, widget):

        font = widget.font()
        font.setItalic(False)

        widget.setFont(font)
        widget.setStyleSheet("")


    def set_room(self, room_id: str | None) -> None:
        self._current_room_id = room_id

        if room_id:
            self._header.setText(f"Heat Loss — {room_id}")
        else:
            self._header.setText("Heat Loss — No room selected")

    # ------------------------------------------------------------------
    # Adapter compatibility (legacy no-op)
    # ------------------------------------------------------------------
    def set_header_context(self, context: dict | None) -> None:
        """
        Adapter compatibility shim.

        Header context was removed from HLP in GUI v3,
        but adapters still call this method.

        Intentionally a no-op.
        """
        return

    # ------------------------------------------------------------------
    # Worksheet population (adapter contract)
    # ------------------------------------------------------------------
    def set_rows(self, rows: Iterable) -> None:

        table = self._table
        rows = list(rows)

        # ---- Disable redraw (prevents flicker) ----
        table.setUpdatesEnabled(False)
        table.setSortingEnabled(False)
        table.clearContents()
        table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            surface_id = row.get("surface_id")

            item = QTableWidgetItem(str(row.get("element", "")))
            item.setData(Qt.UserRole, surface_id)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            table.setItem(r, 0, item)

            area = row.get("A")
            table.setItem(
                r, 1,
                self._num_item(f"{area:.2f}" if isinstance(area, (int, float)) else "—")
            )

            u = row.get("U")
            table.setItem(
                r, 2,
                self._num_item(f"{u:.3f}" if isinstance(u, (int, float)) else "—")
            )

            dt = row.get("dT")
            table.setItem(
                r, 3,
                self._num_item(f"{dt:.1f}" if isinstance(dt, (int, float)) else "—")
            )

            qf = row.get("Qf")
            table.setItem(
                r, 4,
                self._num_item(f"{qf:.1f}" if isinstance(qf, (int, float)) else "—")
            )
        # --- Auto-size table height to visible rows ------------------

        header_h = self._table.horizontalHeader().height()
        rows_h = sum(self._table.rowHeight(i) for i in range(self._table.rowCount()))

        frame = self._table.frameWidth() * 2

        self._table.setMinimumHeight(header_h + rows_h + frame)
        self._table.setMaximumHeight(header_h + rows_h + frame)
        self._table.resizeColumnsToContents()
        # ---- Re-enable redraw ----
        table.setUpdatesEnabled(True)
        table.setSortingEnabled(True)

    # ------------------------------------------------------------------
    # Worksheet interaction
    # ------------------------------------------------------------------

    def _on_worksheet_cell_clicked(self, row: int, column: int) -> None:
        table = self._worksheet_table
        if table is None:
            return

        element_item = table.item(row, 0)
        if element_item is None:
            return

        surface_id = element_item.data(Qt.UserRole)
        self.surface_focus_requested.emit(surface_id)

    # --------------------------------------------------
    # Room-Level Result Display
    # --------------------------------------------------
    def set_default_internal_temp(self, value: float) -> None:
        self._ti_input.blockSignals(True)
        self._ti_input.setValue(value)
        self._ti_input.blockSignals(False)

    def set_room_results(
            self,
            *,
            sum_qf: float | None,
            qv: float | None,
            qt: float | None,
    ) -> None:
        """
        Display room-level aggregate results.

        Rules:
        • sum_qf must come from Fabric engine
        • qv must come from Ventilation engine
        • qt must be explicit aggregation (not auto-computed here)
        • GUI does NOT compute physics
        """

        def _fmt(value: float | None) -> str:
            if isinstance(value, (int, float)):
                return f"{value:,.1f} W"
            return "—"

        self._value_sum_qf.setText(_fmt(sum_qf))
        self._value_qv.setText(_fmt(qv))
        self._value_qt.setText(_fmt(qt))

    # ------------------------------------------------------------------
    # Run control (adapter contract)
    # ------------------------------------------------------------------
    def set_run_enabled(self, enabled: bool) -> None:
        self._run_button.setEnabled(enabled)

        if not hasattr(self, "_ignore_readiness_checkbox"):
            return

        if self._ignore_readiness_checkbox.isChecked():
            self._run_button.setEnabled(True)
            self._unsafe_warning_label.setText(
                "⚠ Running with incomplete geometry — results may be invalid"
            )
            self._unsafe_warning_label.show()
        else:
            self._run_button.setEnabled(enabled)
            self._unsafe_warning_label.hide()

    # ------------------------------------------------------------------
    # Refresh from ProjectState (called by adapter/controller)
    # ------------------------------------------------------------------
    def update_room_totals_from_project(self, project_state) -> None:

        if self._current_room_id is None:
            self.set_room_results(sum_qf=None, qv=None, qt=None)
            return

        qf, qv, qt = project_state.get_room_heatloss_totals(
            self._current_room_id
        )

        self.set_room_results(
            sum_qf=qf,
            qv=qv,
            qt=qt,
        )
    # ------------------------------------------------------------------
    # Readiness presentation
    # ------------------------------------------------------------------
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

    def _align_totals_with_qf(self):

        if not hasattr(self, "_table"):
            return

        header = self._table.horizontalHeader()

        qf_col = 4  # Element | A | U | ΔT | Qf

        x = header.sectionPosition(qf_col) + header.sectionSize(qf_col) // 2

        self._results_frame.move(
            x - self._results_frame.width() // 2,
            self._results_frame.y()
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _num_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        font = QFont()
        font.setStyleHint(QFont.Monospace)
        item.setFont(font)

        return item

    def show_fix_uvalues_action(self, show: bool) -> None:
        if show:
            self._fix_uvalues_link.setText('<a href="#">Fix U-Values…</a>')
            self._fix_uvalues_link.show()
        else:
            self._fix_uvalues_link.hide()

