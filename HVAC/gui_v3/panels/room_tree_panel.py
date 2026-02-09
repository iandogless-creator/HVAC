# ======================================================================
# HVAC/gui_v3/panels/room_tree_panel.py
# ======================================================================
# HVACgooee — RoomTreePanel (GUI v3)
# Phase: E-A — Room Selection
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
)


class RoomTreePanel(QWidget):
    """
    RoomTreePanel — GUI v3 (Observer)

    Phase E-A responsibilities:
    • Display rooms
    • Allow single room selection
    • Emit selected room_id

    No authority.
    No calculations.
    No inference.
    """

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    room_selected = Signal(object)  # room_id (opaque)

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(240)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        title = QLabel("Rooms")
        title.setStyleSheet("font-weight:600;")
        root.addWidget(title)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(False)
        self._tree.setSelectionMode(QTreeWidget.SingleSelection)

        self._tree.itemSelectionChanged.connect(
            self._on_selection_changed
        )

        root.addWidget(self._tree)

    # ------------------------------------------------------------------
    # Adapter-facing API (Phase E-A)
    # ------------------------------------------------------------------
    def set_rooms(self, rooms: list[tuple[object, str]]) -> None:
        """
        Populate the tree with rooms.

        Parameters
        ----------
        rooms:
            List of (room_id, room_name)
        """
        self._tree.clear()

        for room_id, name in rooms:
            item = QTreeWidgetItem([name])
            item.setData(0, Qt.UserRole, room_id)
            self._tree.addTopLevelItem(item)

    def set_active_room(self, room_id: object | None) -> None:
        """
        Select the active room in the tree.

        None-safe.
        """
        if room_id is None:
            self._tree.clearSelection()
            return

        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == room_id:
                item.setSelected(True)
                self._tree.scrollToItem(item)
                return

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _on_selection_changed(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            return

        room_id = items[0].data(0, Qt.UserRole)
        self.room_selected.emit(room_id)
