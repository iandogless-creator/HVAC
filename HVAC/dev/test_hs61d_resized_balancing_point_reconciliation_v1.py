from __future__ import annotations

import inspect

from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    BalancingPointResistanceAllocationProjectionV1,
    BalancingPointResistanceAllocationRowV1,
    BalancingPointRouteConservationRowV1,
)
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    build_committed_balancing_point_allocation_authority_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import (
    ProportionedPipeResizingHydraulicProjectionV1,
    ProportionedResizedRouteHydraulicProjectionV1,
)
from HVAC.hydronics.proportioning.resized_balancing_point_reconciliation_v1 import (
    build_resized_balancing_point_reconciliation_v1,
)


def _point(
        point_id: str,
        route_ids: tuple[str, ...],
        *,
        allocated: float,
        flow: float,
        shared: bool,
        parent: str = "",
) -> BalancingPointResistanceAllocationRowV1:
    return BalancingPointResistanceAllocationRowV1(
        balancing_point_id=point_id,
        point_scope="main" if shared else "subleg",
        point_role="common_main_takeoff" if shared else "downstream-exclusive",
        label=point_id,
        parent_balancing_point_id=parent,
        anchor_section_id="section-1",
        downstream_route_ids=route_ids,
        is_shared=shared,
        is_route_exclusive=not shared,
        point_flow_kg_s=flow,
        allocated_added_dp_pa=allocated,
        allocated_resistance_pa_per_kg_s2=(
            allocated / flow**2 if allocated > 0.0 else 0.0
        ),
        status="Ready",
    )


def _point_authority(*, include_route_one_exclusive: bool = True):
    route_one_committed = (
        300.0 if include_route_one_exclusive else 200.0
    )
    route_one_point_ids = (
        ("point-shared", "point-route-one")
        if include_route_one_exclusive
        else ("point-shared",)
    )
    points = [
        _point(
            "point-shared",
            ("route-one", "route-two"),
            allocated=200.0,
            flow=0.20,
            shared=True,
        ),
    ]
    if include_route_one_exclusive:
        points.append(
            _point(
                "point-route-one",
                ("route-one",),
                allocated=100.0,
                flow=0.10,
                shared=False,
                parent="point-shared",
            )
        )
    points.extend(
        (
            _point(
                "point-route-two",
                ("route-two",),
                allocated=0.0,
                flow=0.12,
                shared=False,
                parent="point-shared",
            ),
            _point(
                "point-control",
                ("route-control",),
                allocated=0.0,
                flow=0.08,
                shared=False,
            ),
        )
    )
    projection = BalancingPointResistanceAllocationProjectionV1(
        ready=True,
        rows=tuple(points),
        route_conservation=(
            BalancingPointRouteConservationRowV1(
                route_id="route-one",
                required_added_dp_pa=route_one_committed,
                allocated_path_dp_pa=route_one_committed,
                difference_pa=0.0,
                contributing_balancing_point_ids=route_one_point_ids,
                conserved=True,
                status="Conserved",
            ),
            BalancingPointRouteConservationRowV1(
                route_id="route-two",
                required_added_dp_pa=200.0,
                allocated_path_dp_pa=200.0,
                difference_pa=0.0,
                contributing_balancing_point_ids=("point-shared",),
                conserved=True,
                status="Conserved",
            ),
            BalancingPointRouteConservationRowV1(
                route_id="route-control",
                required_added_dp_pa=0.0,
                allocated_path_dp_pa=0.0,
                difference_pa=0.0,
                contributing_balancing_point_ids=(),
                conserved=True,
                status="Conserved",
            ),
        ),
    )
    authority = build_committed_balancing_point_allocation_authority_v1(
        projection
    )
    assert authority.ready is True, authority.status
    return authority


def _route(
        route_id: str,
        *,
        total: float,
        target: float,
        required: float,
        rank: int,
        controlling: bool,
) -> ProportionedResizedRouteHydraulicProjectionV1:
    return ProportionedResizedRouteHydraulicProjectionV1(
        route_id=route_id,
        section_ids=(f"{route_id}-section",),
        section_count=1,
        straight_pressure_drop_total_Pa=total - 10.0,
        local_pressure_drop_total_Pa=10.0,
        route_pressure_drop_total_Pa=total,
        controlling_target_Pa=target,
        required_added_dp_Pa=required,
        rank=rank,
        is_controlling=controlling,
        status="Projected",
    )


def _resized(
        *,
        route_one_required: float = 300.0,
        route_two_required: float = 200.0,
) -> ProportionedPipeResizingHydraulicProjectionV1:
    target = 1300.0
    routes = (
        _route(
            "leg-a:route-one",
            total=target - route_one_required,
            target=target,
            required=route_one_required,
            rank=2,
            controlling=False,
        ),
        _route(
            "leg-b:route-two",
            total=target - route_two_required,
            target=target,
            required=route_two_required,
            rank=3,
            controlling=False,
        ),
        _route(
            "leg-c:route-control",
            total=target,
            target=target,
            required=0.0,
            rank=1,
            controlling=True,
        ),
    )
    return ProportionedPipeResizingHydraulicProjectionV1(
        ready=True,
        routes=routes,
        route_count=len(routes),
        controlling_route_id="leg-c:route-control",
        controlling_target_Pa=target,
        status="Ready",
    )


def main() -> None:
    resized = _resized()
    authority = _point_authority()
    before_resized = repr(resized)
    before_authority = repr(authority)

    result = build_resized_balancing_point_reconciliation_v1(
        resized_hydraulics=resized,
        committed_point_allocation_authority=authority,
    )
    repeated = build_resized_balancing_point_reconciliation_v1(
        resized_hydraulics=resized,
        committed_point_allocation_authority=authority,
    )

    assert result == repeated
    assert repr(resized) == before_resized
    assert repr(authority) == before_authority
    assert result.ready is True, result.status
    assert result.point_count == 4
    assert result.route_count == 3
    assert result.valve_duty_point_count == 2

    points = {row.balancing_point_id: row for row in result.point_rows}
    assert points["point-shared"].reconciled_allocated_dp_Pa == 200.0
    assert points["point-route-one"].reconciled_allocated_dp_Pa == 100.0
    assert points["point-route-two"].reconciled_allocated_dp_Pa == 0.0
    assert points["point-control"].reconciled_allocated_dp_Pa == 0.0
    assert points["point-shared"].is_shared is True
    assert points["point-route-one"].parent_balancing_point_id == (
        "point-shared"
    )

    routes = {row.allocation_route_id: row for row in result.route_rows}
    assert routes["route-one"].projected_route_id == "leg-a:route-one"
    assert routes["route-one"].allocated_path_dp_Pa == 300.0
    assert routes["route-two"].allocated_path_dp_Pa == 200.0
    assert routes["route-control"].allocated_path_dp_Pa == 0.0
    assert all(row.residual_Pa == 0.0 for row in result.route_rows)
    assert all(row.conserved for row in result.route_rows)

    # New shortfalls replace the stale committed duty values while retaining
    # point identities and topology.
    changed = build_resized_balancing_point_reconciliation_v1(
        resized_hydraulics=_resized(
            route_one_required=400.0,
            route_two_required=150.0,
        ),
        committed_point_allocation_authority=authority,
    )
    assert changed.ready is True, changed.status
    changed_points = {
        row.balancing_point_id: row for row in changed.point_rows
    }
    assert changed_points["point-shared"].reconciled_allocated_dp_Pa == 150.0
    assert (
        changed_points["point-route-one"].reconciled_allocated_dp_Pa
        == 250.0
    )
    assert changed_points["point-shared"].allocation_change_dp_Pa == -50.0
    assert (
        changed_points["point-route-one"].allocation_change_dp_Pa
        == 150.0
    )

    blocked = build_resized_balancing_point_reconciliation_v1(
        resized_hydraulics=_resized(
            route_one_required=400.0,
            route_two_required=150.0,
        ),
        committed_point_allocation_authority=_point_authority(
            include_route_one_exclusive=False
        ),
    )
    assert blocked.ready is False
    assert "cannot reconcile" in blocked.status

    absent = build_resized_balancing_point_reconciliation_v1(
        resized_hydraulics=resized,
        committed_point_allocation_authority=None,
    )
    assert absent.ready is False
    assert "H-S56-A" in absent.status

    source = inspect.getsource(
        build_resized_balancing_point_reconciliation_v1
    )
    assert "minimum" in source
    assert "ProjectState" not in source
    assert "accepted_kvs" not in source.lower()

    print(
        "OK — H-S61-D resized balancing-point reconciliation passed."
    )


if __name__ == "__main__":
    main()
