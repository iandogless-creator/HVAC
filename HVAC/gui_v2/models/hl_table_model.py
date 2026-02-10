from enum import IntEnum


class HLColumn(IntEnum):
    ROOM = 0
    METHOD = 1
    STATUS = 2

    QT_CALC = 3
    QF = 4
    QV = 5

    QT_OVERRIDE = 6
    NOTES = 7
"""
hl_table_model.py
-----------------

HVACgooee — Heat-Loss Table Model (v1)

• GUI-only
• DTO-backed
• No calculations
• Explicit edit rules
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
)

from HVAC.heatloss.dto.room_heatloss_row_dto import RoomHeatLossRowDTO
from .hl_table_columns import HLColumn


# ------------------------------------------------------------------
# Column headers (LOCKED)
# ------------------------------------------------------------------

HEADERS = {
    HLColumn.ROOM: "Room",
    HLColumn.METHOD: "HL Path",
    HLColumn.STATUS: "Status",

    HLColumn.QT_CALC: "QT (calc) [W]",
    HLColumn.QF: "Qf [W]",
    HLColumn.QV: "Qv [W]",

    HLColumn.QT_OVERRIDE: "QT (override) [W]",
    HLColumn.NOTES: "Notes",
}


class HLTableModel(QAbstractTableModel):
    def __init__(self, rows: Optional[List[RoomHeatLossRowDTO]] = None):
        super().__init__()
        self._rows: List[RoomHeatLossRowDTO] = rows or []

    # ------------------------------------------------------------------
    # Public, read-only access
    # ------------------------------------------------------------------

    def rows(self) -> Sequence[RoomHeatLossRowDTO]:
        """Read-only view of table rows."""
        return tuple(self._rows)

    def set_rows(self, rows: list[RoomHeatLossRowDTO]):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    # ------------------------------------------------------------------
    # Qt required overrides
    # ------------------------------------------------------------------

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(HLColumn)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            try:
                return HEADERS[HLColumn(section)]
            except (KeyError, ValueError):
                return None

        return str(section + 1)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        try:
            col = HLColumn(index.column())
        except ValueError:
            return None

        row = self._rows[index.row()]

        # ---------------- Display ----------------
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._display_value(row, col)

        # ---------------- Alignment ----------------
        if role == Qt.TextAlignmentRole:
            if col in (
                HLColumn.QT_CALC,
                HLColumn.QF,
                HLColumn.QV,
                HLColumn.QT_OVERRIDE,
            ):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        # ---------------- Tooltips ----------------
        if role == Qt.ToolTipRole:
            return self._tooltip(row, col)

        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        try:
            col = HLColumn(index.column())
        except ValueError:
            return Qt.NoItemFlags

        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        if col in (HLColumn.QT_OVERRIDE, HLColumn.NOTES):
            flags |= Qt.ItemIsEditable

        return flags

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False

        try:
            col = HLColumn(index.column())
        except ValueError:
            return False

        row = self._rows[index.row()]

        if col == HLColumn.QT_OVERRIDE:
            try:
                row.qt_override_w = (
                    float(value) if value not in ("", None) else None
                )
            except (TypeError, ValueError):
                return False

            self.dataChanged.emit(index, index)
            return True

        if col == HLColumn.NOTES:
            row.notes = str(value)
            self.dataChanged.emit(index, index)
            return True

        return False

    # ------------------------------------------------------------------
    # Helpers (NO LOGIC)
    # ------------------------------------------------------------------

    def _display_value(self, row: RoomHeatLossRowDTO, col: HLColumn):
        if col == HLColumn.ROOM:
            return row.room_name
        if col == HLColumn.METHOD:
            return row.hl_method
        if col == HLColumn.STATUS:
            if row.is_stale:
                return "Stale"
            if row.has_override:
                return "Overridden"
            return "OK"

        if col == HLColumn.QT_CALC:
            return f"{row.qt_calc_w:.0f}"
        if col == HLColumn.QF:
            return f"{row.qf_w:.0f}"
        if col == HLColumn.QV:
            return f"{row.qv_w:.0f}"

        if col == HLColumn.QT_OVERRIDE:
            return "" if row.qt_override_w is None else f"{row.qt_override_w:.0f}"

        if col == HLColumn.NOTES:
            return row.notes

        return None

    def _tooltip(self, row: RoomHeatLossRowDTO, col: HLColumn):
        if col == HLColumn.QT_CALC:
            return "Calculated by Heat-Loss engine"
        if col == HLColumn.QT_OVERRIDE:
            return "Optional user override (replaces calculated QT)"
        if col == HLColumn.STATUS and row.has_override:
            return f"Effective QT: {row.qt_effective_w:.0f} W"
        return None
