# ======================================================================
# H-S58-A — Committed Proportioned-system completion status test
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import HVAC.hydronics.proportioning.committed_proportioned_system_completion_status_v1 as completion_module
from HVAC.hydronics.proportioning.committed_basis_route_proportioning_result_v1 import (
    CommittedBasisRouteProportioningResultRowV1,
    CommittedBasisRouteProportioningResultV1,
)
from HVAC.hydronics.proportioning.committed_basis_section_hydraulic_result_v1 import (
    CommittedBasisSectionHydraulicResultV1,
    CommittedBasisSectionHydraulicRowV1,
)
from HVAC.hydronics.proportioning.committed_point_level_balancing_reconciliation_v1 import (
    CommittedPointBalancingReconciliationRowV1,
    CommittedPointLevelBalancingReconciliationV1,
    CommittedRoutePointReconciliationRowV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


def _route_result():
    rows = tuple(
        CommittedBasisRouteProportioningResultRowV1(
            route_id=route_id,
            route_label=label,
            basis="F&R",
            controlling=index == 0,
            chosen_pressure_drop_Pa=40_000.0 - (index * 1_000.0),
            required_added_pressure_drop_Pa=index * 1_000.0,
            proportioned_pressure_drop_Pa=40_000.0,
            controlling_target_pressure_drop_Pa=40_000.0,
            residual_to_target_Pa=0.0,
            within_tolerance=True,
            ready=True,
            status="Ready",
        )
        for index, (route_id, label) in enumerate(
            (
                ("route-a", "Route A"),
                ("route-b", "Route B"),
            )
        )
    )
    return CommittedBasisRouteProportioningResultV1(
        ready=True,
        controlling_target_pressure_drop_Pa=40_000.0,
        rows=rows,
        status="Ready",
    )


def _point_result():
    return CommittedPointLevelBalancingReconciliationV1(
        ready=True,
        point_rows=(
            CommittedPointBalancingReconciliationRowV1(
                balancing_point_id="point-shared",
                valve_duty_required=True,
                reconciled=True,
                ready=True,
                status="Ready",
            ),
            CommittedPointBalancingReconciliationRowV1(
                balancing_point_id="point-control",
                valve_duty_required=False,
                reconciled=True,
                ready=True,
                status="Ready",
            ),
        ),
        route_rows=(
            CommittedRoutePointReconciliationRowV1(
                committed_route_id="route-a",
                reconciled=True,
                ready=True,
                status="Ready",
            ),
            CommittedRoutePointReconciliationRowV1(
                committed_route_id="route-b",
                reconciled=True,
                ready=True,
                status="Ready",
            ),
        ),
        status="Ready",
    )


def _section_row(route_id: str, label: str):
    return CommittedBasisSectionHydraulicRowV1(
        committed_route_id=route_id,
        committed_route_label=label,
        basis="F&R",
        section_id="common-main-001",
        section_scope="common_main",
        route_ids=("route-a", "route-b"),
        shared_across_routes=True,
        order=1,
        from_label="Boiler / Heat Source",
        to_label="Common main",
        carried_flow_kg_s=0.2,
        pipe_size_label="22 mm",
        dn=22,
        length_m=10.0,
        k_total=1.5,
        velocity_m_s=0.5,
        reynolds_number=10_000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=5,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=200.0,
        straight_pressure_drop_Pa=2_000.0,
        local_pressure_drop_Pa=100.0,
        section_total_pressure_drop_Pa=2_100.0,
    )


def _section_result():
    return CommittedBasisSectionHydraulicResultV1(
        ready=True,
        rows=(
            _section_row("route-a", "Route A"),
            _section_row("route-b", "Route B"),
        ),
        unique_section_count=1,
        route_count=2,
        status="Ready",
    )


def _build(snapshot, route_result=None, point_result=None, section_result=None):
    route_result = route_result or _route_result()
    point_result = point_result or _point_result()
    section_result = section_result or _section_result()
    with (
        patch.object(
            completion_module,
            "build_committed_basis_route_proportioning_result_v1",
            return_value=route_result,
        ),
        patch.object(
            completion_module,
            "build_committed_point_level_balancing_reconciliation_v1",
            return_value=point_result,
        ),
        patch.object(
            completion_module,
            "build_committed_basis_section_hydraulic_result_v1",
            return_value=section_result,
        ),
    ):
        return (
            completion_module
            .build_committed_proportioned_system_completion_status_v1(
                snapshot
            )
        )


def main() -> None:
    snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis="DIRECT_RETURN",
    )
    before = repr(snapshot)
    result = _build(snapshot)

    assert result.ready is True, result.status
    assert result.accepted_return_arrangement_basis == "DIRECT_RETURN"
    assert result.controlling_target_pressure_drop_Pa == 40_000.0
    assert result.route_count == 2
    assert result.routes_at_target_count == 2
    assert result.balancing_point_count == 2
    assert result.reconciled_balancing_point_count == 2
    assert result.valve_duty_point_count == 1
    assert result.unique_section_count == 1
    assert result.route_addressable_section_count == 2
    assert "No pump selection" in result.exclusions
    assert "No valve product selected" in result.exclusions
    assert "No ProjectState mutation" in result.exclusions
    assert repr(snapshot) == before
    assert _build(snapshot) == result

    blocked_route = _build(
        snapshot,
        route_result=replace(
            _route_result(),
            ready=False,
            status="Blocked",
            blockers=("route convergence incomplete",),
        ),
    )
    assert blocked_route.ready is False
    assert "H-S55-A: route convergence incomplete" in (
        blocked_route.blockers
    )

    mismatched_sections = _build(
        snapshot,
        section_result=CommittedBasisSectionHydraulicResultV1(
            ready=True,
            rows=(_section_row("route-a", "Route A"),),
            unique_section_count=1,
            route_count=1,
            status="Ready",
        ),
    )
    assert mismatched_sections.ready is False
    assert "H-S57-A committed route identities" in (
        mismatched_sections.status
    )

    unreconciled_point = replace(
        _point_result().point_rows[0],
        reconciled=False,
        ready=False,
    )
    blocked_point = _build(
        snapshot,
        point_result=replace(
            _point_result(),
            point_rows=(
                unreconciled_point,
                _point_result().point_rows[1],
            ),
        ),
    )
    assert blocked_point.ready is False
    assert "Every H-S56-C balancing point must reconcile" in (
        blocked_point.blockers
    )

    undecided = _build(
        replace(snapshot, return_arrangement_basis="UNDECIDED")
    )
    assert undecided.ready is False
    assert "accepted return arrangement basis" in undecided.status

    absent = (
        completion_module
        .build_committed_proportioned_system_completion_status_v1(None)
    )
    assert absent.ready is False
    assert "committed proportioning snapshot required" in absent.status

    print(
        "OK — H-S58-A committed Proportioned-system completion status "
        "passed."
    )


if __name__ == "__main__":
    main()
