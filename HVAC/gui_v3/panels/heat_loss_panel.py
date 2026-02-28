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

        # --- Header ---------------------------------------------------
        self._header = QLabel("Heat Loss — No room selected")
        self._header.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(self._header)

        # --- Ti input -------------------------------------------------
        ti_label = QLabel("Internal design temperature (°C)")
        self._ti_input = QDoubleSpinBox()
        self._ti_input.setRange(-50.0, 50.0)
        self._ti_input.setDecimals(1)
        self._ti_input.setSingleStep(0.5)
        self._ti_input.valueChanged.connect(
            self.internal_design_temp_changed.emit
        )

        root.addWidget(ti_label)
        root.addWidget(self._ti_input)

        # --- Worksheet ------------------------------------------------
        table = QTableWidget(self)
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            [
                "Element",
                "A (m²)",
                "U (W/m²·K)",
                "ΔT (K)",
                "Qf (W)",
            ]
        )

        table.setRowCount(0)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)

        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)

        # Column sizing
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1, 2, 3, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self._worksheet_table = table
        root.addWidget(table)
        # --------------------------------------------------
        # Room Results (Room-Level Aggregates)
        # --------------------------------------------------

        from PySide6.QtWidgets import QFrame, QGridLayout
        self._results_frame = QFrame(self)
        self._results_frame.setFrameShape(QFrame.StyledPanel)

        results_layout = QGridLayout(self._results_frame)
        results_layout.setContentsMargins(12, 8, 12, 8)
        results_layout.setHorizontalSpacing(12)

        # ---- Labels ----
        self._label_sum_qf = QLabel("ΣQf")
        self._label_qv = QLabel("Qv")
        self._label_qt = QLabel("Qt")
        self._label_ach = QLabel("ACH")

        # Right-align result labels
        for lbl in (self._label_sum_qf, self._label_qv, self._label_qt):
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

        # ---- Values ----
        self._value_sum_qf = QLabel("—")
        self._value_qv = QLabel("—")
        self._value_qt = QLabel("—")

        for lbl in (self._value_sum_qf, self._value_qv, self._value_qt):
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        # ---------------------------
        # ACH input (for Qv)
        # ---------------------------
        self._ach_input = QDoubleSpinBox(self)
        self._ach_input.setRange(0.0, 20.0)
        self._ach_input.setDecimals(2)
        self._ach_input.setSingleStep(0.1)
        self._ach_input.setValue(0.50)  # sensible default
        self._ach_input.setFixedWidth(80)

        # Optional small suffix label
        self._ach_label = QLabel("ACH")

        # -------------------------------
        # Layout structure
        # -------------------------------

        # Row 0: ΣQf (right side only)
        results_layout.addWidget(self._label_sum_qf, 0, 2)
        results_layout.addWidget(self._value_sum_qf, 0, 3)

        # Row 1: ACH + Qv
        results_layout.addWidget(self._ach_input, 1, 0)
        results_layout.addWidget(self._label_ach, 1, 1)
        results_layout.addWidget(self._label_qv, 1, 2)
        results_layout.addWidget(self._value_qv, 1, 3)

        # Row 2: Qt (right side only)
        results_layout.addWidget(self._label_qt, 2, 2)
        results_layout.addWidget(self._value_qt, 2, 3)

        # Column stretch
        results_layout.setColumnStretch(0, 0)
        results_layout.setColumnStretch(1, 0)
        results_layout.setColumnStretch(2, 0)
        results_layout.setColumnStretch(3, 1)
        root.addWidget(self._results_frame)
        # --- Run button ----------------------------------------------
        self._run_button = QPushButton("Run Heat-Loss")
        self._run_button.clicked.connect(self.run_requested.emit)
        root.addWidget(self._run_button)

        # --- Readiness label -----------------------------------------
        # --- Fix action link (hidden by default) ------------------------
        self._fix_uvalues_link = QLabel("")
        self._fix_uvalues_link.setOpenExternalLinks(False)
        self._fix_uvalues_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self._fix_uvalues_link.linkActivated.connect(lambda _href: self.open_uvalues_requested.emit(None))
        self._fix_uvalues_link.hide()
        root.addWidget(self._fix_uvalues_link)


        self._readiness_label = QLabel("")
        root.addWidget(self._readiness_label)

        root.addStretch(1)

    def set_room(self, room_id: str | None) -> None:
        self._current_room_id = room_id

        if room_id:
            self._header.setText(f"Heat Loss — {room_id}")
        else:
            self._header.setText("Heat Loss — No room selected")

    # ------------------------------------------------------------------
    # Worksheet population (adapter contract)
    # ------------------------------------------------------------------
    def set_rows(self, rows: Iterable) -> None:
        table = self._worksheet_table
        if table is None:
            return

        table.clearContents()
        table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            # Element (left-aligned)
            item_element = QTableWidgetItem(row.element_name)
            item_element.setData(Qt.UserRole, row.element_id)
            item_element.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            table.setItem(row_idx, 0, item_element)

            # Numeric columns (right-aligned)
            # Numeric columns (right-aligned, None-safe)

            # Area (m²)
            table.setItem(
                row_idx,
                1,
                self._num_item(
                    f"{row.area_m2:.2f}" if isinstance(row.area_m2, (int, float)) else "—"
                ),
            )

            # U-value (W/m²·K)
            table.setItem(
                row_idx,
                2,
                self._num_item(
                    f"{row.u_value_w_m2k:.3f}"
                    if isinstance(row.u_value_w_m2k, (int, float))
                    else "—"
                ),
            )

            # ΔT (K)
            table.setItem(
                row_idx,
                3,
                self._num_item(
                    f"{row.delta_t_k:.1f}"
                    if isinstance(row.delta_t_k, (int, float))
                    else "—"
                ),
            )

            # Qf (W)
            table.setItem(
                row_idx,
                4,
                self._num_item(
                    f"{row.qf_w:.1f}"
                    if isinstance(row.qf_w, (int, float))
                    else "—"
                ),
            )

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