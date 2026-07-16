from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


# H-S35-B — Proportioned table viewer regression guard.


class _FakeHeader:
    def __init__(self, stretch_last: bool = False) -> None:
        self._stretch_last = stretch_last

    def stretchLastSection(self) -> bool:
        return self._stretch_last

    def setStretchLastSection(self, value: bool) -> None:
        self._stretch_last = bool(value)


class _FakeProjectionTable:
    def __init__(
            self,
            *,
            headers: list[str] | None = None,
            rows: list[list[str]] | None = None,
            current_row: int = -1,
    ) -> None:
        headers = headers or []
        rows = rows or []

        self._headers = [QTableWidgetItem(value) for value in headers]
        self._items: dict[tuple[int, int], QTableWidgetItem] = {}
        self._row_count = len(rows)
        self._column_count = len(headers)
        self._row_heights = {
            row_index: 24 + row_index
            for row_index in range(self._row_count)
        }
        self._column_widths = {
            column_index: 90 + (column_index * 10)
            for column_index in range(self._column_count)
        }
        self._header = _FakeHeader(stretch_last=True)
        self._signals_blocked = False
        self.signal_states: list[bool] = []
        self.clear_count = 0
        self.selected_row = -1
        self._current_row = current_row
        self.current_cell: tuple[int, int] | None = None
        self.scrolled_item = None

        for row_index, values in enumerate(rows):
            for column_index, value in enumerate(values):
                self._items[(row_index, column_index)] = QTableWidgetItem(
                    value
                )

    def blockSignals(self, blocked: bool) -> bool:
        previous = self._signals_blocked
        self._signals_blocked = bool(blocked)
        self.signal_states.append(bool(blocked))
        return previous

    def columnCount(self) -> int:
        return self._column_count

    def rowCount(self) -> int:
        return self._row_count

    def horizontalHeaderItem(self, column: int):
        if 0 <= column < len(self._headers):
            return self._headers[column]
        return None

    def setColumnCount(self, count: int) -> None:
        self._column_count = count

    def setHorizontalHeaderLabels(self, labels: list[str]) -> None:
        self._headers = [QTableWidgetItem(value) for value in labels]

    def setRowCount(self, count: int) -> None:
        self._row_count = count
        self._items = {
            key: value
            for key, value in self._items.items()
            if key[0] < count
        }

    def rowHeight(self, row: int) -> int:
        return self._row_heights.get(row, 24)

    def setRowHeight(self, row: int, height: int) -> None:
        self._row_heights[row] = height

    def item(self, row: int, column: int):
        return self._items.get((row, column))

    def setItem(
            self,
            row: int,
            column: int,
            item: QTableWidgetItem,
    ) -> None:
        self._items[(row, column)] = item

    def columnWidth(self, column: int) -> int:
        return self._column_widths.get(column, 90)

    def setColumnWidth(self, column: int, width: int) -> None:
        self._column_widths[column] = width

    def horizontalHeader(self) -> _FakeHeader:
        return self._header

    def clearSelection(self) -> None:
        self.clear_count += 1
        self.selected_row = -1

    def selectRow(self, row: int) -> None:
        self.selected_row = row

    def setCurrentCell(self, row: int, column: int) -> None:
        self._current_row = row
        self.current_cell = (row, column)

    def scrollToItem(self, item) -> None:
        self.scrolled_item = item

    def currentRow(self) -> int:
        return self._current_row


class _FakeCombo:
    def __init__(self, value: str) -> None:
        self._value = value
        self.set_values: list[str] = []

    def currentText(self) -> str:
        return self._value

    def setCurrentText(self, value: str) -> None:
        self._value = str(value)
        self.set_values.append(self._value)


class _FakeDialog:
    def __init__(self) -> None:
        self.show_count = 0
        self.raise_count = 0
        self.activate_count = 0

    def show(self) -> None:
        self.show_count += 1

    def raise_(self) -> None:
        self.raise_count += 1

    def activateWindow(self) -> None:
        self.activate_count += 1


def _make_panel() -> HydronicsSchematicPanel:
    return HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)


def _test_projection_copy() -> None:
    source = _FakeProjectionTable(
        headers=["Route", "Status"],
        rows=[["Leg 2B Branch subleg", "Ready"]],
    )
    target = _FakeProjectionTable()

    HydronicsSchematicPanel._copy_clean_proportioned_table_projection_v1(
        source,
        target,
    )

    assert target.columnCount() == 2
    assert target.rowCount() == 1
    assert target.horizontalHeaderItem(0).text() == "Route"
    assert target.item(0, 0).text() == "Leg 2B Branch subleg"
    assert target.item(0, 1).text() == "Ready"
    assert target.item(0, 0) is not source.item(0, 0)
    assert not bool(target.item(0, 0).flags() & Qt.ItemIsEditable)
    assert target.rowHeight(0) == source.rowHeight(0)
    assert target.columnWidth(1) == source.columnWidth(1)
    assert target.horizontalHeader().stretchLastSection() is True
    assert target.signal_states == [True, False]


def _test_two_surface_route_selection() -> None:
    rows = [
        ["Leg 1A Common subleg"],
        ["Leg 2B Branch subleg"],
    ]
    embedded = _FakeProjectionTable(
        headers=["Route"],
        rows=rows,
    )
    viewer = _FakeProjectionTable(
        headers=["Route"],
        rows=rows,
        current_row=1,
    )

    panel = _make_panel()
    panel._clean_proportioned_route_output_table = embedded
    panel._clean_proportioned_table_viewer_route_table = viewer

    panel._sync_clean_proportioned_route_selection_v1(
        "Leg 2B Branch subleg"
    )

    assert embedded.selected_row == 1
    assert viewer.selected_row == 1
    assert embedded.current_cell == (1, 0)
    assert viewer.current_cell == (1, 0)
    assert embedded.signal_states == [True, False]
    assert viewer.signal_states == [True, False]

    refresh_calls: list[str] = []
    panel._refresh_clean_proportioned_focused_section_view_v1 = (
        lambda: refresh_calls.append("sections")
    )
    panel._on_clean_proportioned_table_viewer_route_selection_changed_v1()

    assert panel._clean_proportioned_focused_route_label_v1() == (
        "Leg 2B Branch subleg"
    )
    assert embedded.selected_row == 1
    assert viewer.selected_row == 1
    assert refresh_calls == ["sections"]

    panel._sync_clean_proportioned_route_selection_v1("")
    assert embedded.selected_row == -1
    assert viewer.selected_row == -1


def _test_view_mode_mirroring() -> None:
    panel = _make_panel()
    combo = _FakeCombo("Selected route only")
    panel._clean_proportioned_section_view_mode_combo = combo

    refresh_calls: list[str] = []
    panel._refresh_clean_proportioned_focused_section_view_v1 = (
        lambda: refresh_calls.append("sections")
    )

    panel._on_clean_proportioned_table_viewer_mode_changed_v1("All routes")
    assert combo.currentText() == "All routes"
    assert combo.set_values == ["All routes"]

    panel._on_clean_proportioned_table_viewer_mode_changed_v1("All routes")
    assert refresh_calls == ["sections"]


def _test_show_refreshes_reusable_dialog() -> None:
    panel = _make_panel()
    created_dialogs: list[_FakeDialog] = []
    refresh_calls: list[str] = []

    def build_dialog() -> None:
        if getattr(panel, "_clean_proportioned_table_viewer_dialog", None):
            return

        dialog = _FakeDialog()
        created_dialogs.append(dialog)
        panel._clean_proportioned_table_viewer_dialog = dialog

    panel._build_clean_proportioned_table_viewer_v1 = build_dialog
    panel._refresh_clean_proportioned_table_viewer_v1 = (
        lambda: refresh_calls.append("viewer")
    )

    panel._show_clean_proportioned_table_viewer_v1()
    panel._show_clean_proportioned_table_viewer_v1()

    assert len(created_dialogs) == 1
    assert refresh_calls == ["viewer", "viewer"]
    assert created_dialogs[0].show_count == 2
    assert created_dialogs[0].raise_count == 2
    assert created_dialogs[0].activate_count == 2


def _test_named_section_preference() -> None:
    panel = _make_panel()

    named = {
        "route": "Leg 2A Common subleg",
        "section": "1",
        "from": "Common main / leg entry",
        "to": "L2A-R01",
        "flow_kg_s": "0.1794 kg/s",
    }
    matching_fallback = {
        **named,
        "section": "—",
    }
    unmatched_fallback = {
        "route": "Leg 2B Branch subleg",
        "section": "—",
        "from": "L2B-R04",
        "to": "L2B-R05",
        "flow_kg_s": "0.0096 kg/s",
    }

    result = panel._clean_proportioned_prefer_engineering_section_rows_v1(
        [named, matching_fallback, unmatched_fallback]
    )

    assert result == [named, unmatched_fallback]


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    for expected in (
        "H-S35-A2 — fixed table-viewer launcher",
        "H-S35-A3: prefer named sections over matching fallbacks",
        "def _build_clean_proportioned_table_viewer_v1",
        "def _copy_clean_proportioned_table_projection_v1",
        "def _sync_clean_proportioned_route_selection_v1",
        "def _on_clean_proportioned_table_viewer_route_selection_changed_v1",
        "def _on_clean_proportioned_table_viewer_mode_changed_v1",
        "def _show_clean_proportioned_table_viewer_v1",
    ):
        assert expected in source

    assert 'if getattr(self, "_clean_proportioned_table_viewer_dialog", None)' in source
    assert "dialog.show()" in source
    assert "dialog.raise_()" in source
    assert "dialog.activateWindow()" in source

    _test_projection_copy()
    _test_two_surface_route_selection()
    _test_view_mode_mirroring()
    _test_show_refreshes_reusable_dialog()
    _test_named_section_preference()

    print("OK — H-S35-B Proportioned table viewer regression guard passed.")


if __name__ == "__main__":
    main()
