from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


class _FakeItem:
    def __init__(self, value: str) -> None:
        self._value = value

    def text(self) -> str:
        return self._value


class _FakeIndex:
    def __init__(self, row: int) -> None:
        self._row = row

    def row(self) -> int:
        return self._row


class _FakeSelectionModel:
    def __init__(self, row: int) -> None:
        self._row = row

    def selectedRows(self) -> list[_FakeIndex]:
        return [_FakeIndex(self._row)]


class _FakeSignal:
    def __init__(self) -> None:
        self.connected_to = None

    def connect(self, callback) -> None:
        self.connected_to = callback


class _FakeTable:
    def __init__(self, selected_row: int = 1) -> None:
        self.itemSelectionChanged = _FakeSignal()
        self._selected_row = selected_row
        self._items = {
            (0, 0): _FakeItem("Leg 1B Branch subleg"),
            (1, 0): _FakeItem("Leg 2B Branch subleg"),
        }

    def selectionModel(self) -> _FakeSelectionModel:
        return _FakeSelectionModel(self._selected_row)

    def currentRow(self) -> int:
        return self._selected_row

    def item(self, row: int, column: int):
        return self._items.get((row, column))


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "def _clean_proportioned_focused_route_label_v1" in source
    assert "def _set_clean_proportioned_focused_route_label_v1" in source
    assert "def _clean_proportioned_route_label_for_row_v1" in source
    assert "def _on_clean_proportioned_route_output_selection_changed_v1" in source
    assert "def _wire_clean_proportioned_route_output_selection_v1" in source
    assert "self._wire_clean_proportioned_route_output_selection_v1(table)" in source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    assert panel._clean_proportioned_focused_route_label_v1() == ""

    panel._set_clean_proportioned_focused_route_label_v1(
        "Leg 1A Common subleg"
    )
    assert panel._clean_proportioned_focused_route_label_v1() == (
        "Leg 1A Common subleg"
    )

    table = _FakeTable(selected_row=1)
    panel._clean_proportioned_route_output_table = table

    assert panel._clean_proportioned_route_label_for_row_v1(0) == (
        "Leg 1B Branch subleg"
    )
    assert panel._clean_proportioned_route_label_for_row_v1(1) == (
        "Leg 2B Branch subleg"
    )

    panel._on_clean_proportioned_route_output_selection_changed_v1()
    assert panel._clean_proportioned_focused_route_label_v1() == (
        "Leg 2B Branch subleg"
    )

    panel._wire_clean_proportioned_route_output_selection_v1(table)
    assert table.itemSelectionChanged.connected_to == (
        panel._on_clean_proportioned_route_output_selection_changed_v1
    )
    assert panel._clean_proportioned_route_output_selection_wired_v1 is True

    print("OK — H-S33-J clean route selection state passed.")


if __name__ == "__main__":
    main()
