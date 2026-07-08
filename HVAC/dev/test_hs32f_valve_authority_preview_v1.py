from __future__ import annotations

import json

from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    build_balancing_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.controlled_circuit_dp_basis_v1 import (
    ROUTE_CHOSEN_DP,
    ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    ACCEPTABLE_AUTHORITY_PREVIEW,
    MANUAL_REVIEW_REQUIRED,
    VALVE_AUTHORITY_NONE_REQUIRED,
)
from HVAC.hydronics.proportioning.valve_authority_input_mapping_v1 import (
    build_valve_authority_input_mapping_v1,
)
from HVAC.hydronics.proportioning.valve_authority_preview_v1 import (
    build_valve_authority_preview_v1,
    valve_authority_preview_to_dict_v1,
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

    input_mapping = build_valve_authority_input_mapping_v1(
        balancing_mapping
    )

    preview = build_valve_authority_preview_v1(
        valve_authority_input_mapping=input_mapping,
        route_pressure_rows=[
            {
                "route": "leg-002:subleg-b",
                "chosen_dp": "7654.1 Pa",
            },
        ],
    )

    assert preview.ready is False
    assert len(preview.rows) == 3

    none_row = preview.rows[0]
    authority_row = preview.rows[1]
    manual_row = preview.rows[2]

    assert none_row.authority_band_id == VALVE_AUTHORITY_NONE_REQUIRED
    assert none_row.ready is True
    assert none_row.authority is None

    assert authority_row.ready is True
    assert authority_row.design_valve_dp_pa == 2559.3
    assert authority_row.controlled_circuit_dp_pa == 7654.1
    assert round(authority_row.authority or 0.0, 3) == 0.251
    assert authority_row.authority_band_id == ACCEPTABLE_AUTHORITY_PREVIEW
    assert "acceptable authority" in authority_row.status

    assert manual_row.ready is False
    assert manual_row.authority_band_id == MANUAL_REVIEW_REQUIRED
    assert "Positive route flow kg/s required" in manual_row.blockers

    assert preview.blockers
    assert "leg-003:subleg-c" in preview.blockers[0]

    payload = valve_authority_preview_to_dict_v1(preview)

    assert payload is not None
    assert payload["schema"] == "valve_authority_preview_v1"
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

    json.dumps(payload)

    minus_preview = build_valve_authority_preview_v1(
        valve_authority_input_mapping=input_mapping,
        route_pressure_rows=[
            {
                "route": "leg-002:subleg-b",
                "chosen_dp": "7654.1 Pa",
            },
        ],
        controlled_circuit_basis_id=ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP,
    )

    minus_row = minus_preview.rows[1]

    assert minus_row.ready is True
    assert round(minus_row.controlled_circuit_dp_pa or 0.0, 1) == 5094.8
    assert round(minus_row.authority or 0.0, 3) == 0.334

    missing_route_preview = build_valve_authority_preview_v1(
        valve_authority_input_mapping=input_mapping,
        route_pressure_rows=[],
        controlled_circuit_basis_id=ROUTE_CHOSEN_DP,
    )

    missing_row = missing_route_preview.rows[1]

    assert missing_row.ready is False
    assert "Route chosen Δp required" in missing_row.blockers

    blocked = build_valve_authority_preview_v1(
        valve_authority_input_mapping=None,
        route_pressure_rows=[],
    )

    assert blocked.ready is False
    assert "Valve authority input rows required" in blocked.blockers

    print("OK — H-S32-F valve authority preview passed.")


if __name__ == "__main__":
    main()
