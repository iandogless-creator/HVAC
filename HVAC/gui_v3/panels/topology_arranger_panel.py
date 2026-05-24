# ======================================================================
# HVAC/gui_v3/panels/topology_arranger_panel.py
# ======================================================================

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
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
    move_up_requested = Signal(str)
    move_down_requested = Signal(str)
    make_terminal_requested = Signal(str)
    set_index_requested = Signal(str)

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
        self._selected_room_id: str | None = None
        self._table.itemSelectionChanged.connect(self._capture_selected_room)
        self._move_up_button = QPushButton("Move Up")
        self._move_down_button = QPushButton("Move Down")
        self._make_terminal_button = QPushButton("Make Terminal")
        self._set_index_button = QPushButton("Set As Index")

        self._move_up_button.clicked.connect(self._emit_move_up)
        self._move_down_button.clicked.connect(self._emit_move_down)
        self._make_terminal_button.clicked.connect(self._emit_make_terminal)
        self._set_index_button.clicked.connect(self._emit_set_index)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._move_up_button)
        button_layout.addWidget(self._move_down_button)
        button_layout.addWidget(self._make_terminal_button)
        button_layout.addWidget(self._set_index_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._status_label)
        layout.addWidget(self._table)
        layout.addLayout(button_layout)

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
        previous_selected_room_id = self.selected_room_id()
        row_to_restore: int | None = None
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
        if previous_selected_room_id and room_id == previous_selected_room_id:
            row_to_restore = row_index
        self._table.resizeRowsToContents()
        if row_to_restore is not None:
            self._table.selectRow(row_to_restore)

        self._table.resizeRowsToContents()

        if row_to_restore is not None:
            self._table.blockSignals(True)
            try:
                self._table.selectRow(row_to_restore)
                self._table.setCurrentCell(row_to_restore, self.COL_ROOM)
                self._selected_room_id = previous_selected_room_id
            finally:
                self._table.blockSignals(False)


    def _capture_selected_room(self) -> None:
        room_id = self._selected_room_id_from_table()

        if room_id:
            self._selected_room_id = room_id

    def _selected_room_id_from_table(self) -> str | None:
        selected_items = self._table.selectedItems()

        if selected_items:
            row = selected_items[0].row()
        else:
            row = self._table.currentRow()

        if row < 0:
            return None

        room_item = self._table.item(row, self.COL_ROOM)

        if room_item is None:
            return None

        room_id = room_item.data(Qt.UserRole)

        if not room_id:
            return None

        return str(room_id)

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

    def select_room_id(self, room_id: str | None) -> None:
        """
        Select the route row for room_id, if present.

        Used by the adapter after route edits rebuild the table.
        """

        if not room_id:
            return

        room_id = str(room_id)
        self._selected_room_id = room_id

        for row in range(self._table.rowCount()):
            room_item = self._table.item(row, self.COL_ROOM)

            if room_item is None:
                continue

            if str(room_item.data(Qt.UserRole) or "") == room_id:
                self._table.blockSignals(True)
                try:
                    self._table.selectRow(row)
                    self._table.setCurrentCell(row, self.COL_ROOM)
                finally:
                    self._table.blockSignals(False)

                return

    def _emit_move_up(self) -> None:
        room_id = self.selected_room_id()
        if room_id:
            self.move_up_requested.emit(room_id)

    def _emit_move_down(self) -> None:
        room_id = self.selected_room_id()
        if room_id:
            self.move_down_requested.emit(room_id)

    def _emit_make_terminal(self) -> None:
        room_id = self.selected_room_id()
        if room_id:
            self.make_terminal_requested.emit(room_id)

    def _emit_set_index(self) -> None:
        room_id = self.selected_room_id()
        if room_id:
            self.set_index_requested.emit(room_id)