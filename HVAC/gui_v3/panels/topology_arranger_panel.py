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
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from HVAC.gui_v3.widgets.topology_arranger_schematic_widget_v1 import (
    TopologyArrangerSchematicWidgetV1,
)
from HVAC.gui_v3.widgets.topology_room_drag_drop_interaction_v1 import (
    TopologyRoomStagingTrayV1,
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
    branch_parent_selection_requested = Signal(str)
    branch_origin_selection_requested = Signal(str)
    branch_first_room_selection_requested = Signal(str)
    add_branch_requested = Signal(str, str, str, str)
    room_placement_requested = Signal(str, str, int)
    return_room_to_staging_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._title_label = QLabel("Topology Arranger")
        self._title_label.setObjectName("topologyArrangerTitleLabel")

        self._status_label = QLabel("No topology loaded")
        self._status_label.setObjectName("topologyArrangerStatusLabel")
        self._status_label.setWordWrap(True)

        self._creation_result_label = QLabel("")
        self._creation_result_label.setObjectName(
            "topologyArrangerCreationResultLabel"
        )
        self._creation_result_label.setWordWrap(True)
        self._creation_result_label.setVisible(False)
        self._creation_result_label.setStyleSheet(
            "QLabel { background: #f6d39a; color: #2b2115; "
            "border: 1px solid #69451d; border-radius: 4px; padding: 6px; }"
        )

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
        self._add_leg_button = QPushButton("Create New Leg + Principal")
        self._add_leg_button.setObjectName("topologyArrangerAddLegButton")
        self._add_principal_button = QPushButton("Add Principal")
        self._add_principal_button.setObjectName(
            "topologyArrangerAddPrincipalButton"
        )
        self._branch_parent_selector = QComboBox()
        self._branch_parent_selector.setObjectName(
            "topologyArrangerBranchParentSelector"
        )
        self._branch_origin_selector = QComboBox()
        self._branch_origin_selector.setObjectName(
            "topologyArrangerBranchOriginSelector"
        )
        self._branch_first_room_selector = QComboBox()
        self._branch_first_room_selector.setObjectName(
            "topologyArrangerBranchFirstRoomSelector"
        )
        self._branch_label_edit = QLineEdit()
        self._branch_label_edit.setObjectName("topologyArrangerNewBranchLabel")
        self._branch_label_edit.setPlaceholderText("Automatic branch label")
        self._add_branch_button = QPushButton("Add Branch")
        self._add_branch_button.setObjectName("topologyArrangerAddBranchButton")

        creation_layout = QGridLayout()
        creation_layout.addWidget(QLabel("View leg"), 0, 0)
        creation_layout.addWidget(self._leg_selector, 0, 1)
        creation_layout.addWidget(QLabel("View subleg"), 0, 2)
        creation_layout.addWidget(self._principal_selector, 0, 3)
        creation_layout.addWidget(QLabel("Initial room (moves if allocated)"), 1, 0)
        creation_layout.addWidget(self._initial_room_selector, 1, 1)
        creation_layout.addWidget(QLabel("New leg label"), 2, 0)
        creation_layout.addWidget(self._leg_label_edit, 2, 1)
        creation_layout.addWidget(QLabel("New principal label"), 2, 2)
        creation_layout.addWidget(self._principal_label_edit, 2, 3)
        creation_layout.addWidget(self._add_leg_button, 3, 1)
        creation_layout.addWidget(self._add_principal_button, 3, 3)
        creation_layout.addWidget(QLabel("Branch parent"), 4, 0)
        creation_layout.addWidget(self._branch_parent_selector, 4, 1)
        creation_layout.addWidget(QLabel("Origin on parent"), 4, 2)
        creation_layout.addWidget(self._branch_origin_selector, 4, 3)
        creation_layout.addWidget(
            QLabel("First branch room (moves if allocated)"), 5, 0
        )
        creation_layout.addWidget(self._branch_first_room_selector, 5, 1)
        creation_layout.addWidget(QLabel("New branch label"), 5, 2)
        creation_layout.addWidget(self._branch_label_edit, 5, 3)
        creation_layout.addWidget(self._add_branch_button, 6, 3)

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
        self._branch_parent_selector.currentIndexChanged.connect(
            self._emit_branch_parent_selection
        )
        self._branch_origin_selector.currentIndexChanged.connect(
            self._emit_branch_origin_selection
        )
        self._branch_first_room_selector.currentIndexChanged.connect(
            self._emit_branch_first_room_selection
        )
        self._add_branch_button.clicked.connect(self._emit_add_branch)

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

        self._topology_schematic_widget = TopologyArrangerSchematicWidgetV1()
        self._topology_schematic_widget.setObjectName(
            "topologyArrangerSchematicWidget"
        )
        self._topology_schematic_widget.room_placement_requested.connect(
            self.room_placement_requested.emit
        )
        self._staging_tray = TopologyRoomStagingTrayV1()
        self._staging_tray.return_to_staging_requested.connect(
            self.return_room_to_staging_requested.emit
        )
        self._staging_scroll = QScrollArea()
        self._staging_scroll.setObjectName("topologyRoomStagingScroll")
        self._staging_scroll.setWidgetResizable(True)
        self._staging_scroll.setMinimumHeight(105)
        self._staging_scroll.setMaximumHeight(145)
        self._staging_scroll.setWidget(self._staging_tray)
        self._topology_schematic_scroll = QScrollArea()
        self._topology_schematic_scroll.setObjectName(
            "topologyArrangerSchematicScroll"
        )
        self._topology_schematic_scroll.setWidgetResizable(False)
        self._topology_schematic_scroll.setMinimumHeight(235)
        self._topology_schematic_scroll.setMaximumHeight(340)
        self._topology_schematic_scroll.setWidget(
            self._topology_schematic_widget
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._status_label)
        layout.addWidget(self._creation_result_label)
        layout.addLayout(creation_layout)
        layout.addWidget(self._staging_scroll)
        layout.addWidget(self._topology_schematic_scroll)
        layout.addWidget(self._table)
        layout.addLayout(button_layout)

    # ------------------------------------------------------------------
    # Adapter-facing API
    # ------------------------------------------------------------------

    def set_title(self, text: str) -> None:
        self._title_label.setText(str(text or "Topology Arranger"))

    def set_status(self, text: str) -> None:
        self._status_label.setText(str(text or ""))

    def set_creation_result(self, text: str) -> None:
        cleaned = str(text or "").strip()
        self._creation_result_label.setText(cleaned)
        self._creation_result_label.setVisible(bool(cleaned))

    def set_topology_schematic(
        self,
        rows: list[dict[str, Any]],
        *,
        heat_source_label: str,
        focus: dict[str, str] | None = None,
    ) -> None:
        self._topology_schematic_widget.set_topology(
            rows,
            heat_source_label=heat_source_label,
            focus=focus,
        )

    def set_staging_rooms(self, rooms: list[dict[str, str]]) -> None:
        self._staging_tray.set_rooms(rooms)

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

    def set_branch_parent_options(
        self,
        options: list[dict[str, str]],
        selected_parent_id: str,
    ) -> None:
        self._replace_combo_options(
            self._branch_parent_selector,
            options,
            selected_parent_id,
        )
        self._refresh_creation_enablement()

    def set_branch_origin_options(
        self,
        options: list[dict[str, str]],
        selected_origin_room_id: str = "",
    ) -> None:
        self._replace_combo_options(
            self._branch_origin_selector,
            options,
            selected_origin_room_id,
        )
        self._refresh_creation_enablement()

    def set_branch_first_room_options(
        self,
        options: list[dict[str, str]],
        selected_room_id: str = "",
    ) -> None:
        self._replace_combo_options(
            self._branch_first_room_selector,
            options,
            selected_room_id,
        )
        self._refresh_creation_enablement()

    def set_route_editing_enabled(self, enabled: bool) -> None:
        for button in (
            self._move_up_button,
            self._move_down_button,
            self._make_terminal_button,
            self._set_index_button,
        ):
            button.setEnabled(bool(enabled))

    def selected_leg_id(self) -> str:
        return str(self._leg_selector.currentData() or "")

    def selected_principal_subleg_id(self) -> str:
        return str(self._principal_selector.currentData() or "")

    def selected_initial_room_id(self) -> str:
        return str(self._initial_room_selector.currentData() or "")

    def selected_branch_parent_id(self) -> str:
        return str(self._branch_parent_selector.currentData() or "")

    def selected_branch_origin_room_id(self) -> str:
        return str(self._branch_origin_selector.currentData() or "")

    def selected_branch_first_room_id(self) -> str:
        return str(self._branch_first_room_selector.currentData() or "")

    @staticmethod
    def _replace_combo_options(
        combo: QComboBox,
        options: list[dict[str, str]],
        selected_id: str,
    ) -> None:
        previous_identity = str(combo.currentData() or "")
        wanted_identity = str(selected_id or previous_identity)
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
                if identity == wanted_identity:
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

    def _emit_branch_parent_selection(self) -> None:
        parent_id = self.selected_branch_parent_id()
        if parent_id:
            self.branch_parent_selection_requested.emit(parent_id)

    def _emit_branch_origin_selection(self) -> None:
        origin_room_id = self.selected_branch_origin_room_id()
        if origin_room_id:
            self.branch_origin_selection_requested.emit(origin_room_id)

    def _emit_branch_first_room_selection(self) -> None:
        room_id = self.selected_branch_first_room_id()
        if room_id:
            self.branch_first_room_selection_requested.emit(room_id)

    def _emit_add_branch(self) -> None:
        room_id = self.selected_branch_first_room_id()
        parent_id = self.selected_branch_parent_id()
        origin_room_id = self.selected_branch_origin_room_id()
        if room_id and parent_id and origin_room_id:
            self.add_branch_requested.emit(
                self._branch_label_edit.text().strip(),
                parent_id,
                origin_room_id,
                room_id,
            )

    def clear_creation_labels(self) -> None:
        self._leg_label_edit.clear()
        self._principal_label_edit.clear()
        self._branch_label_edit.clear()

    def _refresh_creation_enablement(self) -> None:
        has_room = bool(self.selected_initial_room_id())
        self._add_leg_button.setEnabled(has_room)
        self._add_principal_button.setEnabled(
            has_room and bool(self.selected_leg_id())
        )
        self._add_branch_button.setEnabled(
            bool(self.selected_branch_first_room_id())
            and bool(self.selected_branch_parent_id())
            and bool(self.selected_branch_origin_room_id())
        )
