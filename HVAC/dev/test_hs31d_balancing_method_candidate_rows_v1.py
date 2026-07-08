from __future__ import annotations

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    build_balancing_method_candidate_mapping_v1,
)


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )

    mapping = build_balancing_method_candidate_mapping_v1(
        [
            {
                "route": "leg-001:primary-subleg",
                "controlling": "Yes",
                "required_added_dp": "0.0 Pa",
                "flow_kg_s": "0.0300",
                "resistance_pa_per_kg_s2": "0.0",
            },
            {
                "route": "leg-002:subleg-b",
                "controlling": "No",
                "required_added_dp": "2559.3 Pa",
                "flow_kg_s": "0.0227",
                "resistance_pa_per_kg_s2": "4965000.0",
            },
            {
                "route": "leg-003:subleg-c",
                "controlling": "No",
                "required_added_dp": "119.5 Pa",
                "flow_kg_s": "—",
                "resistance_pa_per_kg_s2": "—",
            },
        ]
    )

    rows = adapter._build_balancing_method_candidate_rows_v1(mapping)

    assert len(rows) == 3

    assert rows[0]["route"] == "leg-001:primary-subleg"
    assert rows[0]["method"] == "None required"
    assert rows[0]["ready"] == "Yes"
    assert rows[0]["controlling"] == "Yes"

    assert rows[1]["route"] == "leg-002:subleg-b"
    assert rows[1]["method"] == "Proportional added resistance"
    assert rows[1]["ready"] == "Yes"
    assert rows[1]["required_added_dp"] == "2559.3 Pa"
    assert rows[1]["flow_kg_s"] == "0.0227"
    assert rows[1]["resistance_pa_per_kg_s2"] == "4965000.0"

    assert rows[2]["route"] == "leg-003:subleg-c"
    assert rows[2]["method"] == "Manual review required"
    assert rows[2]["ready"] == "No"
    assert "Positive route flow kg/s required" in rows[2]["blockers"]

    empty_rows = adapter._build_balancing_method_candidate_rows_v1(None)

    assert len(empty_rows) == 1
    assert empty_rows[0]["route"] == "—"
    assert empty_rows[0]["status"] == (
        "Waiting for balancing method candidate evidence"
    )

    print("OK — H-S31-D balancing method candidate rows passed.")


if __name__ == "__main__":
    main()
