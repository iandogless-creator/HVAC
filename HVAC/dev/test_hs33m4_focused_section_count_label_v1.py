from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "def _clean_proportioned_focused_section_count_label_v1" in source
    assert "showing {count} {suffix}" in source
    assert "no sections available" in source
    assert 'base_label="Focused route: all routes"' in source
    assert 'base_label=f"Focused route: {route_label}"' in source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    assert panel._clean_proportioned_focused_section_count_label_v1(
        base_label="Focused route: Leg 1A Common subleg",
        rows=[],
    ) == "Focused route: Leg 1A Common subleg — no sections available"

    assert panel._clean_proportioned_focused_section_count_label_v1(
        base_label="Focused route: Leg 1A Common subleg",
        rows=[{"section": "1"}],
    ) == "Focused route: Leg 1A Common subleg — showing 1 section"

    assert panel._clean_proportioned_focused_section_count_label_v1(
        base_label="Focused route: all routes",
        rows=[
            {"section": "1"},
            {"section": "2"},
            {"section": "3"},
        ],
    ) == "Focused route: all routes — showing 3 sections"

    print("OK — H-S33-M4 focused section count label passed.")


if __name__ == "__main__":
    main()
