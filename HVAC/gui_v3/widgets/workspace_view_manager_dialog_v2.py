from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from HVAC.gui_v3.context.gui_settings import GuiSettings


class WorkspaceViewManagerDialogV2(QDialog):
    """Compact editor for persistent named-view membership and placement."""

    views_changed = Signal(str)
    view_selected = Signal(str)

    def __init__(
            self,
            *,
            settings: GuiSettings,
            panel_rows: tuple[tuple[str, str], ...],
            parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._panel_rows = tuple(panel_rows)
        self._refreshing = False

        self.setWindowTitle("Views")
        self.setMinimumWidth(620)
        self.resize(680, 560)

        root = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("View", self))

        self._view_combo = QComboBox(self)
        self._view_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self._view_combo.currentIndexChanged.connect(
            self._on_selected_view_changed_v2
        )
        top.addWidget(self._view_combo, 1)

        self._new_button = self._tool_button_v2(
            icon=QStyle.StandardPixmap.SP_FileDialogNewFolder,
            tooltip="New view",
            slot=self._create_view_v2,
        )
        self._rename_button = self._tool_button_v2(
            icon=QStyle.StandardPixmap.SP_FileDialogDetailedView,
            tooltip="Rename view",
            slot=self._rename_view_v2,
        )
        self._delete_button = self._tool_button_v2(
            icon=QStyle.StandardPixmap.SP_TrashIcon,
            tooltip="Delete view",
            slot=self._delete_view_v2,
        )
        self._new_button.setEnabled(bool(self._panel_rows))
        top.addWidget(self._new_button)
        top.addWidget(self._rename_button)
        top.addWidget(self._delete_button)
        root.addLayout(top)

        self._table = QTableWidget(0, 5, self)
        self._table.setHorizontalHeaderLabels((
            "Include",
            "Panel",
            "Main",
            "Side",
            "Bottom",
        ))
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in (2, 3, 4):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        root.addWidget(self._table, 1)

        note = QLabel("Changes save immediately.", self)
        note.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(note)

        selected = self._settings.last_workspace_view_v2()["view_id"]
        self._refresh_views_v2(select_view_id=selected)

    def _tool_button_v2(self, *, icon, tooltip: str, slot) -> QToolButton:
        button = QToolButton(self)
        button.setIcon(self.style().standardIcon(icon))
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setAutoRaise(True)
        button.clicked.connect(slot)
        return button

    def _current_view_id_v2(self) -> str:
        return str(self._view_combo.currentData() or "")

    def _refresh_views_v2(self, *, select_view_id: str = "") -> None:
        self._refreshing = True
        try:
            views = self._settings.workspace_views_v2()
            wanted = str(select_view_id or self._current_view_id_v2())
            self._view_combo.blockSignals(True)
            self._view_combo.clear()
            selected_index = 0
            for index, view in enumerate(views):
                self._view_combo.addItem(view["name"], view["view_id"])
                if view["view_id"] == wanted:
                    selected_index = index
            if views:
                self._view_combo.setCurrentIndex(selected_index)
            self._view_combo.blockSignals(False)
            self._delete_button.setEnabled(len(views) > 1)
            self._rename_button.setEnabled(bool(views))
            self._refresh_panel_rows_v2()
        finally:
            self._view_combo.blockSignals(False)
            self._refreshing = False

    def _refresh_panel_rows_v2(self) -> None:
        view = self._settings.workspace_view_v2(
            self._current_view_id_v2()
        )
        panels = dict(view.get("panels") or {}) if view else {}
        self._table.setRowCount(len(self._panel_rows))

        icons = {
            "main": QStyle.StandardPixmap.SP_TitleBarMaxButton,
            "side": QStyle.StandardPixmap.SP_ArrowRight,
            "bottom": QStyle.StandardPixmap.SP_ArrowDown,
        }
        tooltips = {
            "main": "Main — large working panel",
            "side": "Side — right-hand panel or tab",
            "bottom": "Bottom — lower panel or tab",
        }
        for row, (panel_id, panel_label) in enumerate(self._panel_rows):
            included = panel_id in panels
            placement = panels.get(panel_id, "side")

            checkbox = QCheckBox(self._table)
            checkbox.setChecked(included)
            checkbox.setToolTip("Include in view")
            checkbox.setAccessibleName(
                f"Include {panel_label} in view"
            )
            checkbox.toggled.connect(
                lambda checked, selected_panel_id=panel_id: (
                    self._set_panel_included_v2(
                        selected_panel_id, checked
                    )
                )
            )
            self._table.setCellWidget(row, 0, checkbox)

            label_item = QTableWidgetItem(panel_label)
            label_item.setData(Qt.ItemDataRole.UserRole, panel_id)
            self._table.setItem(row, 1, label_item)

            for column, option in enumerate(
                    ("main", "side", "bottom"), start=2
            ):
                button = QToolButton(self._table)
                button.setIcon(self.style().standardIcon(icons[option]))
                button.setToolTip(tooltips[option])
                button.setAccessibleName(
                    f"Place {panel_label} at {option}"
                )
                button.setCheckable(True)
                button.setAutoRaise(True)
                button.setEnabled(included)
                button.setChecked(included and placement == option)
                button.clicked.connect(
                    lambda _checked=False,
                    selected_panel_id=panel_id,
                    selected_option=option: self._set_panel_placement_v2(
                        selected_panel_id, selected_option
                    )
                )
                self._table.setCellWidget(row, column, button)

    def _persist_and_refresh_v2(self, *, view_id: str) -> None:
        self._settings.save()
        self._refresh_views_v2(select_view_id=view_id)
        self.views_changed.emit(view_id)

    def _on_selected_view_changed_v2(self, _index: int) -> None:
        if not self._refreshing:
            self._refresh_panel_rows_v2()
            view_id = self._current_view_id_v2()
            if view_id:
                self.view_selected.emit(view_id)

    def _set_panel_included_v2(
            self,
            panel_id: str,
            included: bool,
    ) -> None:
        if self._refreshing:
            return
        view_id = self._current_view_id_v2()
        view = self._settings.workspace_view_v2(view_id)
        panels = dict(view.get("panels") or {}) if view else {}
        placement = "side"
        if included and sum(
            value == "side" for value in panels.values()
        ) >= 2:
            placement = "bottom"
        if self._settings.set_workspace_view_panel_v2(
            view_id=view_id,
            panel_id=panel_id,
            included=included,
            placement=placement,
        ):
            self._persist_and_refresh_v2(view_id=view_id)
            return
        self._refresh_views_v2(select_view_id=view_id)
        QMessageBox.information(
            self,
            "Views",
            "Keep one Main panel, with up to two Side and two Bottom panels.",
        )

    def _set_panel_placement_v2(
            self,
            panel_id: str,
            placement: str,
    ) -> None:
        if self._refreshing:
            return
        view_id = self._current_view_id_v2()
        if self._settings.set_workspace_view_panel_v2(
            view_id=view_id,
            panel_id=panel_id,
            included=True,
            placement=placement,
        ):
            self._persist_and_refresh_v2(view_id=view_id)
            return
        self._refresh_views_v2(select_view_id=view_id)
        QMessageBox.information(
            self,
            "Views",
            "Side and Bottom can each contain up to two panels.",
        )

    def _create_view_v2(self) -> None:
        if not self._panel_rows:
            return
        suggested = f"View {len(self._settings.workspace_views_v2()) + 1}"
        name, accepted = QInputDialog.getText(
            self,
            "New View",
            "Name",
            text=suggested,
        )
        if not accepted:
            return
        first_panel_id = self._panel_rows[0][0]
        view_id = self._settings.create_workspace_view_v2(
            name=name,
            panels={first_panel_id: "main"},
        )
        if view_id is None:
            QMessageBox.information(
                self, "Views", "Use a unique view name."
            )
            return
        self._persist_and_refresh_v2(view_id=view_id)

    def _rename_view_v2(self) -> None:
        view_id = self._current_view_id_v2()
        view = self._settings.workspace_view_v2(view_id)
        if view is None:
            return
        name, accepted = QInputDialog.getText(
            self,
            "Rename View",
            "Name",
            text=view["name"],
        )
        if not accepted:
            return
        if not self._settings.rename_workspace_view_v2(view_id, name):
            QMessageBox.information(
                self, "Views", "Use a unique view name."
            )
            return
        self._persist_and_refresh_v2(view_id=view_id)

    def _delete_view_v2(self) -> None:
        view_id = self._current_view_id_v2()
        view = self._settings.workspace_view_v2(view_id)
        if view is None:
            return
        answer = QMessageBox.question(
            self,
            "Delete View",
            f"Delete {view['name']}?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if not self._settings.delete_workspace_view_v2(view_id):
            QMessageBox.information(
                self, "Views", "The final view cannot be deleted."
            )
            return
        next_view_id = self._settings.workspace_views_v2()[0]["view_id"]
        self._persist_and_refresh_v2(view_id=next_view_id)
