# ======================================================================
# HVAC/gui_v3/panels/heat_loss_panel.py
# ======================================================================

"""
HVACgooee — GUI v3
Heat-Loss Panel (Worksheet + Results Substrate)

ARCHITECTURE (LOCKED)
--------------------
This panel is a worksheet surface with two visual layers:

• Results substrate (read-only, post-run truth)
• Worksheet overlay (editable intent, barely opaque)

This panel:
• Displays values only
• Emits override intent
• Shows project-level status
• Never owns authority
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from PySide6.QtCore import Qt, QModelIndex, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QStyledItemDelegate,
)
from PySide6.QtCore import QAbstractTableModel


# ----------------------------------------------------------------------
# View-local row (NON-authoritative)
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class HeatLossWorksheetRow:
    room_id: str
    element_id: str
    element_name: str
    element_kind: str

    derived_area_m2: Optional[float] = None
    derived_delta_t_k: Optional[float] = None
    derived_u_value_w_m2k: Optional[float] = None

    result_area_m2: Optional[float] = None
    result_delta_t_k: Optional[float] = None
    result_u_value_w_m2k: Optional[float] = None
    result_loss_w: Optional[float] = None

    override_area_m2: Optional[float] = None
    override_delta_t_k: Optional[float] = None
    override_u_value_w_m2k: Optional[float] = None


# ----------------------------------------------------------------------
# Overlay delegate (display only)
# ----------------------------------------------------------------------
class _OverlayDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        payload = index.data(Qt.UserRole)
        if not payload:
            return super().paint(painter, option, index)

        override = payload.get("override")
        substrate = payload.get("substrate")

        if override is None:
            return super().paint(painter, option, index)

        painter.save()
        super().paint(painter, option, index)

        rect = option.rect.adjusted(3, 2, -3, -2)

        if substrate is not None:
            painter.setOpacity(0.35)
            painter.drawText(
                rect,
                Qt.AlignVCenter | Qt.AlignLeft,
                f"{substrate:.2f}",
            )

        painter.setOpacity(1.0)
        painter.fillRect(rect, QColor(255, 255, 255, 35))
        painter.drawText(
            rect,
            Qt.AlignVCenter | Qt.AlignLeft,
            f"{override:.2f}",
        )

        painter.restore()


# ----------------------------------------------------------------------
# Edit delegate (emits intent only)
# ----------------------------------------------------------------------
class _EditDelegate(QStyledItemDelegate):
    def __init__(self, panel: "HeatLossPanelV3") -> None:
        super().__init__()
        self._panel = panel

    def setModelData(self, editor, model, index) -> None:
        try:
            value = float(editor.text())
        except Exception:
            return

        row: HeatLossWorksheetRow = model._rows[index.row()]  # type: ignore
        col = index.column()

        field_map = {
            model.COL_AREA: "area_m2",
            model.COL_DT: "delta_t_k",
            model.COL_U: "u_value",
        }

        field = field_map.get(col)
        if field is None:
            return

        self._panel.override_intent.emit(
            row.room_id,
            row.element_id,
            field,
            value,
        )


# ----------------------------------------------------------------------
# Table model (view-only)
# ----------------------------------------------------------------------
class _HeatLossTableModel(QAbstractTableModel):

    HEADERS = ["Element", "Kind", "Area (m²)", "ΔT (K)", "U (W/m²K)", "Loss (W)"]

    COL_ELEMENT = 0
    COL_KIND = 1
    COL_AREA = 2
    COL_DT = 3
    COL_U = 4
    COL_LOSS = 5

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[HeatLossWorksheetRow] = []

    def set_rows(self, rows: Sequence[HeatLossWorksheetRow]) -> None:
        self.modelReset.emit()
        self._rows = list(rows)

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def flags(self, index):
        base = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() in (self.COL_AREA, self.COL_DT, self.COL_U):
            return base | Qt.ItemIsEditable
        return base

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = self._rows[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            return self._display_value(row, col)

        if role == Qt.UserRole:
            return self._overlay_payload(row, col)

        return None

    def _display_value(self, row: HeatLossWorksheetRow, col: int):
        if col == self.COL_ELEMENT:
            return row.element_name
        if col == self.COL_KIND:
            return row.element_kind
        if col == self.COL_AREA:
            return self._top(row.override_area_m2, row.result_area_m2, row.derived_area_m2)
        if col == self.COL_DT:
            return self._top(row.override_delta_t_k, row.result_delta_t_k, row.derived_delta_t_k)
        if col == self.COL_U:
            return self._top(row.override_u_value_w_m2k, row.result_u_value_w_m2k, row.derived_u_value_w_m2k)
        if col == self.COL_LOSS:
            return "" if row.result_loss_w is None else f"{row.result_loss_w:.2f}"
        return ""

    @staticmethod
    def _top(override, substrate, derived):
        val = override if override is not None else substrate if substrate is not None else derived
        return "" if val is None else f"{val:.2f}"

    @staticmethod
    def _overlay_payload(row: HeatLossWorksheetRow, col: int):
        if col == _HeatLossTableModel.COL_AREA:
            return {"override": row.override_area_m2, "substrate": row.result_area_m2}
        if col == _HeatLossTableModel.COL_DT:
            return {"override": row.override_delta_t_k, "substrate": row.result_delta_t_k}
        if col == _HeatLossTableModel.COL_U:
            return {"override": row.override_u_value_w_m2k, "substrate": row.result_u_value_w_m2k}
        return None


# ----------------------------------------------------------------------
# Panel
# ----------------------------------------------------------------------
class HeatLossPanelV3(QWidget):

    override_intent = Signal(str, str, str, object)
    run_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._status = QLabel("Not calculated")
        self._run_btn = QPushButton("Run heat-loss")
        self._run_btn.setEnabled(False)

        self._table = QTableView()
        self._model = _HeatLossTableModel()
        self._table.setModel(self._model)

        self._table.setItemDelegate(_OverlayDelegate())
        self._table.setItemDelegateForColumn(
            _HeatLossTableModel.COL_AREA, _EditDelegate(self)
        )
        self._table.setItemDelegateForColumn(
            _HeatLossTableModel.COL_DT, _EditDelegate(self)
        )
        self._table.setItemDelegateForColumn(
            _HeatLossTableModel.COL_U, _EditDelegate(self)
        )

        self._build_ui()
        self._wire()

    def set_rows(self, rows: Sequence[HeatLossWorksheetRow]) -> None:
        self._model.set_rows(rows)
        self._table.resizeColumnsToContents()

    def set_status_text(self, text: str) -> None:
        self._status.setText(text)

    def set_run_enabled(self, enabled: bool) -> None:
        self._run_btn.setEnabled(enabled)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(QLabel("Heat-Loss Worksheet"))
        header.addStretch()
        header.addWidget(QLabel("Status:"))
        header.addWidget(self._status)
        header.addWidget(self._run_btn)

        root.addLayout(header)
        root.addWidget(self._table)

    def _wire(self) -> None:
        self._run_btn.clicked.connect(self.run_clicked.emit)


__all__ = ["HeatLossPanelV3", "HeatLossWorksheetRow"]
