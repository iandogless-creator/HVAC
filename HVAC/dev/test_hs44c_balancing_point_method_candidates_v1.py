from __future__ import annotations

import json

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.balancing_point_method_candidate_mapping_v1 import (
    balancing_point_method_candidate_mapping_to_dict_v1,
    build_balancing_point_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    BalancingPointResistanceAllocationProjectionV1,
    BalancingPointResistanceAllocationRowV1,
    BalancingPointRouteConservationRowV1,
)


def _row(
    point_id: str,
    *,
    scope: str,
    shared: bool,
    routes: tuple[str, ...],
    flow: float,
    added_dp: float,
    resistance: float,
) -> BalancingPointResistanceAllocationRowV1:
    return BalancingPointResistanceAllocationRowV1(
        balancing_point_id=point_id,
        point_scope=scope,
        point_role="common_main_takeoff" if scope == "main" else "branch",
        label=point_id,
        parent_balancing_point_id="",
        anchor_section_id=point_id + "-section-001",
        downstream_route_ids=routes,
        is_shared=shared,
        is_route_exclusive=not shared,
        point_flow_kg_s=flow,
        allocated_added_dp_pa=added_dp,
        allocated_resistance_pa_per_kg_s2=resistance,
        status="H-S44-B conserved allocation",
    )


def _conservation(route_id: str, required: float):
    return BalancingPointRouteConservationRowV1(
        route_id=route_id,
        required_added_dp_pa=required,
        allocated_path_dp_pa=required,
        difference_pa=0.0,
        contributing_balancing_point_ids=(),
        conserved=True,
        status="Conserved",
    )


def main() -> None:
    allocation = BalancingPointResistanceAllocationProjectionV1(
        ready=True,
        rows=(
            _row(
                "balancing-point:main:leg-001",
                scope="main",
                shared=True,
                routes=("route-a", "route-b"),
                flow=0.30,
                added_dp=90.0,
                resistance=1000.0,
            ),
            _row(
                "balancing-point:subleg:route-b",
                scope="subleg",
                shared=False,
                routes=("route-b",),
                flow=0.10,
                added_dp=50.0,
                resistance=5000.0,
            ),
            _row(
                "balancing-point:subleg:route-a",
                scope="subleg",
                shared=False,
                routes=("route-a",),
                flow=0.20,
                added_dp=0.0,
                resistance=0.0,
            ),
        ),
        route_conservation=(
            _conservation("route-a", 90.0),
            _conservation("route-b", 140.0),
        ),
        blockers=(),
        status="H-S44-B ready",
    )

    mapping = build_balancing_point_method_candidate_mapping_v1(allocation)
    assert mapping.ready is True
    assert mapping.blockers == ()
    assert len(mapping.candidates) == 3
    by_id = {row.balancing_point_id: row for row in mapping.candidates}

    shared = by_id["balancing-point:main:leg-001"]
    assert shared.method_id == PROPORTIONAL_ADDED_RESISTANCE
    assert shared.ready is True
    assert shared.point_scope == "main"
    assert shared.is_shared is True
    assert shared.is_route_exclusive is False
    assert shared.downstream_route_ids == ("route-a", "route-b")
    assert "group-scoped" in shared.note
    assert "shared" in shared.status.lower()

    exclusive = by_id["balancing-point:subleg:route-b"]
    assert exclusive.method_id == PROPORTIONAL_ADDED_RESISTANCE
    assert exclusive.is_shared is False
    assert exclusive.is_route_exclusive is True
    assert "route-exclusive" in exclusive.status.lower()

    zero = by_id["balancing-point:subleg:route-a"]
    assert zero.method_id == NONE_REQUIRED
    assert zero.ready is True
    assert zero.required_added_dp_pa == 0.0

    payload = balancing_point_method_candidate_mapping_to_dict_v1(mapping)
    assert payload is not None
    assert payload["schema"] == "balancing_point_method_candidate_mapping_v1"
    assert payload["candidates"][0]["point_scope"] == "main"
    assert payload["candidates"][0]["is_shared"] is True
    assert "No valve product selected" in payload["exclusions"]
    json.dumps(payload)

    bad_formula = BalancingPointResistanceAllocationProjectionV1(
        ready=True,
        rows=(
            _row(
                "balancing-point:bad",
                scope="subleg",
                shared=False,
                routes=("route-a",),
                flow=0.10,
                added_dp=50.0,
                resistance=123.0,
            ),
        ),
        route_conservation=(_conservation("route-a", 50.0),),
    )
    blocked = build_balancing_point_method_candidate_mapping_v1(bad_formula)
    assert blocked.ready is False
    assert blocked.candidates[0].method_id == MANUAL_REVIEW_REQUIRED
    assert any("differs" in item for item in blocked.candidates[0].blockers)

    unconserved = BalancingPointResistanceAllocationProjectionV1(
        ready=True,
        rows=allocation.rows,
        route_conservation=(
            BalancingPointRouteConservationRowV1(
                route_id="route-a",
                required_added_dp_pa=90.0,
                allocated_path_dp_pa=80.0,
                difference_pa=10.0,
                contributing_balancing_point_ids=(),
                conserved=False,
                status="Blocked",
            ),
        ),
    )
    conservation_blocked = build_balancing_point_method_candidate_mapping_v1(
        unconserved
    )
    assert conservation_blocked.ready is False
    assert conservation_blocked.candidates == ()
    assert "Unconserved" in conservation_blocked.status

    print(
        "OK — H-S44-C conserved point allocations map to scope-preserving "
        "balancing-method candidates."
    )


if __name__ == "__main__":
    main()
