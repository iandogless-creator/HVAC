# ======================================================================
# HVAC/dev/test_hs40c_universal_pipe_section_mode_indicator_v1.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def _background_rgb(item) -> tuple[int, int, int]:
    colour = item.background().color()
    return colour.red(), colour.green(), colour.blue()


def _foreground_rgb(item) -> tuple[int, int, int]:
    colour = item.foreground().color()
    return colour.red(), colour.green(), colour.blue()


def _row(method: str, iteration: str) -> dict:
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
        "iter": iteration,
        "friction_method": method,
        "status": f"{method} pressure evidence",
    }


def _assert_mode(table, text: str, rgb: tuple[int, int, int]) -> None:
    item = table.item(0, 0)
    assert item is not None
    assert item.text() == text
    assert item.font().bold() is True
    assert item.font().pointSize() <= table.font().pointSize() + 1
    assert item.textAlignment() & Qt.AlignCenter
    assert _background_rgb(item) == rgb
    assert _foreground_rgb(item) == (
        (255, 255, 255)
        if text == "Colebrook"
        else (0, 0, 0)
    )


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()

    assert not hasattr(panel, "_common_main_leg_entry_sizing_table")

    panel._set_clean_proportioned_evidence_view_v1(
        "Basic PS",
        refresh=False,
    )
    panel._set_clean_proportioned_focused_section_rows_v1(
        [_row("Haaland", "—")]
    )
    embedded = panel._clean_proportioned_section_mode_table
    _assert_mode(embedded, "Haaland estimate", (232, 145, 55))
    assert panel._clean_proportioned_focused_section_table.columnCount() == 12
    assert panel._clean_proportioned_focused_section_table.rowCount() == 1

    panel._build_clean_proportioned_table_viewer_v1()
    panel._refresh_clean_proportioned_table_viewer_v1()
    viewer = panel._clean_proportioned_table_viewer_section_mode_table
    _assert_mode(viewer, "Haaland estimate", (232, 145, 55))

    panel._set_clean_proportioned_evidence_view_v1(
        "Proportioning",
        refresh=False,
    )
    panel._set_clean_proportioned_focused_section_rows_v1(
        [_row("colebrook", "6")]
    )
    panel._refresh_clean_proportioned_table_viewer_v1()
    _assert_mode(embedded, "Colebrook", (46, 139, 87))
    _assert_mode(viewer, "Colebrook", (46, 139, 87))
    assert panel._clean_proportioned_focused_section_table.item(0, 10).text() == "6"

    # Route filtering cannot change the explicitly selected evidence stage.
    panel._set_clean_proportioned_focused_section_rows_v1(
        [_row("colebrook", "6"), _row("Haaland", "—")]
    )
    _assert_mode(embedded, "Colebrook", (46, 139, 87))

    panel._set_clean_proportioned_evidence_view_v1("Basic PS")
    _assert_mode(embedded, "Haaland estimate", (232, 145, 55))
    _assert_mode(viewer, "Haaland estimate", (232, 145, 55))

    dialog = getattr(panel, "_clean_proportioned_table_viewer_dialog", None)
    if dialog is not None:
        dialog.close()
    panel.close()
    app.processEvents()
    print("OK — H-S40-C universal pipe-section mode indicator passed.")


if __name__ == "__main__":
    main()
