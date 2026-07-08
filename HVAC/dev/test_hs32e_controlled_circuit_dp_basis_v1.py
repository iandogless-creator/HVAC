from __future__ import annotations

import json

from HVAC.hydronics.proportioning.controlled_circuit_dp_basis_v1 import (
    CONTROLLED_CIRCUIT_DP_UNRESOLVED,
    MANUAL_REVIEW_REQUIRED,
    ROUTE_CHOSEN_DP,
    ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP,
    build_controlled_circuit_dp_basis_model_v1,
    controlled_circuit_dp_basis_model_to_dict_v1,
    controlled_circuit_dp_resolution_to_dict_v1,
    resolve_controlled_circuit_dp_v1,
)


def main() -> None:
    model = build_controlled_circuit_dp_basis_model_v1()

    assert model.ready is True
    assert model.selected_basis_id == ROUTE_CHOSEN_DP
    assert model.selected_basis_label == "Route chosen Δp"

    option_ids = {option.basis_id for option in model.options}

    assert CONTROLLED_CIRCUIT_DP_UNRESOLVED in option_ids
    assert ROUTE_CHOSEN_DP in option_ids
    assert ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP in option_ids
    assert MANUAL_REVIEW_REQUIRED in option_ids

    payload = controlled_circuit_dp_basis_model_to_dict_v1(model)

    assert payload is not None
    assert payload["schema"] == "controlled_circuit_dp_basis_model_v1"
    assert payload["ready"] is True
    assert payload["selected_basis_id"] == ROUTE_CHOSEN_DP

    assert "No authority ratio calculated" in payload["exclusions"]
    assert "No valve product selected" in payload["exclusions"]
    assert "No Kv or Kvs selected" in payload["exclusions"]
    assert "No lockshield turn count" in payload["exclusions"]
    assert "No manufacturer valve data" in payload["exclusions"]
    assert "No pump selected" in payload["exclusions"]
    assert "No final balancing" in payload["exclusions"]
    assert "No pipe resizing" in payload["exclusions"]
    assert "No ProjectState mutation" in payload["exclusions"]

    assert "no authority ratio" in payload["note"]
    assert "no Kv/Kvs" in payload["note"]

    json.dumps(payload)

    route_basis = resolve_controlled_circuit_dp_v1(
        basis_id=ROUTE_CHOSEN_DP,
        route_chosen_dp_pa=22056.5,
        required_added_dp_pa=6687.2,
    )

    assert route_basis.ready is True
    assert route_basis.controlled_circuit_dp_pa == 22056.5
    assert "No authority ratio calculated" in route_basis.note

    minus_basis = resolve_controlled_circuit_dp_v1(
        basis_id=ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP,
        route_chosen_dp_pa=22056.5,
        required_added_dp_pa=6687.2,
    )

    assert minus_basis.ready is True
    assert round(minus_basis.controlled_circuit_dp_pa or 0.0, 1) == 15369.3

    unresolved = resolve_controlled_circuit_dp_v1(
        basis_id=CONTROLLED_CIRCUIT_DP_UNRESOLVED,
    )

    assert unresolved.ready is False
    assert "unresolved" in unresolved.status

    blocked = resolve_controlled_circuit_dp_v1(
        basis_id=ROUTE_CHOSEN_DP,
        route_chosen_dp_pa="—",
    )

    assert blocked.ready is False
    assert "Route chosen Δp required" in blocked.blockers

    bad_minus = resolve_controlled_circuit_dp_v1(
        basis_id=ROUTE_CHOSEN_DP_MINUS_REQUIRED_ADDED_DP,
        route_chosen_dp_pa=100.0,
        required_added_dp_pa=150.0,
    )

    assert bad_minus.ready is False
    assert "must be greater than zero" in bad_minus.status

    unknown = build_controlled_circuit_dp_basis_model_v1(
        selected_basis_id="MAGIC_DP_BASIS",
    )

    assert unknown.ready is False
    assert unknown.selected_basis_id == MANUAL_REVIEW_REQUIRED

    resolution_payload = controlled_circuit_dp_resolution_to_dict_v1(route_basis)

    assert resolution_payload is not None
    assert resolution_payload["ready"] is True
    assert resolution_payload["controlled_circuit_dp_pa"] == 22056.5

    json.dumps(resolution_payload)

    print("OK — H-S32-E controlled-circuit Δp basis model passed.")


if __name__ == "__main__":
    main()
