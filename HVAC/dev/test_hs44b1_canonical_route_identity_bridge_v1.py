from __future__ import annotations

from types import SimpleNamespace

from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    build_balancing_point_resistance_allocation_v1,
)
from HVAC.hydronics.proportioning.balancing_point_topology_authority_v1 import (
    BalancingPointTopologyProjectionV1,
    BalancingPointTopologyRowV1,
)


def _point(
    point_id: str,
    scope: str,
    parent_id: str,
    routes: tuple[str, ...],
    *,
    leg_id: str = "leg-001",
    subleg_id: str = "",
) -> BalancingPointTopologyRowV1:
    return BalancingPointTopologyRowV1(
        balancing_point_id=point_id,
        point_scope=scope,
        point_role="test",
        label=point_id,
        leg_id=leg_id,
        subleg_id=subleg_id,
        parent_balancing_point_id=parent_id,
        anchor_section_id=f"{point_id}-section-001",
        origin_room_id="",
        downstream_route_ids=routes,
        is_shared=len(routes) > 1,
        is_route_exclusive=len(routes) == 1,
        status="Test topology point",
    )


def main() -> None:
    common = "leg-001-primary-subleg"
    branch = "leg-001-subleg-b"
    main_id = "balancing-point:main:leg-001"
    common_id = f"balancing-point:subleg:{common}"
    branch_id = f"balancing-point:subleg:{branch}"

    points = (
        _point(main_id, "main", "", (common, branch)),
        _point(common_id, "subleg", main_id, (common,), subleg_id=common),
        _point(branch_id, "subleg", main_id, (branch,), subleg_id=branch),
    )
    topology = BalancingPointTopologyProjectionV1(
        ready=True,
        points=points,
        main_points=(points[0],),
        leg_points=(),
        subleg_points=points[1:],
        blockers=(),
        status="Test topology ready",
    )

    # Live chosen-pressure rows use leg_id:subleg_id. H-S44 topology retains
    # the stable physical subleg identity. The bridge must be deterministic.
    resistance = SimpleNamespace(
        ready=True,
        blockers=(),
        rows=(
            SimpleNamespace(
                route_id=f"leg-001:{common}",
                flow_kg_s="0.16990 kg/s",
                required_added_dp="1968.3 Pa",
            ),
            SimpleNamespace(
                route_id=f"leg-001:{branch}",
                flow_kg_s="0.07660 kg/s",
                required_added_dp="0.0 Pa",
            ),
        ),
    )

    result = build_balancing_point_resistance_allocation_v1(
        topology=topology,
        resistance_basis=resistance,
    )

    assert result.ready is True, result.blockers
    assert len(result.rows) == 3
    assert len(result.route_conservation) == 2
    by_route = {row.route_id: row for row in result.route_conservation}
    assert set(by_route) == {common, branch}
    assert by_route[common].conserved is True
    assert by_route[branch].conserved is True
    assert abs(by_route[common].difference_pa) <= 0.05
    assert abs(by_route[branch].difference_pa) <= 0.05

    by_point = {row.balancing_point_id: row for row in result.rows}
    assert by_point[main_id].allocated_added_dp_pa == 0.0
    assert by_point[common_id].allocated_added_dp_pa == 1968.3
    assert by_point[branch_id].allocated_added_dp_pa == 0.0

    # Exact bare subleg identities remain accepted for existing callers.
    exact = SimpleNamespace(
        ready=True,
        blockers=(),
        rows=(
            SimpleNamespace(
                route_id=common,
                flow_kg_s="0.16990 kg/s",
                required_added_dp="1968.3 Pa",
            ),
            SimpleNamespace(
                route_id=branch,
                flow_kg_s="0.07660 kg/s",
                required_added_dp="0.0 Pa",
            ),
        ),
    )
    exact_result = build_balancing_point_resistance_allocation_v1(
        topology=topology,
        resistance_basis=exact,
    )
    assert exact_result.ready is True, exact_result.blockers

    print(
        "OK — H-S44-B1 canonical chosen-route identity bridges to "
        "stable balancing-point topology without double counting."
    )


if __name__ == "__main__":
    main()
