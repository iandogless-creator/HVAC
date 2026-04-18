# ======================================================================
# HVAC/gui_v3/common/overlay_controller.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QTableWidget

from HVAC.gui_v3.common.edit_context import EditContext


class OverlayController:
    """
    Single authority for all editor overlays.
    """

    def __init__(self, table: QTableWidget, parent: QWidget):
        self._table = table
        self._parent = parent

        self._active_ctx: Optional[EditContext] = None
        self._editor: Optional[QWidget] = None
        self._mode: str = "anchored"   # "anchored" | "floating"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def activate(self, ctx: EditContext) -> None:
        self._clear()

        self._active_ctx = ctx
        self._editor = self._create_editor(ctx)

        if self._editor is None:
            return

        self._editor.setParent(self._table.viewport())
        self._editor.show()
        self._position_editor()

    def clear(self) -> None:
        self._clear()

    def current_editor(self) -> Optional[QWidget]:
        return self._editor

    def current_context(self) -> Optional[EditContext]:
        return self._active_ctx

    def set_mode(self, mode: str) -> None:
        if mode not in {"anchored", "floating"}:
            return
        self._mode = mode
        self._position_editor()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _clear(self) -> None:
        if self._editor is not None:
            self._editor.hide()
            self._editor.deleteLater()

        self._editor = None
        self._active_ctx = None

    def _create_editor(self, ctx: EditContext) -> Optional[QWidget]:
        if ctx.kind == "geometry":
            return self._create_geometry_editor(ctx)
        if ctx.kind == "ach":
            return self._create_ach_editor(ctx)
        if ctx.kind == "cell":
            return self._create_cell_editor(ctx)
        return None

    def _position_editor(self) -> None:
        if self._editor is None or self._active_ctx is None:
            return

        if self._mode != "anchored":
            return

        row = self._active_ctx.row
        column = self._active_ctx.column

        if row is None or column is None:
            # fallback for non-cell editors
            self._editor.move(12, 12)
            return

        index = self._table.model().index(row, column)
        rect = self._table.visualRect(index)

        x = rect.right() + 6
        y = rect.top()
        self._editor.move(x, y)

    # ------------------------------------------------------------------
    # Editor factories
    # ------------------------------------------------------------------
    def _create_geometry_editor(self, ctx: EditContext) -> QWidget:
        from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel
        return GeometryMiniPanel(parent=self._parent)

    def _create_ach_editor(self, ctx: EditContext) -> QWidget:
        from PySide6.QtWidgets import QDoubleSpinBox

        spin = QDoubleSpinBox(self._parent)
        spin.setRange(0.0, 20.0)
        spin.setDecimals(2)
        spin.setSingleStep(0.10)
        return spin

    def _create_cell_editor(self, ctx: EditContext) -> QWidget:
        from PySide6.QtWidgets import QDoubleSpinBox

        spin = QDoubleSpinBox(self._parent)
        spin.setRange(0.0, 999999.0)
        spin.setDecimals(3)
        spin.setSingleStep(0.10)
        return spin

