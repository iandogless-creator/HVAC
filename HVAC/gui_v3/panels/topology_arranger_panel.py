# ======================================================================
# HVAC/gui_v3/panels/topology_arranger_panel.py
# ======================================================================

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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
    leg_selection_requested = Signal(str)
    principal_selection_requested = Signal(str)
    add_leg_requested = Signal(str, str, str)
    add_principal_requested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._title_label = QLabel("Topology Arranger")
        self._title_label.setObjectName("topologyArrangerTitleLabel")

        self._status_label = QLabel("No topology loaded")
        self._status_label.setObjectName("topologyArrangerStatusLabel")
        self._status_label.setWordWrap(True)

        self._leg_selector = QComboBox()
        self._leg_selector.setObjectName("topologyArrangerLegSelector")
        self._principal_selector = QComboBox()
        self._principal_selector.setObjectName(
            "topologyArrangerPrincipalSelector"
        )
        self._initial_room_selector = QComboBox()
        self._initial_room_selector.setObjectName(
            "topologyArrangerInitialRoomSelector"
        )
        self._leg_label_edit = QLineEdit()
        self._leg_label_edit.setObjectName("topologyArrangerNewLegLabel")
        self._leg_label_edit.setPlaceholderText("Automatic leg label")
        self._principal_label_edit = QLineEdit()
        self._principal_label_edit.setObjectName(
            "topologyArrangerNewPrincipalLabel"
        )
        self._principal_label_edit.setPlaceholderText(
            "Automatic principal label"
        )
        self._add_leg_button = QPushButton("Add Leg + Principal")
        self._add_leg_button.setObjectName("topologyArrangerAddLegButton")
        self._add_principal_button = QPushButton("Add Principal")
        self._add_principal_button.setObjectName(
            "topologyArrangerAddPrincipalButton"
        )

        creation_layout = QGridLayout()
        creation_layout.addWidget(QLabel("View leg"), 0, 0)
        creation_layout.addWidget(self._leg_selector, 0, 1)
        creation_layout.addWidget(QLabel("View principal"), 0, 2)
        creation_layout.addWidget(self._principal_selector, 0, 3)
        creation_layout.addWidget(QLabel("Initial room (moves if allocated)"), 1, 0)
        creation_layout.addWidget(self._initial_room_selector, 1, 1)
        creation_layout.addWidget(QLabel("New leg label"), 2, 0)
        creation_layout.addWidget(self._leg_label_edit, 2, 1)
        creation_layout.addWidget(QLabel("New principal label"), 2, 2)
        creation_layout.addWidget(self._principal_label_edit, 2, 3)
        creation_layout.addWidget(self._add_leg_button, 3, 1)
        creation_layout.addWidget(self._add_principal_button, 3, 3)

        self._leg_selector.currentIndexChanged.connect(
            self._emit_leg_selection
        )
        self._principal_selector.currentIndexChanged.connect(
            self._emit_principal_selection
        )
        self._initial_room_selector.currentIndexChanged.connect(
            self._refresh_creation_enablement
        )
        self._add_leg_button.clicked.connect(self._emit_add_leg)
        self._add_principal_button.clicked.connect(self._emit_add_principal)

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
        layout.addLayout(creation_layout)
        layout.addWidget(self._table)
        layout.addLayout(button_layout)

    # ------------------------------------------------------------------
    # Adapter-facing API
    # ------------------------------------------------------------------

    def set_title(self, text: str) -> None:
        self._title_label.setText(str(text or "Topology Arranger"))

    def set_status(self, text: str) -> None:
        self._status_label.setText(str(text or ""))

    def set_leg_options(
        self,
        options: list[dict[str, str]],
        selected_leg_id: str,
    ) -> None:
        self._replace_combo_options(
            self._leg_selector,
            options,
            selected_leg_id,
        )
        self._refresh_creation_enablement()

    def set_principal_options(
        self,
        options: list[dict[str, str]],
        selected_subleg_id: str,
    ) -> None:
        self._replace_combo_options(
            self._principal_selector,
            options,
            selected_subleg_id,
        )
        self._refresh_creation_enablement()

    def set_available_rooms(
        self,
        options: list[dict[str, str]],
    ) -> None:
        self._replace_combo_options(self._initial_room_selector, options, "")
        self._refresh_creation_enablement()

    def selected_leg_id(self) -> str:
        return str(self._leg_selector.currentData() or "")

    def selected_principal_subleg_id(self) -> str:
        return str(self._principal_selector.currentData() or "")

    def selected_initial_room_id(self) -> str:
        return str(self._initial_room_selector.currentData() or "")

    @staticmethod
    def _replace_combo_options(
        combo: QComboBox,
        options: list[dict[str, str]],
        selected_id: str,
    ) -> None:
        combo.blockSignals(True)
        try:
            combo.clear()
            selected_index = -1
            for index, option in enumerate(options):
                identity = str(option.get("id", "") or "")
                combo.addItem(
                    str(option.get("label", "") or identity),
                    identity,
                )
                if identity == str(selected_id or ""):
                    selected_index = index
            if selected_index >= 0:
                combo.setCurrentIndex(selected_index)
        finally:
            combo.blockSignals(False)

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

    def _emit_leg_selection(self) -> None:
        leg_id = self.selected_leg_id()
        if leg_id:
            self.leg_selection_requested.emit(leg_id)

    def _emit_principal_selection(self) -> None:
        subleg_id = self.selected_principal_subleg_id()
        if subleg_id:
            self.principal_selection_requested.emit(subleg_id)

    def _emit_add_leg(self) -> None:
        room_id = self.selected_initial_room_id()
        if room_id:
            self.add_leg_requested.emit(
                self._leg_label_edit.text().strip(),
                self._principal_label_edit.text().strip(),
                room_id,
            )

    def _emit_add_principal(self) -> None:
        room_id = self.selected_initial_room_id()
        if room_id:
            self.add_principal_requested.emit(
                self._principal_label_edit.text().strip(),
                room_id,
            )

    def clear_creation_labels(self) -> None:
        self._leg_label_edit.clear()
        self._principal_label_edit.clear()

    def _refresh_creation_enablement(self) -> None:
        has_room = bool(self.selected_initial_room_id())
        self._add_leg_button.setEnabled(has_room)
        self._add_principal_button.setEnabled(
            has_room and bool(self.selected_leg_id())
        )
