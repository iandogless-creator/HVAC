# ======================================================================
# HVAC/gui_v3/panels/topology_arranger_panel.py
# ======================================================================

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


# ======================================================================
# TopologyArrangerPanel
# ======================================================================

class TopologyArrangerPanel(QWidget):
    """
    GUI v3 — Topology Arranger Panel.

    DEV v1 scope
    ------------
    Read-only route order display for HydronicTopologyV1.

    Responsibilities
    ----------------
    • Display topology route rows
    • Display index/terminal markers
    • Remain a passive panel

    Explicitly forbidden
    --------------------
    • No ProjectState mutation
    • No pipe sizing
    • No pressure-drop calculation
    • No proportioning calculation
    • No heat-loss calculation

    Later buttons
    -------------
    • Move Up
    • Move Down
    • Make Terminal
    • Set As Index
    """

    COL_ORDER = 0
    COL_ROOM = 1
    COL_INDEX = 2
    COL_TERMINAL = 3

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._title_label = QLabel("Topology Arranger")
        self._title_label.setObjectName("topologyArrangerTitleLabel")

        self._status_label = QLabel("No topology loaded")
        self._status_label.setObjectName("topologyArrangerStatusLabel")
        self._status_label.setWordWrap(True)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            [
                "Order",
                "Room",
                "Index",
                "Terminal",
            ]
        )

        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(self.COL_ORDER, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_ROOM, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_INDEX, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_TERMINAL, QHeaderView.ResizeToContents)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._status_label)
        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Adapter-facing API
    # ------------------------------------------------------------------

    def set_title(self, text: str) -> None:
        self._title_label.setText(str(text or "Topology Arranger"))

    def set_status(self, text: str) -> None:
        self._status_label.setText(str(text or ""))

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        """
        Replace all displayed topology route rows.

        Expected row keys:
        - order
        - room_id
        - label
        - is_index
        - is_terminal
        """

        self._table.setRowCount(0)

        for row_data in rows:
            row_index = self._table.rowCount()
            self._table.insertRow(row_index)

            order = row_data.get("order", "")
            room_id = str(row_data.get("room_id", "") or "")
            label = str(row_data.get("label", "") or room_id)
            is_index = bool(row_data.get("is_index", False))
            is_terminal = bool(row_data.get("is_terminal", False))

            order_item = QTableWidgetItem(str(order))
            order_item.setTextAlignment(Qt.AlignCenter)

            room_item = QTableWidgetItem(label)
            room_item.setData(Qt.UserRole, room_id)

            index_item = QTableWidgetItem("⚑" if is_index else "")
            index_item.setTextAlignment(Qt.AlignCenter)

            terminal_item = QTableWidgetItem("Terminal" if is_terminal else "")
            terminal_item.setTextAlignment(Qt.AlignCenter)

            self._table.setItem(row_index, self.COL_ORDER, order_item)
            self._table.setItem(row_index, self.COL_ROOM, room_item)
            self._table.setItem(row_index, self.COL_INDEX, index_item)
            self._table.setItem(row_index, self.COL_TERMINAL, terminal_item)

        self._table.resizeRowsToContents()

    def selected_room_id(self) -> str | None:
        """
        Return selected route room id, if a route row is selected.
        """

        selected_items = self._table.selectedItems()

        if not selected_items:
            return None

        row = selected_items[0].row()
        room_item = self._table.item(row, self.COL_ROOM)

        if room_item is None:
            return None

        room_id = room_item.data(Qt.UserRole)

        if not room_id:
            return None

        return str(room_id)