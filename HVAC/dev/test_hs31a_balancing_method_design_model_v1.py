from __future__ import annotations

import json

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    DPCV_ZONE_PREVIEW,
    LOCKSHIELD_THROTTLING_PREVIEW,
    MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PICV_EMITTER_PREVIEW,
    PROPORTIONAL_ADDED_RESISTANCE,
    balancing_method_design_model_to_dict_v1,
    build_balancing_method_design_model_v1,
    build_balancing_method_options_v1,
)


def main() -> None:
    options = build_balancing_method_options_v1()
    option_ids = {option.method_id for option in options}

    assert NONE_REQUIRED in option_ids
    assert PROPORTIONAL_ADDED_RESISTANCE in option_ids
    assert LOCKSHIELD_THROTTLING_PREVIEW in option_ids
    assert DPCV_ZONE_PREVIEW in option_ids
    assert PICV_EMITTER_PREVIEW in option_ids
    assert MANUAL_REVIEW_REQUIRED in option_ids

    model = build_balancing_method_design_model_v1()

    assert model.ready is True
    assert model.selected_method_id == PROPORTIONAL_ADDED_RESISTANCE
    assert model.selected_method_label == "Proportional added resistance"
    assert "Ready" in model.status

    assert "No valve product selected" in model.exclusions
    assert "No Kv or Kvs selected" in model.exclusions
    assert "No lockshield turn count" in model.exclusions
    assert "No pump selected" in model.exclusions
    assert "No final balancing" in model.exclusions
    assert "No pipe resizing" in model.exclusions
    assert "No ProjectState mutation" in model.exclusions

    payload = balancing_method_design_model_to_dict_v1(model)

    assert payload is not None
    assert payload["schema"] == "balancing_method_design_model_v1"
    assert payload["ready"] is True
    assert payload["selected_method_id"] == PROPORTIONAL_ADDED_RESISTANCE
    assert "no valve sizing" in payload["note"]

    json.dumps(payload)

    none_model = build_balancing_method_design_model_v1(
        selected_method_id=NONE_REQUIRED,
    )

    assert none_model.ready is True
    assert none_model.selected_method_id == NONE_REQUIRED

    deferred = build_balancing_method_design_model_v1(
        selected_method_id=LOCKSHIELD_THROTTLING_PREVIEW,
    )

    assert deferred.ready is False
    assert "deferred in v1" in deferred.status
    assert deferred.selected_method_id == LOCKSHIELD_THROTTLING_PREVIEW

    unknown = build_balancing_method_design_model_v1(
        selected_method_id="MAGIC_VALVE_BALANCE",
    )

    assert unknown.ready is False
    assert unknown.selected_method_id == MANUAL_REVIEW_REQUIRED
    assert "Unknown balancing method" in unknown.status

    print("OK — H-S31-A balancing method design model passed.")


if __name__ == "__main__":
    main()
