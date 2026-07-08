from __future__ import annotations

import json

from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    build_balancing_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
)
from HVAC.hydronics.proportioning.valve_authority_input_mapping_v1 import (
    build_valve_authority_input_mapping_v1,
    valve_authority_input_mapping_to_dict_v1,
)


def main() -> None:
    balancing_mapping = build_balancing_method_candidate_mapping_v1(
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

    mapping = build_valve_authority_input_mapping_v1(balancing_mapping)

    assert mapping.ready is False
    assert len(mapping.rows) == 3

    none_row = mapping.rows[0]
    input_row = mapping.rows[1]
    manual_row = mapping.rows[2]

    assert none_row.authority_band_id == VALVE_AUTHORITY_NONE_REQUIRED
    assert none_row.authority_label == "No valve authority required"
    assert none_row.ready is True
    assert none_row.design_valve_dp_pa == 0.0
    assert none_row.authority is None

    assert input_row.authority_band_id == VALVE_AUTHORITY_INPUT_AVAILABLE
    assert input_row.authority_label == "Valve authority input available"
    assert input_row.ready is True
    assert input_row.design_valve_dp_pa == 2559.3
    assert input_row.route_flow_kg_s == 0.0227
    assert input_row.candidate_resistance_pa_per_kg_s2 == 4965000.0
    assert input_row.controlled_circuit_dp_pa is None
    assert input_row.authority is None
    assert "pending controlled circuit Δp" in input_row.status
    assert "No Kv/Kvs" in input_row.note

    assert manual_row.authority_band_id == MANUAL_REVIEW_REQUIRED
    assert manual_row.ready is False
    assert "Positive route flow kg/s required" in manual_row.blockers

    assert mapping.blockers
    assert "leg-003:subleg-c" in mapping.blockers[0]

    payload = valve_authority_input_mapping_to_dict_v1(mapping)

    assert payload is not None
    assert payload["schema"] == "valve_authority_input_mapping_v1"
    assert payload["ready"] is False
    assert len(payload["rows"]) == 3
    assert payload["design_model"] is not None

    assert "No valve product selected" in payload["exclusions"]
    assert "No Kv or Kvs selected" in payload["exclusions"]
    assert "No lockshield turn count" in payload["exclusions"]
    assert "No manufacturer valve data" in payload["exclusions"]
    assert "No pump selected" in payload["exclusions"]
    assert "No final balancing" in payload["exclusions"]
    assert "No pipe resizing" in payload["exclusions"]
    assert "No ProjectState mutation" in payload["exclusions"]

    json.dumps(payload)

    blocked = build_valve_authority_input_mapping_v1(None)

    assert blocked.ready is False
    assert "Balancing method candidates required" in blocked.blockers

    print("OK — H-S32-B valve authority input mapping passed.")


if __name__ == "__main__":
    main()
