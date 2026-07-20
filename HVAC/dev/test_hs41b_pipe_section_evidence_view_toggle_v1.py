from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.dev.test_hs37b5_basic_vs_proportioning_evidence_v1 import (
    _test_adapter_evidence_keys,
)


def _row() -> dict:
    return {
        "route": "Heating Leg 1 / Leg 1A Common subleg",
        "section": "2",
        "from": "L1A-R01",
        "to": "L1A-R02",
        "flow_kg_s": "0.1483 kg/s",
        "pipe_dn": "15 mm",
        "dp_per_m": "1359.4",
        "length": "4.00 m",
        "k": "3.50",
        "section_dp": "7627.2 Pa",
        "iter": "6",
        "friction_method": "colebrook",
        "basic_pipe_dn": "15 mm",
        "basic_dp_per_m": "1100.0",
        "basic_friction_method": "Haaland",
        "proportioning_pipe_dn": "15 mm",
        "proportioning_dp_per_m": "1359.4",
        "proportioning_iter": "6",
        "proportioning_friction_method": "colebrook",
        "status": "Prepared Proportioning evidence",
    }


def _assert_button_colours(button, *, background: str, foreground: str) -> None:
    style = str(button.styleSheet() or "").replace(" ", "")
    assert f"background-color:{background}" in style
    assert f"color:{foreground}" in style


def _text(table, row: int, column: int) -> str:
    item = table.item(row, column)
    assert item is not None
    return item.text()


def main() -> None:
    app = QApplication.instance() or QApplication([])
    adapter_row = _test_adapter_evidence_keys()
    assert adapter_row["basic_dp_per_m"] == "1100.0"
    assert adapter_row["basic_friction_method"] == "Haaland"

    panel = HydronicsSchematicPanel()
    row = _row()

    assert panel._clean_proportioned_evidence_view_v1() == "Proportioning"
    _assert_button_colours(
        panel._clean_proportioned_evidence_view_button,
        background="rgb(46,139,87)",
        foreground="white",
    )
    panel._set_clean_proportioned_focused_section_rows_v1([row])
    table = panel._clean_proportioned_focused_section_table
    indicator = panel._clean_proportioned_section_mode_table
    assert indicator.item(0, 0).text() == "Colebrook"
    assert _text(table, 0, 5) == "15 mm"
    assert _text(table, 0, 6) == "1359.4"
    assert _text(table, 0, 10) == "6"

    panel._set_clean_proportioned_evidence_view_v1(
        "Basic PS",
        refresh=False,
    )
    panel._set_clean_proportioned_focused_section_rows_v1([row])
    assert indicator.item(0, 0).text() == "Haaland estimate"
    _assert_button_colours(
        panel._clean_proportioned_evidence_view_button,
        background="rgb(232,145,55)",
        foreground="black",
    )
    assert _text(table, 0, 5) == "15 mm"
    assert _text(table, 0, 6) == "1100.0"
    assert _text(table, 0, 8) == "—"
    assert _text(table, 0, 9) == "—"
    assert _text(table, 0, 10) == "—"

    # Changing the displayed route rows does not select Proportioning.
    panel._set_clean_proportioned_focused_section_rows_v1([dict(row)])
    assert panel._clean_proportioned_evidence_view_v1() == "Basic PS"
    assert indicator.item(0, 0).text() == "Haaland estimate"

    panel._build_clean_proportioned_table_viewer_v1()
    panel._refresh_clean_proportioned_table_viewer_v1()
    viewer_button = panel._clean_proportioned_table_viewer_evidence_button
    viewer_indicator = (
        panel._clean_proportioned_table_viewer_section_mode_table
    )
    assert viewer_button.text() == "Basic PS"
    assert viewer_button.isChecked() is False
    _assert_button_colours(
        viewer_button,
        background="rgb(232,145,55)",
        foreground="black",
    )
    assert viewer_indicator.item(0, 0).text() == "Haaland estimate"

    panel._set_clean_proportioned_evidence_view_v1("Proportioning")
    assert panel._clean_proportioned_evidence_view_button.text() == (
        "Proportioning"
    )
    assert viewer_button.text() == "Proportioning"
    assert viewer_button.isChecked() is True
    _assert_button_colours(
        viewer_button,
        background="rgb(46,139,87)",
        foreground="white",
    )
    assert viewer_indicator.item(0, 0).text() == "Colebrook"

    dialog = getattr(panel, "_clean_proportioned_table_viewer_dialog", None)
    if dialog is not None:
        dialog.close()
    panel.close()
    app.quit()
    print("OK — H-S41-B pipe-section evidence-view toggle passed.")


if __name__ == "__main__":
    main()
