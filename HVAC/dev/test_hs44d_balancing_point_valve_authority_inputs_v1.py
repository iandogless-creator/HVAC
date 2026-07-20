from __future__ import annotations

import json

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED as BALANCING_MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.balancing_point_method_candidate_mapping_v1 import (
    BalancingPointMethodCandidateMappingV1,
    BalancingPointMethodCandidateV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_input_mapping_v1 import (
    balancing_point_valve_authority_input_mapping_to_dict_v1,
    build_balancing_point_valve_authority_input_mapping_v1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
)


def _candidate(
    point_id: str,
    *,
    scope: str,
    shared: bool,
    routes: tuple[str, ...],
    method_id: str,
    flow: float,
    added_dp: float,
    resistance: float,
    ready: bool = True,
    blockers: tuple[str, ...] = (),
) -> BalancingPointMethodCandidateV1:
    return BalancingPointMethodCandidateV1(
        balancing_point_id=point_id,
        point_scope=scope,
        point_role="common_main_takeoff" if scope == "main" else "branch",
        label=point_id,
        parent_balancing_point_id="",
        anchor_section_id=point_id + "-section-001",
        downstream_route_ids=routes,
        is_shared=shared,
        is_route_exclusive=not shared,
        method_id=method_id,
        method_label=method_id.replace("_", " ").title(),
        ready=ready,
        point_flow_kg_s=flow,
        required_added_dp_pa=added_dp,
        resistance_pa_per_kg_s2=resistance,
        status="H-S44-C candidate",
        blockers=blockers,
    )


def main() -> None:
    candidates = BalancingPointMethodCandidateMappingV1(
        ready=True,
        status="H-S44-C ready",
        candidates=(
            _candidate(
                "balancing-point:main:leg-001",
                scope="main",
                shared=True,
                routes=("route-a", "route-b"),
                method_id=PROPORTIONAL_ADDED_RESISTANCE,
                flow=0.30,
                added_dp=90.0,
                resistance=1000.0,
            ),
            _candidate(
                "balancing-point:subleg:route-b",
                scope="subleg",
                shared=False,
                routes=("route-b",),
                method_id=PROPORTIONAL_ADDED_RESISTANCE,
                flow=0.10,
                added_dp=50.0,
                resistance=5000.0,
            ),
            _candidate(
                "balancing-point:subleg:route-a",
                scope="subleg",
                shared=False,
                routes=("route-a",),
                method_id=NONE_REQUIRED,
                flow=0.20,
                added_dp=0.0,
                resistance=0.0,
            ),
        ),
    )

    mapping = build_balancing_point_valve_authority_input_mapping_v1(
        candidates
    )
    assert mapping.ready is True
    assert mapping.blockers == ()
    assert len(mapping.rows) == 3
    by_id = {row.balancing_point_id: row for row in mapping.rows}

    shared = by_id["balancing-point:main:leg-001"]
    assert shared.authority_band_id == VALVE_AUTHORITY_INPUT_AVAILABLE
    assert shared.ready is True
    assert shared.point_scope == "main"
    assert shared.is_shared is True
    assert shared.is_route_exclusive is False
    assert shared.downstream_route_ids == ("route-a", "route-b")
    assert shared.design_valve_dp_pa == 90.0
    assert shared.point_flow_kg_s == 0.30
    assert shared.candidate_resistance_pa_per_kg_s2 == 1000.0
    assert shared.controlled_circuit_dp_pa is None
    assert shared.authority is None
    assert "group-scoped" in shared.note

    exclusive = by_id["balancing-point:subleg:route-b"]
    assert exclusive.authority_band_id == VALVE_AUTHORITY_INPUT_AVAILABLE
    assert exclusive.is_route_exclusive is True
    assert "route-exclusive" in exclusive.status.lower()

    none_row = by_id["balancing-point:subleg:route-a"]
    assert none_row.authority_band_id == VALVE_AUTHORITY_NONE_REQUIRED
    assert none_row.ready is True
    assert none_row.design_valve_dp_pa == 0.0
    assert none_row.authority is None

    payload = balancing_point_valve_authority_input_mapping_to_dict_v1(
        mapping
    )
    assert payload is not None
    assert payload["schema"] == (
        "balancing_point_valve_authority_input_mapping_v1"
    )
    assert payload["rows"][0]["point_scope"] == "main"
    assert payload["rows"][0]["is_shared"] is True
    assert "No valve product selected" in payload["exclusions"]
    json.dumps(payload)

    manual_candidates = BalancingPointMethodCandidateMappingV1(
        ready=False,
        blockers=("manual evidence",),
        candidates=(
            _candidate(
                "balancing-point:manual",
                scope="leg",
                shared=False,
                routes=("route-a",),
                method_id=BALANCING_MANUAL_REVIEW_REQUIRED,
                flow=0.10,
                added_dp=50.0,
                resistance=5000.0,
                ready=False,
                blockers=("Manual review required",),
            ),
        ),
    )
    blocked = build_balancing_point_valve_authority_input_mapping_v1(
        manual_candidates
    )
    assert blocked.ready is False
    assert len(blocked.rows) == 1
    assert blocked.rows[0].authority_band_id == MANUAL_REVIEW_REQUIRED
    assert blocked.rows[0].ready is False
    assert blocked.rows[0].is_route_exclusive is True

    invalid_formula = BalancingPointMethodCandidateMappingV1(
        ready=True,
        candidates=(
            _candidate(
                "balancing-point:bad-formula",
                scope="subleg",
                shared=False,
                routes=("route-a",),
                method_id=PROPORTIONAL_ADDED_RESISTANCE,
                flow=0.10,
                added_dp=50.0,
                resistance=123.0,
            ),
        ),
    )
    formula_blocked = build_balancing_point_valve_authority_input_mapping_v1(
        invalid_formula
    )
    assert formula_blocked.ready is False
    assert formula_blocked.rows[0].authority_band_id == MANUAL_REVIEW_REQUIRED
    assert any("differs" in value for value in formula_blocked.rows[0].blockers)

    print(
        "OK — H-S44-D point candidates map to scope-preserving "
        "valve-authority inputs."
    )


if __name__ == "__main__":
    main()
