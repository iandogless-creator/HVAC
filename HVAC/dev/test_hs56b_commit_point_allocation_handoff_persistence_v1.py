from __future__ import annotations

from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_proportioning_commit_readiness_v1 import (
    PointProportioningCommitReadinessV1,
)
from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    BalancingPointResistanceAllocationProjectionV1,
    BalancingPointResistanceAllocationRowV1,
    BalancingPointRouteConservationRowV1,
)
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    build_committed_balancing_point_allocation_authority_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    build_proportioned_basis_snapshot_v1,
    proportioned_basis_snapshot_from_dict_v1,
    proportioned_basis_snapshot_to_dict_v1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    ReturnArrangementIntentV1,
)
from HVAC.project.project_state import ProjectState


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


def _authority():
    projection = BalancingPointResistanceAllocationProjectionV1(
        ready=True,
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
        ),
        route_conservation=(
            BalancingPointRouteConservationRowV1(
                route_id="route-one",
                required_added_dp_pa=300.0,
                allocated_path_dp_pa=300.0,
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
                difference_pa=-0.0,
                contributing_balancing_point_ids=("point-shared",),
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


def main() -> None:
    project = ProjectState(project_id="hs56b", name="H-S56-B")
    project.hydronic_return_arrangement_intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
    )
    point_authority = _authority()
    hydraulic_authority = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        status="Ready",
    )
    result = build_proportioned_basis_snapshot_v1(
        project,
        point_commit_readiness=PointProportioningCommitReadinessV1(
            ready=True,
            rows=(),
        ),
        hydraulic_input_authority=hydraulic_authority,
        point_allocation_authority=point_authority,
    )

    assert result.ready is True, result.status
    snapshot = result.snapshot
    assert snapshot is not None
    assert snapshot.point_allocation_authority == point_authority
    assert "committed balancing-point" in (
        snapshot.point_allocation_authority_status.lower()
    )

    payload = proportioned_basis_snapshot_to_dict_v1(snapshot)
    assert payload is not None
    assert payload["point_allocation_authority"]["ready"] is True
    assert len(payload["point_allocation_authority"]["rows"]) == 2
    restored = proportioned_basis_snapshot_from_dict_v1(payload)
    assert restored is not None
    assert restored.point_allocation_authority == point_authority

    project.hydronic_proportioned_basis_snapshot = snapshot
    restored_project = ProjectState.from_dict(project.to_dict())
    restored_snapshot = restored_project.hydronic_proportioned_basis_snapshot
    assert restored_snapshot is not None
    assert restored_snapshot.point_allocation_authority == point_authority

    old_payload = dict(payload)
    old_payload.pop("point_allocation_authority")
    old_payload.pop("point_allocation_authority_status")
    restored_old = proportioned_basis_snapshot_from_dict_v1(old_payload)
    assert restored_old is not None
    assert restored_old.point_allocation_authority is None
    assert "no committed" in (
        restored_old.point_allocation_authority_status.lower()
    )

    blocked = build_proportioned_basis_snapshot_v1(
        project,
        point_commit_readiness=PointProportioningCommitReadinessV1(
            ready=True,
            rows=(),
        ),
        hydraulic_input_authority=hydraulic_authority,
        point_allocation_authority=type(point_authority)(
            ready=False,
            blockers=("point allocation incomplete",),
            status="Blocked",
        ),
    )
    assert blocked.ready is False
    assert blocked.snapshot is None
    assert "point allocation incomplete" in blocked.status

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert (
        "build_committed_balancing_point_allocation_authority_v1"
        in adapter_source
    )
    assert (
        "_committed_balancing_point_allocation_projection_v1"
        in adapter_source
    )
    assert "point_allocation_authority=point_allocation_authority" in (
        adapter_source
    )
    assert "H-S56-B Commit Proportioning blocked:" in adapter_source

    print(
        "OK — H-S56-B Commit Proportioning point-allocation handoff and "
        "snapshot persistence passed."
    )


if __name__ == "__main__":
    main()
