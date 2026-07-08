from __future__ import annotations

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )

    balancing_mapping = (
        adapter._build_balancing_method_candidate_mapping_preview_v1(
            provisional_burden_rows=[
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
    )

    valve_mapping = adapter._build_valve_authority_input_mapping_preview_v1(
        balancing_candidate_mapping=balancing_mapping,
    )

    rows = adapter._build_valve_authority_input_rows_v1(valve_mapping)

    assert len(rows) == 3

    assert rows[0]["route"] == "leg-001:primary-subleg"
    assert rows[0]["balancing_method"] == "None required"
    assert rows[0]["authority_state"] == "No valve authority required"
    assert rows[0]["ready"] == "Yes"
    assert rows[0]["design_valve_dp"] == "0.0 Pa"
    assert rows[0]["authority"] == "—"

    assert rows[1]["route"] == "leg-002:subleg-b"
    assert rows[1]["balancing_method"] == "Proportional added resistance"
    assert rows[1]["authority_state"] == "Valve authority input available"
    assert rows[1]["ready"] == "Yes"
    assert rows[1]["design_valve_dp"] == "2559.3 Pa"
    assert rows[1]["flow_kg_s"] == "0.0227"
    assert rows[1]["candidate_resistance"] == "4965000.0"
    assert rows[1]["controlled_circuit_dp"] == "—"
    assert rows[1]["authority"] == "—"
    assert "pending controlled circuit Δp" in rows[1]["status"]

    assert rows[2]["route"] == "leg-003:subleg-c"
    assert rows[2]["authority_state"] == "Manual review required"
    assert rows[2]["ready"] == "No"
    assert "Positive route flow kg/s required" in rows[2]["blockers"]

    empty_rows = adapter._build_valve_authority_input_rows_v1(None)

    assert len(empty_rows) == 1
    assert empty_rows[0]["route"] == "—"
    assert empty_rows[0]["status"] == (
        "Waiting for valve authority input evidence"
    )

    print("OK — H-S32-D valve authority input rows passed.")


if __name__ == "__main__":
    main()
