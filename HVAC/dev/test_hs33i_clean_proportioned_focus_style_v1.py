from __future__ import annotations

from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "QAbstractItemView" in source

    assert "def _apply_clean_proportioned_table_focus_style_v1" in source
    assert "_configure_clean_proportioned_output_summary_table_v1" in source
    assert "_configure_clean_proportioned_route_output_table_v1" in source

    assert source.count(
        "self._apply_clean_proportioned_table_focus_style_v1(table)"
    ) >= 2

    assert "SelectionBehavior.SelectRows" in source
    assert "SelectionMode.SingleSelection" in source

    assert "H-S33-I clean Proportioned focus style" in source
    assert "selection-background-color: rgb(246, 215, 168)" in source
    assert "selection-color: rgb(20, 20, 20)" in source
    assert "QTableWidget::item:selected" in source

    assert "setAlternatingRowColors(True)" in source

    print("OK — H-S33-I clean Proportioned focus style passed.")


if __name__ == "__main__":
    main()
