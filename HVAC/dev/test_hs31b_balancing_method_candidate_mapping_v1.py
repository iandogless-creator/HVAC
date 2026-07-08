from __future__ import annotations

import json

from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    balancing_method_candidate_mapping_to_dict_v1,
    build_balancing_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)


def main() -> None:
    mapping = build_balancing_method_candidate_mapping_v1(
        [
            {
                "route": "leg-001:primary-subleg",
                "controlling": "Yes",
                "required_added_dp": "0.0 Pa",
                "flow_kg_s": "0.0300",
                "resistance_pa_per_kg_s2": "0.0",
                "status": "Preview only — no valve selected",
            },
            {
                "route": "leg-002:subleg-b",
                "controlling": "No",
                "required_added_dp": "2559.3 Pa",
                "flow_kg_s": "0.0227",
                "resistance_pa_per_kg_s2": "4965000.0",
                "status": "Preview only — no valve selected",
            },
            {
                "route": "leg-003:subleg-c",
                "controlling": "No",
                "required_added_dp": "119.5 Pa",
                "flow_kg_s": "—",
                "resistance_pa_per_kg_s2": "—",
                "status": "Preview only — no valve selected",
            },
        ]
    )

    assert mapping.ready is False
    assert len(mapping.candidates) == 3

    controlling = mapping.candidates[0]
    candidate = mapping.candidates[1]
    manual = mapping.candidates[2]

    assert controlling.method_id == NONE_REQUIRED
    assert controlling.ready is True
    assert controlling.controlling is True
    assert "controlling route" in controlling.status

    assert candidate.method_id == PROPORTIONAL_ADDED_RESISTANCE
    assert candidate.ready is True
    assert candidate.required_added_dp_pa == 2559.3
    assert candidate.flow_kg_s == 0.0227
    assert candidate.resistance_pa_per_kg_s2 == 4965000.0
    assert "no valve selected" in candidate.note
    assert "Kv/Kvs" in candidate.note

    assert manual.method_id == MANUAL_REVIEW_REQUIRED
    assert manual.ready is False
    assert "Positive route flow kg/s required" in manual.blockers
    assert "Positive resistance Pa/(kg/s)² required" in manual.blockers

    assert mapping.blockers
    assert "leg-003:subleg-c" in mapping.blockers[0]

    payload = balancing_method_candidate_mapping_to_dict_v1(mapping)

    assert payload is not None
    assert payload["schema"] == "balancing_method_candidate_mapping_v1"
    assert payload["ready"] is False
    assert len(payload["candidates"]) == 3

    assert "No valve product selected" in payload["exclusions"]
    assert "No Kv or Kvs selected" in payload["exclusions"]
    assert "No lockshield turn count" in payload["exclusions"]
    assert "No pump selected" in payload["exclusions"]
    assert "No final balancing" in payload["exclusions"]
    assert "No pipe resizing" in payload["exclusions"]
    assert "No ProjectState mutation" in payload["exclusions"]

    json.dumps(payload)

    zero_mapping = build_balancing_method_candidate_mapping_v1(
        [
            {
                "route": "leg-004:subleg-d",
                "controlling": "No",
                "required_added_dp": "0.2 Pa",
                "flow_kg_s": "0.0100",
                "resistance_pa_per_kg_s2": "0.0",
            }
        ],
        dp_tolerance_pa=0.5,
    )

    assert zero_mapping.ready is True
    assert zero_mapping.candidates[0].method_id == NONE_REQUIRED

    blocked = build_balancing_method_candidate_mapping_v1([])

    assert blocked.ready is False
    assert "Provisional route burden rows required" in blocked.blockers

    print("OK — H-S31-B balancing method candidate mapping passed.")


if __name__ == "__main__":
    main()
