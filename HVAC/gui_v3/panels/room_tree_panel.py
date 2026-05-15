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

        self._is_priming = False

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
    def set_rooms(self, rooms: list[object]) -> None:
        """
        Populate the room tree.

        Supported input forms
        ---------------------
        • ["room-001", "room-002"]
        • [("room-001", "R1 Airing Cupboard"), ...]

        Display labels are human-facing only.
        Qt.UserRole stores the internal room_id.
        """
        self._is_priming = True
        self._tree.blockSignals(True)

        try:
            self._tree.clear()

            for entry in rooms:
                if isinstance(entry, tuple) and len(entry) >= 2:
                    room_id = entry[0]
                    label = entry[1]
                else:
                    room_id = entry
                    label = entry

                item = QTreeWidgetItem([str(label)])
                item.setData(0, Qt.UserRole, room_id)
                self._tree.addTopLevelItem(item)

        finally:
            self._tree.blockSignals(False)
            self._is_priming = False

    def set_active_room(self, room_id: object | None) -> None:
        """
        Select the active room in the tree.

        None-safe.
        """
        self._is_priming = True
        self._tree.blockSignals(True)

        try:
            if room_id is None:
                self._tree.clearSelection()
                return

            for i in range(self._tree.topLevelItemCount()):
                item = self._tree.topLevelItem(i)

                if item is None:
                    continue

                try:
                    if item.data(0, Qt.UserRole) == room_id:
                        item.setSelected(True)

                        try:
                            self._tree.scrollToItem(item)
                        except RuntimeError:
                            # Qt item was invalidated during a concurrent refresh.
                            # Safe to ignore; next refresh will restore selection.
                            pass

                        return
                except RuntimeError:
                    # Item was deleted by Qt during refresh.
                    continue

        finally:
            self._tree.blockSignals(False)
            self._is_priming = False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _on_selection_changed(self) -> None:
        if self._is_priming:
            return

        items = self._tree.selectedItems()
        if not items:
            return

        try:
            room_id = items[0].data(0, Qt.UserRole)
        except RuntimeError:
            return

        self.room_selected.emit(room_id)