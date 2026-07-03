from __future__ import annotations

from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


def test_route_section_contribution_map_uses_section_id() -> None:
    section_a = SimpleNamespace(section_id="section-001")
    section_b = SimpleNamespace(section_id="section-002")
    section_blank = SimpleNamespace(section_id="")

    projection = SimpleNamespace(
        rows=(
            SimpleNamespace(sections=(section_a, section_blank)),
            SimpleNamespace(sections=(section_b,)),
        )
    )

    by_id = (
        HydronicsSchematicPanelAdapter
        ._route_pressure_section_contribution_by_id_v1(projection)
    )

    assert by_id["section-001"] is section_a
    assert by_id["section-002"] is section_b
    assert "" not in by_id


if __name__ == "__main__":
    test_route_section_contribution_map_uses_section_id()
    print("OK — H-S29-G route section metadata map passed.")
