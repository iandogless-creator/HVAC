from __future__ import annotations

import json

from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    ACCEPTABLE_AUTHORITY_PREVIEW,
    HIGH_THROTTLING_BURDEN,
    MANUAL_REVIEW_REQUIRED,
    TOO_LOW_AUTHORITY_PREVIEW,
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
    build_valve_authority_design_model_v1,
    classify_valve_authority_band_v1,
    valve_authority_design_model_to_dict_v1,
)


def main() -> None:
    model = build_valve_authority_design_model_v1()

    assert model.ready is True
    assert model.minimum_authority == 0.25
    assert model.high_throttling_authority == 0.70
    assert "authority =" in model.authority_formula

    band_ids = {band.band_id for band in model.bands}

    assert VALVE_AUTHORITY_NONE_REQUIRED in band_ids
    assert VALVE_AUTHORITY_INPUT_AVAILABLE in band_ids
    assert TOO_LOW_AUTHORITY_PREVIEW in band_ids
    assert ACCEPTABLE_AUTHORITY_PREVIEW in band_ids
    assert HIGH_THROTTLING_BURDEN in band_ids
    assert MANUAL_REVIEW_REQUIRED in band_ids

    assert classify_valve_authority_band_v1(None) == MANUAL_REVIEW_REQUIRED
    assert classify_valve_authority_band_v1(-0.1) == MANUAL_REVIEW_REQUIRED
    assert classify_valve_authority_band_v1(1.1) == MANUAL_REVIEW_REQUIRED
    assert classify_valve_authority_band_v1(0.10) == TOO_LOW_AUTHORITY_PREVIEW
    assert classify_valve_authority_band_v1(0.25) == ACCEPTABLE_AUTHORITY_PREVIEW
    assert classify_valve_authority_band_v1(0.50) == ACCEPTABLE_AUTHORITY_PREVIEW
    assert classify_valve_authority_band_v1(0.70) == ACCEPTABLE_AUTHORITY_PREVIEW
    assert classify_valve_authority_band_v1(0.80) == HIGH_THROTTLING_BURDEN

    payload = valve_authority_design_model_to_dict_v1(model)

    assert payload is not None
    assert payload["schema"] == "valve_authority_design_model_v1"
    assert payload["ready"] is True
    assert "authority =" in payload["authority_formula"]

    assert "No valve product selected" in payload["exclusions"]
    assert "No Kv or Kvs selected" in payload["exclusions"]
    assert "No lockshield turn count" in payload["exclusions"]
    assert "No manufacturer valve data" in payload["exclusions"]
    assert "No pump selected" in payload["exclusions"]
    assert "No final balancing" in payload["exclusions"]
    assert "No pipe resizing" in payload["exclusions"]
    assert "No ProjectState mutation" in payload["exclusions"]

    assert "no valve sizing" in payload["note"]
    assert "no Kv/Kvs" in payload["note"]

    json.dumps(payload)

    bad_model = build_valve_authority_design_model_v1(
        minimum_authority=0.80,
        high_throttling_authority=0.70,
    )

    assert bad_model.ready is False
    assert "Minimum authority must be lower" in bad_model.status

    print("OK — H-S32-A valve authority design model passed.")


if __name__ == "__main__":
    main()
