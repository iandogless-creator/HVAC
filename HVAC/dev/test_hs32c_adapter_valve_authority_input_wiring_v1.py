from __future__ import annotations

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
)
from HVAC.hydronics.proportioning.valve_authority_input_mapping_v1 import (
    valve_authority_input_mapping_to_dict_v1,
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

    mapping = adapter._build_valve_authority_input_mapping_preview_v1(
        balancing_candidate_mapping=balancing_mapping,
    )

    assert mapping.ready is False
    assert len(mapping.rows) == 3

    none_row = mapping.rows[0]
    input_row = mapping.rows[1]
    manual_row = mapping.rows[2]

    assert none_row.authority_band_id == VALVE_AUTHORITY_NONE_REQUIRED
    assert none_row.ready is True
    assert none_row.design_valve_dp_pa == 0.0

    assert input_row.authority_band_id == VALVE_AUTHORITY_INPUT_AVAILABLE
    assert input_row.ready is True
    assert input_row.design_valve_dp_pa == 2559.3
    assert input_row.route_flow_kg_s == 0.0227
    assert input_row.candidate_resistance_pa_per_kg_s2 == 4965000.0
    assert input_row.controlled_circuit_dp_pa is None
    assert input_row.authority is None
    assert "pending controlled circuit Δp" in input_row.status

    assert manual_row.authority_band_id == MANUAL_REVIEW_REQUIRED
    assert manual_row.ready is False
    assert "Positive route flow kg/s required" in manual_row.blockers

    payload = valve_authority_input_mapping_to_dict_v1(mapping)

    assert payload is not None
    assert payload["schema"] == "valve_authority_input_mapping_v1"
    assert payload["ready"] is False
    assert len(payload["rows"]) == 3

    assert "No valve product selected" in payload["exclusions"]
    assert "No Kv or Kvs selected" in payload["exclusions"]
    assert "No lockshield turn count" in payload["exclusions"]
    assert "No manufacturer valve data" in payload["exclusions"]
    assert "No pump selected" in payload["exclusions"]
    assert "No final balancing" in payload["exclusions"]
    assert "No pipe resizing" in payload["exclusions"]
    assert "No ProjectState mutation" in payload["exclusions"]

    blocked = adapter._build_valve_authority_input_mapping_preview_v1(
        balancing_candidate_mapping=None,
    )

    assert blocked.ready is False
    assert "Balancing method candidates required" in blocked.blockers

    print("OK — H-S32-C adapter valve authority input wiring passed.")


if __name__ == "__main__":
    main()
