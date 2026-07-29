from __future__ import annotations

from dataclasses import replace

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
)
from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    BalancingPointResistanceAllocationProjectionV1,
    BalancingPointResistanceAllocationRowV1,
    BalancingPointRouteConservationRowV1,
)
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    build_committed_balancing_point_allocation_authority_v1,
)
from HVAC.hydronics.proportioning.committed_point_level_balancing_reconciliation_v1 import (
    build_committed_point_level_balancing_reconciliation_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    CommittedPointValveBasisV1,
    ProportionedBasisSnapshotV1,
)


def _hydraulic_authority(
    *,
    route_one_added: float = 300.0,
) -> CommittedProportioningHydraulicInputAuthorityV1:
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
            route(
                "leg-a:route-one",
                1300.0 - route_one_added,
                route_one_added,
            ),
            route("leg-b:route-two", 1100.0, 200.0),
            route(
                "leg-c:route-control",
                1300.0,
                0.0,
                controlling=True,
            ),
        ),
        status="Ready",
    )


def _point_authority(
    *,
    route_one_required: float = 300.0,
):
    shared = 200.0
    exclusive = route_one_required - shared

    def point(
        point_id,
        route_ids,
        allocated,
        flow,
        shared_point,
        parent="",
    ):
        return BalancingPointResistanceAllocationRowV1(
            balancing_point_id=point_id,
            point_scope="main" if shared_point else "subleg",
            point_role=(
                "common_main_takeoff"
                if shared_point
                else "downstream-exclusive"
            ),
            label=point_id,
            parent_balancing_point_id=parent,
            anchor_section_id="section-1",
            downstream_route_ids=route_ids,
            is_shared=shared_point,
            is_route_exclusive=not shared_point,
            point_flow_kg_s=flow,
            allocated_added_dp_pa=allocated,
            allocated_resistance_pa_per_kg_s2=allocated / (flow ** 2),
            status="Ready",
        )

    projection = BalancingPointResistanceAllocationProjectionV1(
        ready=True,
        rows=(
            point(
                "point-shared",
                ("route-one", "route-two"),
                shared,
                0.20,
                True,
            ),
            point(
                "point-route-one",
                ("route-one",),
                exclusive,
                0.10,
                False,
                "point-shared",
            ),
            point(
                "point-control",
                ("route-control",),
                0.0,
                0.08,
                False,
            ),
        ),
        route_conservation=(
            BalancingPointRouteConservationRowV1(
                route_id="route-one",
                required_added_dp_pa=route_one_required,
                allocated_path_dp_pa=route_one_required,
                difference_pa=0.0,
                contributing_balancing_point_ids=(
                    "point-shared",
                    "point-route-one",
                ),
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
                difference_pa=-0.0,
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


def _bases(*point_ids):
    values = {
        "point-shared": 6.3,
        "point-route-one": 4.0,
        "point-control": 2.5,
    }
    return tuple(
        CommittedPointValveBasisV1(
            balancing_point_id=point_id,
            accepted_kvs_basis=values[point_id],
            disposition=APPROVED_FOR_PRODUCT_SEARCH,
        )
        for point_id in point_ids
    )


def _snapshot(
    *,
    route_one_added=300.0,
    route_one_required=300.0,
    bases=("point-shared", "point-route-one"),
):
    return ProportionedBasisSnapshotV1(
        hydraulic_input_authority=_hydraulic_authority(
            route_one_added=route_one_added
        ),
        point_allocation_authority=_point_authority(
            route_one_required=route_one_required
        ),
        committed_point_valve_bases=_bases(*bases),
    )


def main() -> None:
    snapshot = _snapshot()
    before = repr(snapshot)
    result = build_committed_point_level_balancing_reconciliation_v1(
        snapshot
    )

    assert result.ready is True, result.status
    assert len(result.point_rows) == 3
    assert len(result.route_rows) == 3
    point_by_id = {
        row.balancing_point_id: row for row in result.point_rows
    }
    assert point_by_id["point-shared"].is_shared is True
    assert point_by_id["point-shared"].accepted_kvs_basis == 6.3
    assert point_by_id["point-route-one"].accepted_kvs_basis == 4.0
    assert point_by_id["point-control"].valve_duty_required is False
    assert point_by_id["point-control"].accepted_kvs_basis is None

    route_by_id = {
        row.committed_route_id: row for row in result.route_rows
    }
    route_one = route_by_id["leg-a:route-one"]
    assert route_one.allocation_route_id == "route-one"
    assert route_one.required_added_pressure_drop_Pa == 300.0
    assert route_one.allocated_path_pressure_drop_Pa == 300.0
    assert route_one.residual_Pa == 0.0
    assert route_one.contributing_balancing_point_ids == (
        "point-shared",
        "point-route-one",
    )
    assert route_by_id["leg-b:route-two"].residual_Pa == 0.0
    assert route_by_id["leg-c:route-control"].residual_Pa == 0.0
    assert "No live hydraulic or point preview used" in result.exclusions
    assert "No valve setting selected" in result.exclusions
    assert repr(snapshot) == before

    repeated = build_committed_point_level_balancing_reconciliation_v1(
        snapshot
    )
    assert repeated == result

    missing_basis = build_committed_point_level_balancing_reconciliation_v1(
        _snapshot(bases=("point-shared",))
    )
    assert missing_basis.ready is False
    assert "point-route-one" in missing_basis.status

    stale_basis = build_committed_point_level_balancing_reconciliation_v1(
        _snapshot(
            bases=("point-shared", "point-route-one", "point-control")
        )
    )
    assert stale_basis.ready is False
    assert "no positive point allocation" in stale_basis.status

    route_mismatch = (
        build_committed_point_level_balancing_reconciliation_v1(
            _snapshot(
                route_one_added=300.0,
                route_one_required=250.0,
            )
        )
    )
    assert route_mismatch.ready is False
    assert "differs from point-allocation" in route_mismatch.status

    no_point_authority = (
        build_committed_point_level_balancing_reconciliation_v1(
            replace(snapshot, point_allocation_authority=None)
        )
    )
    assert no_point_authority.ready is False
    assert "H-S56-A" in no_point_authority.status

    absent = build_committed_point_level_balancing_reconciliation_v1(None)
    assert absent.ready is False
    assert "snapshot required" in absent.status

    print(
        "OK — H-S56-C committed point-level balancing reconciliation "
        "result passed."
    )


if __name__ == "__main__":
    main()
