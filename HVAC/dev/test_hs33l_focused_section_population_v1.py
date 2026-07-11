from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "def _normalise_clean_proportioned_section_source_row_v1" in source
    assert "def set_clean_proportioned_focused_section_source_rows_v1" in source
    assert "def _clean_proportioned_section_source_rows_v1" in source
    assert "def _clean_proportioned_section_rows_for_view_v1" in source
    assert "def _clean_proportioned_route_matches_section_row_v1" in source
    assert "No matching pipe-section rows available" in source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    raw = {
        "Route": "Leg 1A Common subleg",
        "Order": "3",
        "From": "Boiler / Heat Source",
        "To": "Kitchen",
        "Flow kg/s": "0.16990 kg/s",
        "Pipe DN": "15",
        "Δp/m": "245.0",
        "Length": "4.2",
        "K": "1.5",
        "Section Δp": "1029.0 Pa",
        "Status": "Existing section evidence",
    }

    row = panel._normalise_clean_proportioned_section_source_row_v1(raw)

    assert row["route"] == "Leg 1A Common subleg"
    assert row["section"] == "3"
    assert row["from"] == "Boiler / Heat Source"
    assert row["to"] == "Kitchen"
    assert row["flow_kg_s"] == "0.16990 kg/s"
    assert row["pipe_dn"] == "15"
    assert row["dp_per_m"] == "245.0"
    assert row["length"] == "4.2"
    assert row["k"] == "1.5"
    assert row["section_dp"] == "1029.0 Pa"
    assert row["status"] == "Existing section evidence"

    source_rows = [
        row,
        panel._normalise_clean_proportioned_section_source_row_v1(
            {
                "Route": "Leg 2B Branch subleg",
                "Order": "4",
                "From": "Hall",
                "To": "Bedroom",
                "Flow kg/s": "0.08370 kg/s",
                "Status": "Existing section evidence",
            }
        ),
    ]

    selected_rows = panel._clean_proportioned_section_rows_for_view_v1(
        mode="Selected route only",
        route_label="Leg 1A Common subleg",
        source_rows=source_rows,
    )

    assert len(selected_rows) == 1
    assert selected_rows[0]["route"] == "Leg 1A Common subleg"

    all_rows = panel._clean_proportioned_section_rows_for_view_v1(
        mode="All routes",
        route_label="Leg 1A Common subleg",
        source_rows=source_rows,
    )

    assert len(all_rows) == 2

    assert panel._clean_proportioned_route_matches_section_row_v1(
        route_label="Leg 1A Common subleg",
        row={"route": "Leg 1A Common subleg"},
    )

    assert not panel._clean_proportioned_route_matches_section_row_v1(
        route_label="Leg 1A Common subleg",
        row={"route": "Leg 2B Branch subleg"},
    )

    print("OK — H-S33-L focused section population passed.")


if __name__ == "__main__":
    main()
