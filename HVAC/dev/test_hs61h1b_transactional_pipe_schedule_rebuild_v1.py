# ======================================================================
# H-S61-H1B — Transactional accepted pipe-schedule hydraulic rebuild
# ======================================================================

from __future__ import annotations

from dataclasses import replace

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
)
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    CommittedBalancingPointAllocationAuthorityV1,
    CommittedBalancingPointAllocationRowV1,
    CommittedBalancingPointRouteConservationRowV1,
)
from HVAC.hydronics.proportioning.committed_basis_route_proportioning_result_v1 import (
    build_committed_basis_route_proportioning_result_v1,
)
from HVAC.hydronics.proportioning.committed_point_level_balancing_reconciliation_v1 import (
    build_committed_point_level_balancing_reconciliation_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
    CommittedProportioningHydraulicSectionV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    CommittedPointValveBasisV1,
    ProportionedBasisSnapshotV1,
    proportioned_basis_snapshot_from_dict_v1,
    proportioned_basis_snapshot_to_dict_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_material_family_intent_v1 import (
    ProportionedPipeMaterialFamilyIntentV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import (
    ProportionedPipeResizingHydraulicProjectionV1,
    ProportionedResizedRouteHydraulicProjectionV1,
    ProportionedResizedSectionHydraulicProjectionV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_resizing_schedule_acceptance_intent_v1 import (
    ResolvedProportionedPipeResizingScheduleAcceptanceV1,
    ResolvedProportionedPipeSectionDNAcceptanceV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_schedule_commit_rebuild_v1 import (
    COMMITTED_RESIZED_HYDRAULICS_STATUS_V1,
    build_proportioned_pipe_schedule_commit_rebuild_v1,
)
from HVAC.hydronics.proportioning.resized_balancing_point_reconciliation_v1 import (
    ResizedBalancingPointReconciliationV1,
    ResizedBalancingPointReconciliationRowV1,
    ResizedBalancingRouteReconciliationRowV1,
)


def _old_section(
        section_id: str,
        route_id: str,
        *,
        total: float,
) -> CommittedProportioningHydraulicSectionV1:
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="subleg",
        route_ids=(route_id,),
        order=1,
        from_label="A",
        to_label="B",
        carried_flow_kg_s=0.10,
        pipe_size_label="22 mm",
        dn=22,
        length_m=5.0,
        k_total=1.0,
        velocity_m_s=0.32,
        reynolds_number=9000.0,
        friction_factor=0.031,
        friction_method="colebrook",
        colebrook_iteration_count=5,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=(total - 20.0) / 5.0,
        straight_pressure_drop_Pa=total - 20.0,
        local_pressure_drop_Pa=20.0,
        section_total_pressure_drop_Pa=total,
        material_key="copper",
        material_label="Copper EN1057",
        internal_diameter_m=0.020,
        material_roughness_m=0.0000015,
    )


def _old_route(
        route_id: str,
        *,
        total: float,
        added: float,
        controlling: bool,
) -> CommittedProportioningHydraulicRouteV1:
    return CommittedProportioningHydraulicRouteV1(
        route_id=route_id,
        route_label=route_id.title(),
        basis="F+R",
        chosen_pressure_drop_Pa=total,
        controlling=controlling,
        required_added_pressure_drop_Pa=added,
        preliminary_resistance_Pa_per_kg_s2=(
            added / 0.01 if added else 0.0
        ),
        common_main_pressure_drop_Pa=None,
        leg_entry_pressure_drop_Pa=None,
        physical_main_entry_pressure_drop_Pa=None,
    )


def _projected_section(
        section_id: str,
        route_id: str,
        *,
        total: float,
) -> ProportionedResizedSectionHydraulicProjectionV1:
    return ProportionedResizedSectionHydraulicProjectionV1(
        section_id=section_id,
        section_scope="subleg",
        route_ids=(route_id,),
        order=1,
        from_label="A",
        to_label="B",
        carried_flow_kg_s=0.10,
        length_m=5.0,
        k_total=1.0,
        current_dn=22,
        current_pipe_size_label="22 mm",
        projected_dn=20,
        projected_pipe_size_label="20×2 mm",
        recommendation="Resize",
        internal_diameter_m=0.016,
        velocity_m_s=0.50,
        maximum_velocity_m_s=1.0,
        velocity_within_limit=True,
        pressure_gradient_Pa_per_m=(total - 20.0) / 5.0,
        maximum_pressure_gradient_Pa_per_m=300.0,
        pressure_gradient_within_limit=True,
        straight_pressure_drop_Pa=total - 20.0,
        local_pressure_drop_Pa=20.0,
        section_total_pressure_drop_Pa=total,
        reynolds_number=12000.0,
        friction_factor=0.030,
        friction_method="colebrook",
        colebrook_iteration_count=5,
        colebrook_converged=True,
        status="Projected",
        current_material_key="copper",
        current_material_label="Copper EN1057",
        current_internal_diameter_m=0.020,
        projected_material_key="mlcp",
        projected_material_label="MLCP",
    )


def _route_projection(
        route_id: str,
        section_id: str,
        *,
        total: float,
        added: float,
        controlling: bool,
        rank: int,
) -> ProportionedResizedRouteHydraulicProjectionV1:
    return ProportionedResizedRouteHydraulicProjectionV1(
        route_id=route_id,
        section_ids=(section_id,),
        section_count=1,
        straight_pressure_drop_total_Pa=total - 20.0,
        local_pressure_drop_total_Pa=20.0,
        route_pressure_drop_total_Pa=total,
        controlling_target_Pa=1000.0,
        required_added_dp_Pa=added,
        rank=rank,
        is_controlling=controlling,
        status="Projected",
    )


def _fixtures():
    old_hydraulic = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=(
            _old_section("section-a", "route-a", total=900.0),
            _old_section("section-b", "route-b", total=700.0),
        ),
        routes=(
            _old_route(
                "route-a", total=900.0, added=0.0, controlling=True
            ),
            _old_route(
                "route-b", total=700.0, added=200.0, controlling=False
            ),
        ),
        status="Ready",
    )
    old_allocation = CommittedBalancingPointAllocationAuthorityV1(
        ready=True,
        rows=(
            CommittedBalancingPointAllocationRowV1(
                balancing_point_id="point-b",
                point_scope="route",
                point_role="route_exclusive",
                label="Point B",
                parent_balancing_point_id="",
                anchor_section_id="section-b",
                downstream_route_ids=("route-b",),
                is_shared=False,
                is_route_exclusive=True,
                point_flow_kg_s=0.10,
                allocated_added_pressure_drop_Pa=200.0,
                allocated_resistance_Pa_per_kg_s2=20000.0,
                status="Old",
            ),
        ),
        route_conservation=(
            CommittedBalancingPointRouteConservationRowV1(
                route_id="route-a",
                required_added_pressure_drop_Pa=0.0,
                allocated_path_pressure_drop_Pa=0.0,
                difference_Pa=0.0,
                contributing_balancing_point_ids=(),
                conserved=True,
                status="Old",
            ),
            CommittedBalancingPointRouteConservationRowV1(
                route_id="route-b",
                required_added_pressure_drop_Pa=200.0,
                allocated_path_pressure_drop_Pa=200.0,
                difference_Pa=0.0,
                contributing_balancing_point_ids=("point-b",),
                conserved=True,
                status="Old",
            ),
        ),
        status="Ready",
    )
    snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis="DIRECT",
        committed_point_valve_bases=(
            CommittedPointValveBasisV1(
                balancing_point_id="point-b",
                accepted_kvs_basis=0.50,
                disposition=APPROVED_FOR_PRODUCT_SEARCH,
            ),
        ),
        hydraulic_input_authority=old_hydraulic,
        hydraulic_input_authority_status="Ready",
        point_allocation_authority=old_allocation,
        point_allocation_authority_status="Ready",
    )
    projection = ProportionedPipeResizingHydraulicProjectionV1(
        ready=True,
        sections=(
            _projected_section(
                "section-a", "route-a", total=1000.0
            ),
            _projected_section(
                "section-b", "route-b", total=800.0
            ),
        ),
        routes=(
            _route_projection(
                "route-a",
                "section-a",
                total=1000.0,
                added=0.0,
                controlling=True,
                rank=1,
            ),
            _route_projection(
                "route-b",
                "section-b",
                total=800.0,
                added=200.0,
                controlling=False,
                rank=2,
            ),
        ),
        section_count=2,
        route_count=2,
        controlling_route_id="route-a",
        controlling_target_Pa=1000.0,
        status="Ready",
    )
    point_row = ResizedBalancingPointReconciliationRowV1(
        balancing_point_id="point-b",
        point_scope="route",
        point_role="route_exclusive",
        label="Point B",
        parent_balancing_point_id="",
        anchor_section_id="section-b",
        allocation_route_ids=("route-b",),
        projected_route_ids=("route-b",),
        is_shared=False,
        is_route_exclusive=True,
        point_flow_kg_s=0.10,
        previous_allocated_dp_Pa=200.0,
        previous_resistance_Pa_per_kg_s2=20000.0,
        reconciled_allocated_dp_Pa=200.0,
        reconciled_resistance_Pa_per_kg_s2=20000.0,
        allocation_change_dp_Pa=0.0,
        valve_duty_required=True,
        status="Reconciled",
    )
    reconciliation = ResizedBalancingPointReconciliationV1(
        ready=True,
        point_rows=(point_row,),
        route_rows=(
            ResizedBalancingRouteReconciliationRowV1(
                projected_route_id="route-a",
                allocation_route_id="route-a",
                resized_hydraulic_dp_Pa=1000.0,
                controlling_target_Pa=1000.0,
                required_added_dp_Pa=0.0,
                allocated_path_dp_Pa=0.0,
                residual_Pa=0.0,
                contributing_balancing_point_ids=(),
                conserved=True,
                status="Reconciled",
            ),
            ResizedBalancingRouteReconciliationRowV1(
                projected_route_id="route-b",
                allocation_route_id="route-b",
                resized_hydraulic_dp_Pa=800.0,
                controlling_target_Pa=1000.0,
                required_added_dp_Pa=200.0,
                allocated_path_dp_Pa=200.0,
                residual_Pa=0.0,
                contributing_balancing_point_ids=("point-b",),
                conserved=True,
                status="Reconciled",
            ),
        ),
        point_count=1,
        route_count=2,
        valve_duty_point_count=1,
        status="Ready",
    )
    acceptance = ResolvedProportionedPipeResizingScheduleAcceptanceV1(
        ready=True,
        accepted=True,
        schedule_fingerprint="a" * 64,
        accepted_schedule_fingerprint="a" * 64,
        rows=(
            ResolvedProportionedPipeSectionDNAcceptanceV1(
                section_id="section-a",
                current_dn=22,
                proposed_dn=20,
                accepted_dn=20,
                matches_current_schedule=True,
                status="Accepted",
            ),
            ResolvedProportionedPipeSectionDNAcceptanceV1(
                section_id="section-b",
                current_dn=22,
                proposed_dn=20,
                accepted_dn=20,
                matches_current_schedule=True,
                status="Accepted",
            ),
        ),
        status="Ready",
    )
    material = ProportionedPipeMaterialFamilyIntentV1(
        current_material_key="copper",
        proposed_material_key="mlcp",
    )
    return snapshot, material, acceptance, projection, reconciliation


def main() -> None:
    snapshot, material, acceptance, projection, reconciliation = (
        _fixtures()
    )
    before_snapshot = proportioned_basis_snapshot_to_dict_v1(snapshot)
    before_material = material.to_dict()

    result = build_proportioned_pipe_schedule_commit_rebuild_v1(
        committed_snapshot=snapshot,
        material_intent=material,
        acceptance_resolution=acceptance,
        resized_hydraulics=projection,
        resized_point_reconciliation=reconciliation,
    )
    assert result.ready is True, result.status
    assert result.replacement_snapshot is not None
    replacement = result.replacement_snapshot
    assert replacement is not snapshot
    assert replacement.status == COMMITTED_RESIZED_HYDRAULICS_STATUS_V1
    assert replacement.basis_only_output_ready is False
    assert replacement.committed_point_valve_bases == ()
    assert "fresh manual generic-Kvs review" in (
        replacement.point_valve_basis_status
    )

    authority = replacement.hydraulic_input_authority
    assert authority is not None and authority.ready
    assert {row.material_key for row in authority.sections} == {"mlcp"}
    assert {row.dn for row in authority.sections} == {20}
    assert {
        round(float(row.internal_diameter_m or 0.0), 6)
        for row in authority.sections
    } == {0.016}
    assert {
        round(float(row.material_roughness_m or 0.0), 9)
        for row in authority.sections
    } == {0.000007}
    route_by_id = {row.route_id: row for row in authority.routes}
    assert route_by_id["route-a"].chosen_pressure_drop_Pa == 1000.0
    assert route_by_id["route-a"].controlling is True
    assert route_by_id["route-b"].chosen_pressure_drop_Pa == 800.0
    assert route_by_id["route-b"].required_added_pressure_drop_Pa == 200.0

    allocation = replacement.point_allocation_authority
    assert allocation is not None and allocation.ready
    assert allocation.rows[0].allocated_added_pressure_drop_Pa == 200.0
    assert allocation.rows[0].allocated_resistance_Pa_per_kg_s2 == 20000.0
    assert all(row.conserved for row in allocation.route_conservation)

    route_result = build_committed_basis_route_proportioning_result_v1(
        authority
    )
    assert route_result.ready is True
    point_result = (
        build_committed_point_level_balancing_reconciliation_v1(
            replacement
        )
    )
    assert point_result.ready is False
    assert "missing generic-Kvs bases" in point_result.status

    payload = proportioned_basis_snapshot_to_dict_v1(replacement)
    restored = proportioned_basis_snapshot_from_dict_v1(payload)
    assert restored is not None
    assert restored.status == COMMITTED_RESIZED_HYDRAULICS_STATUS_V1
    assert restored.hydraulic_input_authority is not None
    assert restored.hydraulic_input_authority.sections == authority.sections
    assert restored.point_allocation_authority is not None
    assert restored.point_allocation_authority.rows == allocation.rows

    # The pure builder never mutates any supplied authority or intent.
    assert proportioned_basis_snapshot_to_dict_v1(snapshot) == before_snapshot
    assert material.to_dict() == before_material
    assert acceptance.accepted is True

    stale = build_proportioned_pipe_schedule_commit_rebuild_v1(
        committed_snapshot=snapshot,
        material_intent=material,
        acceptance_resolution=replace(
            acceptance,
            accepted_schedule_fingerprint="b" * 64,
        ),
        resized_hydraulics=projection,
        resized_point_reconciliation=reconciliation,
    )
    assert stale.ready is False
    assert stale.replacement_snapshot is None
    assert "fingerprint" in stale.status

    changed_dn = replace(
        projection.sections[0],
        current_dn=15,
    )
    mismatched = build_proportioned_pipe_schedule_commit_rebuild_v1(
        committed_snapshot=snapshot,
        material_intent=material,
        acceptance_resolution=acceptance,
        resized_hydraulics=replace(
            projection,
            sections=(changed_dn, projection.sections[1]),
        ),
        resized_point_reconciliation=reconciliation,
    )
    assert mismatched.ready is False
    assert mismatched.replacement_snapshot is None
    assert "current DN" in mismatched.status

    print(
        "OK — H-S61-H1B exact accepted schedule transactional hydraulic "
        "rebuild authority passed."
    )


if __name__ == "__main__":
    main()
