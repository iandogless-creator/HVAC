from __future__ import annotations

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    balancing_method_candidate_mapping_to_dict_v1,
)
from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )

    mapping = adapter._build_balancing_method_candidate_mapping_preview_v1(
        provisional_burden_rows=[
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

    assert mapping.candidates[0].method_id == NONE_REQUIRED
    assert mapping.candidates[0].ready is True
    assert mapping.candidates[0].controlling is True

    assert mapping.candidates[1].method_id == PROPORTIONAL_ADDED_RESISTANCE
    assert mapping.candidates[1].ready is True
    assert mapping.candidates[1].required_added_dp_pa == 2559.3
    assert mapping.candidates[1].flow_kg_s == 0.0227

    assert mapping.candidates[2].method_id == MANUAL_REVIEW_REQUIRED
    assert mapping.candidates[2].ready is False
    assert "Positive route flow kg/s required" in (
        mapping.candidates[2].blockers
    )

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

    blocked = adapter._build_balancing_method_candidate_mapping_preview_v1(
        provisional_burden_rows=[]
    )

    assert blocked.ready is False
    assert "Provisional route burden rows required" in blocked.blockers

    print("OK — H-S31-C adapter balancing method candidate wiring passed.")


if __name__ == "__main__":
    main()
