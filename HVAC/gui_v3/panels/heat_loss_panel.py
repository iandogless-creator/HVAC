# ======================================================================
# HVAC/gui_v3/panels/heat_loss_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
)
from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel
from HVAC.gui_v3.panels.ach_mini_panel import ACHMiniPanel
from PySide6.QtWidgets import QTableWidgetItem


# (keep your existing imports as they are above this line)


class HeatLossPanelV3(QWidget):
    """
    Heat-Loss Panel (Observer)

    - Displays committed values only
    - Emits edit intent only (does not edit inline)
    """

    # --------------------------------------------------------------
    # Signals (adapter contracts)
    # --------------------------------------------------------------
    run_requested = Signal()

    edit_requested = Signal(
        str,  # room_id
        str,  # element_id
        str,  # attribute: "area" | "u_value" | "delta_t"
    )


    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._room_id: Optional[str] = None
        self._worksheet_table = None  # explicit

        self._build_ui()

        # Wire worksheet click
        if self._worksheet_table is not None:
            self._worksheet_table.cellClicked.connect(
                self._on_worksheet_cell_clicked
            )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """
        Build Heat-Loss panel UI.
        """
        layout = QVBoxLayout(self)

        # --------------------------------------------------------------
        # Geometry / ACH mini panels (panel owns widgets, adapter binds)
        # --------------------------------------------------------------
        self._geometry_panel = GeometryMiniPanel(self)
        self._ach_panel = ACHMiniPanel(self)

        layout.addWidget(self._geometry_panel)
        layout.addWidget(self._ach_panel)

        # --------------------------------------------------------------
        # Worksheet table (THIS MUST SET self._worksheet_table)
        # --------------------------------------------------------------
        self._worksheet_table = QTableWidget(self)
        self._worksheet_table.setColumnCount(5)
        self._worksheet_table.setHorizontalHeaderLabels(
            ["Element", "Area", "ΔT", "U", "Qf"]
        )

        layout.addWidget(self._worksheet_table)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Room binding
    # ------------------------------------------------------------------
    def set_room(self, room_id: Optional[str]) -> None:
        """
        Set the current room context for intent emission.
        """
        self._room_id = room_id

    # ------------------------------------------------------------------
    # Worksheet interaction
    # ------------------------------------------------------------------
    def _on_worksheet_cell_clicked(self, row: int, column: int) -> None:
        if self._room_id is None:
            return

        header_item = self._worksheet_table.horizontalHeaderItem(column)
        if header_item is None:
            return

        attribute = self._attribute_for_header(header_item.text())
        if attribute is None:
            return

        element_id = self._element_id_for_row(row)
        if element_id is None:
            return

        self.edit_requested.emit(
            self._room_id,
            element_id,
            attribute,
        )

    # ------------------------------------------------------------------
    # Worksheet population (adapter contract)
    # ------------------------------------------------------------------
    def set_rows(self, rows: list) -> None:
        """
        Populate the heat-loss worksheet.

        `rows` is an adapter-provided list of DTO-like objects.
        This method renders them only.
        """

        table = self._worksheet_table
        table.clearContents()
        table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            # Column 0 — Element name (read-only)
            item_element = QTableWidgetItem(row.element_name)
            item_element.setData(Qt.UserRole, row.element_id)
            table.setItem(row_idx, 0, item_element)

            # Column 1 — Area
            table.setItem(
                row_idx,
                1,
                QTableWidgetItem(f"{row.area_m2:.2f}")
            )

            # Column 2 — ΔT
            QTableWidgetItem(f"{row.delta_t_k:.1f}")

            # Column 3 — U-value
            QTableWidgetItem(f"{row.u_value_w_m2k:.3f}")

            # Column 4 — Qf
            QTableWidgetItem(f"{row.qf_w:.1f}")

    # ------------------------------------------------------------------
    # Run control (adapter contract)
    # ------------------------------------------------------------------
    def set_run_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the Run Heat-Loss action.
        """
        if hasattr(self, "_run_button") and self._run_button is not None:
            self._run_button.setEnabled(enabled)
