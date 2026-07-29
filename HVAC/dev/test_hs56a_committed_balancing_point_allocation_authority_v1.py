from __future__ import annotations

from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    BalancingPointResistanceAllocationProjectionV1,
    BalancingPointResistanceAllocationRowV1,
    BalancingPointRouteConservationRowV1,
)
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    build_committed_balancing_point_allocation_authority_v1,
    committed_balancing_point_allocation_authority_from_dict_v1,
    committed_balancing_point_allocation_authority_to_dict_v1,
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
        allocated_resistance_pa_per_kg_s2=allocated / (flow ** 2),
        status="Ready",
    )


def _route(
    route_id: str,
    required: float,
    contributors: tuple[str, ...],
) -> BalancingPointRouteConservationRowV1:
    allocated = {
        "route-one": 300.0,
        "route-two": 200.0,
    }[route_id]
    return BalancingPointRouteConservationRowV1(
        route_id=route_id,
        required_added_dp_pa=required,
        allocated_path_dp_pa=allocated,
        difference_pa=required - allocated,
        contributing_balancing_point_ids=contributors,
        conserved=True,
        status="Conserved",
    )


def _projection(*, ready: bool = True, blockers=()):
    return BalancingPointResistanceAllocationProjectionV1(
        ready=ready,
        rows=(
            _point(
                "point-shared",
                ("route-one", "route-two"),
                allocated=200.0,
                flow=0.20,
                shared=True,
            ),
            _point(
                "point-route-one",
                ("route-one",),
                allocated=100.0,
                flow=0.10,
                shared=False,
                parent="point-shared",
            ),
            _point(
                "point-route-two",
                ("route-two",),
                allocated=0.0,
                flow=0.08,
                shared=False,
                parent="point-shared",
            ),
        ),
        route_conservation=(
            _route(
                "route-one",
                300.0,
                ("point-shared", "point-route-one"),
            ),
            _route("route-two", 200.0, ("point-shared",)),
        ),
        blockers=tuple(blockers),
        status="Ready" if ready else "Blocked",
    )


def main() -> None:
    source = _projection()
    source_before = repr(source)
    authority = build_committed_balancing_point_allocation_authority_v1(
        source
    )

    assert authority.ready is True, authority.status
    assert len(authority.rows) == 3
    assert len(authority.route_conservation) == 2
    assert authority.rows[0].is_shared is True
    assert authority.rows[0].allocated_added_pressure_drop_Pa == 200.0
    assert authority.rows[1].parent_balancing_point_id == "point-shared"
    assert authority.rows[2].allocated_added_pressure_drop_Pa == 0.0
    assert authority.route_conservation[0].difference_Pa == 0.0
    assert authority.route_conservation[1].contributing_balancing_point_ids == (
        "point-shared",
    )
    assert repr(source) == source_before
    assert "No valve setting selected" in authority.exclusions
    assert "No ProjectState mutation" in authority.exclusions

    payload = committed_balancing_point_allocation_authority_to_dict_v1(
        authority
    )
    restored = (
        committed_balancing_point_allocation_authority_from_dict_v1(payload)
    )
    assert restored == authority

    repeated = build_committed_balancing_point_allocation_authority_v1(source)
    assert repeated == authority

    upstream = build_committed_balancing_point_allocation_authority_v1(
        _projection(ready=False, blockers=("route burden incomplete",))
    )
    assert upstream.ready is False
    assert upstream.blockers == ("H-S44-B: route burden incomplete",)

    duplicate = BalancingPointResistanceAllocationProjectionV1(
        ready=True,
        rows=(*source.rows, source.rows[0]),
        route_conservation=source.route_conservation,
    )
    duplicate_result = (
        build_committed_balancing_point_allocation_authority_v1(duplicate)
    )
    assert duplicate_result.ready is False
    assert "Duplicate committed balancing_point_id" in duplicate_result.status

    bad_conservation = BalancingPointResistanceAllocationProjectionV1(
        ready=True,
        rows=source.rows,
        route_conservation=(
            BalancingPointRouteConservationRowV1(
                route_id="route-one",
                required_added_dp_pa=300.0,
                allocated_path_dp_pa=200.0,
                difference_pa=100.0,
                contributing_balancing_point_ids=("point-shared",),
                conserved=False,
                status="Blocked",
            ),
            source.route_conservation[1],
        ),
    )
    bad_result = build_committed_balancing_point_allocation_authority_v1(
        bad_conservation
    )
    assert bad_result.ready is False
    assert "route-one" in bad_result.status

    absent = build_committed_balancing_point_allocation_authority_v1(None)
    assert absent.ready is False
    assert "H-S44-B" in absent.status

    print(
        "OK — H-S56-A committed balancing-point allocation authority passed."
    )


if __name__ == "__main__":
    main()
