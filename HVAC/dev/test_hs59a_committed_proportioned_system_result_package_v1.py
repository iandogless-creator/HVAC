# ======================================================================
# H-S59-A — Committed Proportioned-system aggregate result package test
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import HVAC.hydronics.proportioning.committed_proportioned_system_result_package_v1 as package_module
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
)
from HVAC.hydronics.proportioning.committed_proportioned_system_completion_status_v1 import (
    CommittedProportionedSystemCompletionStatusV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


def _route_result():
    return CommittedBasisRouteProportioningResultV1(
        ready=True,
        controlling_target_pressure_drop_Pa=40_000.0,
        rows=(
            CommittedBasisRouteProportioningResultRowV1(
                route_id="route-a",
                route_label="Route A",
                basis="F&R",
                controlling=True,
                proportioned_pressure_drop_Pa=40_000.0,
                controlling_target_pressure_drop_Pa=40_000.0,
                residual_to_target_Pa=0.0,
                within_tolerance=True,
                ready=True,
                status="Ready",
            ),
        ),
        status="Ready",
    )


def _point_result():
    return CommittedPointLevelBalancingReconciliationV1(
        ready=True,
        point_rows=(
            CommittedPointBalancingReconciliationRowV1(
                balancing_point_id="point-a",
                valve_duty_required=True,
                reconciled=True,
                ready=True,
                status="Ready",
            ),
        ),
        status="Ready",
    )


def _section_result():
    return CommittedBasisSectionHydraulicResultV1(
        ready=True,
        rows=(
            CommittedBasisSectionHydraulicRowV1(
                committed_route_id="route-a",
                committed_route_label="Route A",
                basis="F&R",
                section_id="section-a",
                section_scope="route",
                route_ids=("route-a",),
                shared_across_routes=False,
                order=1,
                from_label="Boiler / Heat Source",
                to_label="Route A",
                carried_flow_kg_s=0.1,
                pipe_size_label="15 mm",
                dn=15,
                length_m=5.0,
                k_total=1.0,
                velocity_m_s=0.5,
                reynolds_number=10_000.0,
                friction_factor=0.03,
                friction_method="colebrook",
                colebrook_iteration_count=5,
                colebrook_converged=True,
                pressure_gradient_Pa_per_m=200.0,
                straight_pressure_drop_Pa=1_000.0,
                local_pressure_drop_Pa=100.0,
                section_total_pressure_drop_Pa=1_100.0,
            ),
        ),
        unique_section_count=1,
        route_count=1,
        status="Ready",
    )


def _completion():
    return CommittedProportionedSystemCompletionStatusV1(
        ready=True,
        accepted_return_arrangement_basis="DIRECT_RETURN",
        controlling_target_pressure_drop_Pa=40_000.0,
        route_count=1,
        routes_at_target_count=1,
        balancing_point_count=1,
        reconciled_balancing_point_count=1,
        valve_duty_point_count=1,
        unique_section_count=1,
        route_addressable_section_count=1,
        status="Ready",
    )


def _build(
    snapshot,
    *,
    route_result=None,
    point_result=None,
    section_result=None,
    completion=None,
):
    route_result = route_result or _route_result()
    point_result = point_result or _point_result()
    section_result = section_result or _section_result()
    completion = completion or _completion()
    with (
        patch.object(
            package_module,
            "build_committed_basis_route_proportioning_result_v1",
            return_value=route_result,
        ),
        patch.object(
            package_module,
            "build_committed_point_level_balancing_reconciliation_v1",
            return_value=point_result,
        ),
        patch.object(
            package_module,
            "build_committed_basis_section_hydraulic_result_v1",
            return_value=section_result,
        ),
        patch.object(
            package_module,
            "build_committed_proportioned_system_completion_status_v1",
            return_value=completion,
        ),
    ):
        return (
            package_module
            .build_committed_proportioned_system_result_package_v1(snapshot)
        )


def main() -> None:
    snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis="DIRECT_RETURN",
    )
    before = repr(snapshot)
    result = _build(snapshot)

    assert result.ready is True, result.status
    assert result.source_snapshot_schema == snapshot.schema
    assert result.accepted_return_arrangement_basis == "DIRECT_RETURN"
    assert result.route_result == _route_result()
    assert result.point_reconciliation == _point_result()
    assert result.section_result == _section_result()
    assert result.completion_status == _completion()
    assert result.route_count == 1
    assert result.balancing_point_count == 1
    assert result.unique_section_count == 1
    assert result.route_addressable_section_count == 1
    assert "No ProjectState mutation" in " | ".join(result.exclusions)
    assert "No pump selection" in result.exclusions
    assert "No valve product selected" in result.exclusions
    assert repr(snapshot) == before
    assert _build(snapshot) == result

    blocked_route = _build(
        snapshot,
        route_result=replace(
            _route_result(),
            ready=False,
            status="Blocked",
            blockers=("route result incomplete",),
        ),
    )
    assert blocked_route.ready is False
    assert "H-S55-A: route result incomplete" in blocked_route.blockers

    blocked_completion = _build(
        snapshot,
        completion=replace(
            _completion(),
            ready=False,
            status="Blocked",
            blockers=("system completion incomplete",),
        ),
    )
    assert blocked_completion.ready is False
    assert "H-S58-A: system completion incomplete" in (
        blocked_completion.blockers
    )

    mismatched_count = _build(
        snapshot,
        completion=replace(_completion(), balancing_point_count=2),
    )
    assert mismatched_count.ready is False
    assert "balancing-point count must match" in mismatched_count.status

    mismatched_basis = _build(
        snapshot,
        completion=replace(
            _completion(),
            accepted_return_arrangement_basis="REVERSE_RETURN",
        ),
    )
    assert mismatched_basis.ready is False
    assert "accepted return basis must match" in mismatched_basis.status

    absent = (
        package_module
        .build_committed_proportioned_system_result_package_v1(None)
    )
    assert absent.ready is False
    assert "committed proportioning snapshot required" in absent.status

    print(
        "OK — H-S59-A committed Proportioned-system result package passed."
    )


if __name__ == "__main__":
    main()
