from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "QComboBox" in source
    assert "Pipe-section view:" in source
    assert "Selected route only" in source
    assert "All routes" in source

    assert "_clean_proportioned_section_view_controls" in source
    assert "_clean_proportioned_focused_section_table" in source
    assert "Focused route / subleg sections — read-only" in source

    assert "def _clean_proportioned_section_view_mode_v1" in source
    assert "def _set_clean_proportioned_section_view_mode_v1" in source
    assert "def _on_clean_proportioned_section_view_mode_changed_v1" in source
    assert "def _configure_clean_proportioned_focused_section_table_v1" in source
    assert "def _set_clean_proportioned_focused_section_rows_v1" in source
    assert "def _refresh_clean_proportioned_focused_section_view_v1" in source

    assert "self._refresh_clean_proportioned_focused_section_view_v1()" in source

    for heading in [
        "Route",
        "Section",
        "From",
        "To",
        "Flow kg/s",
        "Pipe DN",
        "Δp/m",
        "Length",
        "K",
        "Section Δp",
        "Status",
    ]:
        assert heading in source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    assert panel._clean_proportioned_section_view_mode_v1() == (
        "Selected route only"
    )

    panel._set_clean_proportioned_section_view_mode_v1("All routes")
    assert panel._clean_proportioned_section_view_mode_v1() == "All routes"

    panel._set_clean_proportioned_section_view_mode_v1("bad mode")
    assert panel._clean_proportioned_section_view_mode_v1() == (
        "Selected route only"
    )

    print("OK — H-S33-K focused section shell passed.")


if __name__ == "__main__":
    main()
