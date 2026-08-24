from __future__ import annotations

from dataclasses import replace

from HVAC.hydronics.proportioning.balancing_completion_readiness_v1 import (
    build_balancing_completion_readiness_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
)
from HVAC.hydronics.proportioning.balancing_point_topology_authority_v1 import (
    BalancingPointTopologyProjectionV1,
    BalancingPointTopologyRowV1,
)
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    CommittedBalancingPointAllocationAuthorityV1,
    CommittedBalancingPointAllocationRowV1,
    CommittedBalancingPointRouteConservationRowV1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    CommittedPointValveBasisV1,
    ProportionedBasisSnapshotV1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    UNDECIDED,
)


POINT_DUTY = "balancing-point:subleg:route-one"
POINT_CONTROL = "balancing-point:subleg:route-control"


def _topology(*, extra: bool = False):
    def point(point_id: str, route_id: str):
        return BalancingPointTopologyRowV1(
            balancing_point_id=point_id,
            point_scope="subleg",
            point_role="downstream-exclusive",
            label=point_id,
            leg_id="leg-a",
            subleg_id=route_id,
            parent_balancing_point_id="",
            anchor_section_id=f"{route_id}-section-001",
            origin_room_id="",
            downstream_route_ids=(route_id,),
            is_shared=False,
            is_route_exclusive=True,
            status="Ready",
        )

    points = [
        point(POINT_DUTY, "route-one"),
        point(POINT_CONTROL, "route-control"),
    ]
    if extra:
        points.append(point("balancing-point:subleg:uncovered", "uncovered"))
    return BalancingPointTopologyProjectionV1(
        ready=True,
        points=tuple(points),
        main_points=(),
        leg_points=(),
        subleg_points=tuple(points),
        status="Ready",
    )


def _hydraulic():
    def route(route_id, chosen, added, controlling=False):
        return CommittedProportioningHydraulicRouteV1(
            route_id=route_id,
            route_label=route_id,
            basis="F&R",
            chosen_pressure_drop_Pa=chosen,
            controlling=controlling,
            required_added_pressure_drop_Pa=added,
            preliminary_resistance_Pa_per_kg_s2=1.0,
            common_main_pressure_drop_Pa=100.0,
            leg_entry_pressure_drop_Pa=50.0,
            physical_main_entry_pressure_drop_Pa=150.0,
        )

    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        routes=(
            route("leg-a:route-one", 1000.0, 300.0),
            route("leg-b:route-control", 1300.0, 0.0, True),
        ),
        status="Ready",
    )


def _allocation():
    def point(point_id, route_id, allocated, flow):
        return CommittedBalancingPointAllocationRowV1(
            balancing_point_id=point_id,
            point_scope="subleg",
            point_role="downstream-exclusive",
            label=point_id,
            parent_balancing_point_id="",
            anchor_section_id=f"{route_id}-section-001",
            downstream_route_ids=(route_id,),
            is_shared=False,
            is_route_exclusive=True,
            point_flow_kg_s=flow,
            allocated_added_pressure_drop_Pa=allocated,
            allocated_resistance_Pa_per_kg_s2=(
                allocated / flow**2 if allocated else 0.0
            ),
            status="Committed",
        )

    return CommittedBalancingPointAllocationAuthorityV1(
        ready=True,
        rows=(
            point(POINT_DUTY, "route-one", 300.0, 0.10),
            point(POINT_CONTROL, "route-control", 0.0, 0.08),
        ),
        route_conservation=(
            CommittedBalancingPointRouteConservationRowV1(
                route_id="route-one",
                required_added_pressure_drop_Pa=300.0,
                allocated_path_pressure_drop_Pa=300.0,
                difference_Pa=0.0,
                contributing_balancing_point_ids=(POINT_DUTY,),
                conserved=True,
                status="Conserved",
            ),
            CommittedBalancingPointRouteConservationRowV1(
                route_id="route-control",
                required_added_pressure_drop_Pa=0.0,
                allocated_path_pressure_drop_Pa=0.0,
                difference_Pa=0.0,
                contributing_balancing_point_ids=(),
                conserved=True,
                status="Conserved",
            ),
        ),
        status="Ready",
    )


def _snapshot(*, with_kvs=True):
    bases = (
        CommittedPointValveBasisV1(
            balancing_point_id=POINT_DUTY,
            accepted_kvs_basis=1.6,
            disposition=APPROVED_FOR_PRODUCT_SEARCH,
        ),
    ) if with_kvs else ()
    return ProportionedBasisSnapshotV1(
        return_arrangement_basis="F&R",
        hydraulic_input_authority=_hydraulic(),
        point_allocation_authority=_allocation(),
        committed_point_valve_bases=bases,
    )


def main() -> None:
    snapshot = _snapshot()
    topology = _topology()
    before_snapshot = repr(snapshot)
    before_topology = repr(topology)

    result = build_balancing_completion_readiness_v1(
        snapshot=snapshot,
        topology=topology,
    )
    repeated = build_balancing_completion_readiness_v1(
        snapshot=snapshot,
        topology=topology,
    )
    assert result == repeated
    assert result.ready is True, result.status
    assert result.accepted_proportioning_basis_ready is True
    assert result.point_coverage_ready is True
    assert result.allocation_conservation_ready is True
    assert result.point_kvs_basis_ready is True
    assert result.expected_point_ids == (POINT_DUTY, POINT_CONTROL)
    assert result.valve_duty_point_ids == (POINT_DUTY,)
    assert repr(snapshot) == before_snapshot
    assert repr(topology) == before_topology

    uncovered = build_balancing_completion_readiness_v1(
        snapshot=snapshot,
        topology=_topology(extra=True),
    )
    assert uncovered.ready is False
    assert uncovered.uncovered_point_ids == (
        "balancing-point:subleg:uncovered",
    )
    assert "missing committed allocation" in uncovered.status

    missing_kvs = build_balancing_completion_readiness_v1(
        snapshot=_snapshot(with_kvs=False),
        topology=topology,
    )
    assert missing_kvs.ready is False
    assert missing_kvs.point_kvs_basis_ready is False
    assert missing_kvs.missing_kvs_point_ids == (POINT_DUTY,)
    assert "missing approved generic-Kvs basis" in missing_kvs.status

    authority = _allocation()
    broken_route = replace(
        authority.route_conservation[0],
        conserved=False,
    )
    broken_snapshot = replace(
        snapshot,
        point_allocation_authority=replace(
            authority,
            route_conservation=(
                broken_route,
                authority.route_conservation[1],
            ),
        ),
    )
    unconserved = build_balancing_completion_readiness_v1(
        snapshot=broken_snapshot,
        topology=topology,
    )
    assert unconserved.ready is False
    assert unconserved.allocation_conservation_ready is False
    assert unconserved.unconserved_route_ids == ("leg-a:route-one",)

    undecided = build_balancing_completion_readiness_v1(
        snapshot=replace(snapshot, return_arrangement_basis=UNDECIDED),
        topology=topology,
    )
    assert undecided.ready is False
    assert undecided.accepted_proportioning_basis_ready is False
    assert "accepted return arrangement basis required" in undecided.status

    assert "No ProjectState mutation" in result.exclusions
    assert "No balancing method accepted" in result.exclusions
    assert "No final balancing schedule committed" in result.exclusions
    assert "No valve product or setting selected" in result.exclusions
    assert "No pump duty or pump selection" in result.exclusions

    print(
        "OK — H-S70-A reports accepted-basis, current point coverage, "
        "allocation conservation and approved generic-Kvs readiness with "
        "exact blockers and no mutation."
    )


if __name__ == "__main__":
    main()
