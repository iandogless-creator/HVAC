# ======================================================================
# H-S61-H1B — Transactional accepted pipe-schedule hydraulic rebuild
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Any

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    CommittedBalancingPointAllocationAuthorityV1,
    CommittedBalancingPointAllocationRowV1,
    CommittedBalancingPointRouteConservationRowV1,
)
from HVAC.hydronics.proportioning.committed_basis_route_proportioning_result_v1 import (
    build_committed_basis_route_proportioning_result_v1,
)
from HVAC.hydronics.proportioning.committed_basis_section_hydraulic_result_v1 import (
    build_committed_basis_section_hydraulic_result_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
    CommittedProportioningHydraulicSectionV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_material_family_intent_v1 import (
    ProportionedPipeMaterialFamilyIntentV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import (
    ProportionedPipeResizingHydraulicProjectionV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_resizing_schedule_acceptance_intent_v1 import (
    ResolvedProportionedPipeResizingScheduleAcceptanceV1,
)
from HVAC.hydronics.proportioning.resized_balancing_point_reconciliation_v1 import (
    ResizedBalancingPointReconciliationV1,
)


COMMITTED_RESIZED_HYDRAULICS_STATUS_V1 = (
    "COMMITTED_RESIZED_HYDRAULICS"
)
POINT_ALLOCATION_TOLERANCE_PA_V1 = 0.05


@dataclass(frozen=True, slots=True)
class ProportionedPipeScheduleCommitRebuildResultV1:
    """
    Complete immutable replacement candidate for the later explicit commit.

    `replacement_snapshot` is never assigned to ProjectState here.  The
    accepted schedule is not consumed and current/proposed material intent is
    not changed by this pure builder.
    """

    schema: str = (
        "proportioned_pipe_schedule_commit_rebuild_result_v1"
    )
    ready: bool = False
    replacement_snapshot: ProportionedBasisSnapshotV1 | None = None
    committed_material_key: str = ""
    accepted_schedule_fingerprint: str = ""
    section_count: int = 0
    route_count: int = 0
    balancing_point_count: int = 0
    status: str = "Accepted pipe-schedule rebuild not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No ProjectState mutation",
        "No persisted material-intent mutation",
        "No acceptance consumption or clearing",
        "No automatic generic-Kvs reuse or revision",
        "No valve product or setting selection",
        "No pump selection",
        "No commissioning or final balancing",
    )
    note: str = (
        "Pure replacement-snapshot authority only — H-S61-H2 must perform "
        "the later explicit atomic ProjectState commit."
    )


def build_proportioned_pipe_schedule_commit_rebuild_v1(
        *,
        committed_snapshot: ProportionedBasisSnapshotV1 | None,
        material_intent: ProportionedPipeMaterialFamilyIntentV1 | None,
        acceptance_resolution: (
            ResolvedProportionedPipeResizingScheduleAcceptanceV1 | None
        ),
        resized_hydraulics: (
            ProportionedPipeResizingHydraulicProjectionV1 | None
        ),
        resized_point_reconciliation: (
            ResizedBalancingPointReconciliationV1 | None
        ),
) -> ProportionedPipeScheduleCommitRebuildResultV1:
    """
    Build all replacement committed authorities before any state mutation.

    The current committed section and point identities must match the
    projection exactly.  Resized pipe/local-K hydraulics and reconciled point
    allocations are copied into new immutable authorities.  Former committed
    generic-Kvs bases are cleared because their duties are stale after the
    hydraulic schedule changes.
    """
    blockers: list[str] = []

    if not isinstance(committed_snapshot, ProportionedBasisSnapshotV1):
        blockers.append("Committed Proportioned basis snapshot required")
    if not isinstance(
            material_intent,
            ProportionedPipeMaterialFamilyIntentV1,
    ):
        blockers.append(
            "Persisted current/proposed pipe-material-family intent required"
        )
    if not isinstance(
            acceptance_resolution,
            ResolvedProportionedPipeResizingScheduleAcceptanceV1,
    ):
        blockers.append(
            "Resolved exact material/size schedule acceptance required"
        )
    elif not (
            acceptance_resolution.ready
            and acceptance_resolution.accepted
    ):
        blockers.extend(
            tuple(acceptance_resolution.blockers or ())
            or ("Exact material/size schedule acceptance is not ready",)
        )
    elif (
            not _text_v1(acceptance_resolution.schedule_fingerprint)
            or acceptance_resolution.schedule_fingerprint
            != acceptance_resolution.accepted_schedule_fingerprint
    ):
        blockers.append(
            "Accepted schedule fingerprint must exactly match current evidence"
        )
    if not isinstance(
            resized_hydraulics,
            ProportionedPipeResizingHydraulicProjectionV1,
    ):
        blockers.append("H-S61-C resized hydraulic projection required")
    elif not resized_hydraulics.ready:
        blockers.extend(
            tuple(resized_hydraulics.blockers or ())
            or ("H-S61-C resized hydraulic projection is not ready",)
        )
    if not isinstance(
            resized_point_reconciliation,
            ResizedBalancingPointReconciliationV1,
    ):
        blockers.append("H-S61-D resized point reconciliation required")
    elif not resized_point_reconciliation.ready:
        blockers.extend(
            tuple(resized_point_reconciliation.blockers or ())
            or ("H-S61-D resized point reconciliation is not ready",)
        )

    if blockers:
        return _blocked_v1(*blockers)
    assert committed_snapshot is not None
    assert material_intent is not None
    assert acceptance_resolution is not None
    assert resized_hydraulics is not None
    assert resized_point_reconciliation is not None

    old_hydraulic = committed_snapshot.hydraulic_input_authority
    old_allocation = committed_snapshot.point_allocation_authority
    if not isinstance(
            old_hydraulic,
            CommittedProportioningHydraulicInputAuthorityV1,
    ) or not old_hydraulic.ready:
        blockers.append(
            "Ready committed hydraulic-input authority required"
        )
    if not isinstance(
            old_allocation,
            CommittedBalancingPointAllocationAuthorityV1,
    ) or not old_allocation.ready:
        blockers.append(
            "Ready committed balancing-point allocation authority required"
        )
    if blockers:
        return _blocked_v1(*blockers)
    assert old_hydraulic is not None
    assert old_allocation is not None

    try:
        new_hydraulic = _build_hydraulic_authority_v1(
            old_authority=old_hydraulic,
            material_intent=material_intent,
            acceptance_resolution=acceptance_resolution,
            projection=resized_hydraulics,
        )
        new_allocation = _build_point_allocation_authority_v1(
            old_authority=old_allocation,
            projection=resized_hydraulics,
            reconciliation=resized_point_reconciliation,
        )
        replacement_snapshot = replace(
            committed_snapshot,
            status=COMMITTED_RESIZED_HYDRAULICS_STATUS_V1,
            committed_point_valve_bases=(),
            point_valve_basis_status=(
                "Cleared — resized point duties require fresh manual "
                "generic-Kvs review"
            ),
            hydraulic_input_authority=new_hydraulic,
            hydraulic_input_authority_status=new_hydraulic.status,
            point_allocation_authority=new_allocation,
            point_allocation_authority_status=new_allocation.status,
            basis_only_output_ready=False,
            basis_only_output_status=(
                "Superseded — committed resized hydraulic authority is "
                "present; generic-Kvs duties require fresh review"
            ),
            note=(
                "Committed accepted material/size schedule with recalculated "
                "section and route hydraulics and reconciled point allocations "
                "— no pump, valve product, valve setting or final balancing."
            ),
        )
        route_result = (
            build_committed_basis_route_proportioning_result_v1(
                new_hydraulic
            )
        )
        if not route_result.ready:
            raise ValueError(
                "Replacement committed route result is not ready: "
                + (
                    "; ".join(route_result.blockers)
                    or route_result.status
                )
            )
        section_result = build_committed_basis_section_hydraulic_result_v1(
            replacement_snapshot
        )
        if not section_result.ready:
            raise ValueError(
                "Replacement committed section result is not ready: "
                + (
                    "; ".join(section_result.blockers)
                    or section_result.status
                )
            )
    except (TypeError, ValueError) as exc:
        return _blocked_v1(str(exc))

    return ProportionedPipeScheduleCommitRebuildResultV1(
        ready=True,
        replacement_snapshot=replacement_snapshot,
        committed_material_key=material_intent.proposed_material_key,
        accepted_schedule_fingerprint=(
            acceptance_resolution.schedule_fingerprint
        ),
        section_count=len(new_hydraulic.sections),
        route_count=len(new_hydraulic.routes),
        balancing_point_count=len(new_allocation.rows),
        status=(
            "Ready — exact accepted material/size schedule rebuilt into one "
            "immutable committed-snapshot candidate"
        ),
        blockers=(),
    )


def _build_hydraulic_authority_v1(
        *,
        old_authority: CommittedProportioningHydraulicInputAuthorityV1,
        material_intent: ProportionedPipeMaterialFamilyIntentV1,
        acceptance_resolution: (
            ResolvedProportionedPipeResizingScheduleAcceptanceV1
        ),
        projection: ProportionedPipeResizingHydraulicProjectionV1,
) -> CommittedProportioningHydraulicInputAuthorityV1:
    old_sections = _unique_by_id_v1(
        old_authority.sections,
        attribute="section_id",
        label="committed section",
    )
    projected_sections = _unique_by_id_v1(
        projection.sections,
        attribute="section_id",
        label="projected section",
    )
    accepted_sections = _unique_by_id_v1(
        acceptance_resolution.rows,
        attribute="section_id",
        label="accepted section",
    )
    if set(old_sections) != set(projected_sections):
        raise ValueError(
            "Projected section identities do not match committed sections"
        )
    if set(accepted_sections) != set(projected_sections):
        raise ValueError(
            "Accepted section identities do not match projected sections"
        )

    current_key = material_intent.current_material_key
    proposed_key = material_intent.proposed_material_key
    proposed_material = get_material(proposed_key)
    if proposed_material is None:
        raise ValueError(
            f"Proposed material absent from library: {proposed_key}"
        )
    roughness_m = float(proposed_material.roughness_mm) / 1000.0

    sections: list[CommittedProportioningHydraulicSectionV1] = []
    for section_id in sorted(projected_sections):
        old = old_sections[section_id]
        projected = projected_sections[section_id]
        accepted = accepted_sections[section_id]
        _validate_stable_section_v1(old, projected)
        if _text_v1(old.material_key).lower() != current_key:
            raise ValueError(
                f"{section_id}: committed current material is stale"
            )
        if _text_v1(projected.current_material_key).lower() != current_key:
            raise ValueError(
                f"{section_id}: projected current material is stale"
            )
        if _text_v1(projected.projected_material_key).lower() != proposed_key:
            raise ValueError(
                f"{section_id}: projected proposed material is stale"
            )
        if (
                int(accepted.current_dn) != int(projected.current_dn)
                or int(accepted.proposed_dn) != int(projected.projected_dn)
                or not bool(accepted.matches_current_schedule)
        ):
            raise ValueError(
                f"{section_id}: accepted DN evidence does not exactly match"
            )
        size = proposed_material.sizes.get(int(projected.projected_dn))
        if size is None:
            raise ValueError(
                f"{section_id}: proposed material/size absent from library"
            )
        expected_bore = float(size.id_mm) / 1000.0
        if not math.isclose(
                float(projected.internal_diameter_m),
                expected_bore,
                rel_tol=0.0,
                abs_tol=1.0e-12,
        ):
            raise ValueError(
                f"{section_id}: projected bore does not match material library"
            )
        sections.append(
            CommittedProportioningHydraulicSectionV1(
                section_id=section_id,
                section_scope=_required_text_v1(
                    projected.section_scope,
                    f"{section_id}: section scope required",
                ),
                route_ids=tuple(projected.route_ids),
                order=int(projected.order),
                from_label=_text_v1(projected.from_label),
                to_label=_text_v1(projected.to_label),
                carried_flow_kg_s=_positive_v1(
                    projected.carried_flow_kg_s,
                    f"{section_id}: positive carried flow required",
                ),
                pipe_size_label=_required_text_v1(
                    projected.projected_pipe_size_label,
                    f"{section_id}: projected pipe-size label required",
                ),
                dn=_positive_int_v1(
                    projected.projected_dn,
                    f"{section_id}: positive projected DN required",
                ),
                length_m=_positive_v1(
                    projected.length_m,
                    f"{section_id}: positive length required",
                ),
                k_total=_non_negative_v1(
                    projected.k_total,
                    f"{section_id}: non-negative Local K required",
                ),
                velocity_m_s=_positive_v1(
                    projected.velocity_m_s,
                    f"{section_id}: positive velocity required",
                ),
                reynolds_number=_positive_v1(
                    projected.reynolds_number,
                    f"{section_id}: positive Reynolds number required",
                ),
                friction_factor=_positive_v1(
                    projected.friction_factor,
                    f"{section_id}: positive friction factor required",
                ),
                friction_method=_required_text_v1(
                    projected.friction_method,
                    f"{section_id}: friction method required",
                ),
                colebrook_iteration_count=_non_negative_int_v1(
                    projected.colebrook_iteration_count,
                    f"{section_id}: non-negative iteration count required",
                ),
                colebrook_converged=bool(
                    projected.colebrook_converged
                ),
                pressure_gradient_Pa_per_m=_positive_v1(
                    projected.pressure_gradient_Pa_per_m,
                    f"{section_id}: positive pressure gradient required",
                ),
                straight_pressure_drop_Pa=_positive_v1(
                    projected.straight_pressure_drop_Pa,
                    f"{section_id}: positive straight pressure drop required",
                ),
                local_pressure_drop_Pa=_non_negative_v1(
                    projected.local_pressure_drop_Pa,
                    f"{section_id}: non-negative local pressure drop required",
                ),
                section_total_pressure_drop_Pa=_positive_v1(
                    projected.section_total_pressure_drop_Pa,
                    f"{section_id}: positive total pressure drop required",
                ),
                material_key=proposed_key,
                material_label=_text_v1(proposed_material.name),
                internal_diameter_m=expected_bore,
                material_roughness_m=roughness_m,
            )
        )
        if not bool(projected.colebrook_converged):
            raise ValueError(
                f"{section_id}: converged projected Colebrook evidence required"
            )

    old_routes = _unique_by_id_v1(
        old_authority.routes,
        attribute="route_id",
        label="committed route",
    )
    projected_routes = _unique_by_id_v1(
        projection.routes,
        attribute="route_id",
        label="projected route",
    )
    if set(old_routes) != set(projected_routes):
        raise ValueError(
            "Projected route identities do not match committed routes"
        )
    section_tuple = tuple(sorted(
        sections,
        key=lambda row: (row.order, row.section_id),
    ))
    routes: list[CommittedProportioningHydraulicRouteV1] = []
    for route_id in sorted(projected_routes):
        old = old_routes[route_id]
        projected = projected_routes[route_id]
        route_sections = tuple(
            row for row in section_tuple if route_id in row.route_ids
        )
        if not route_sections:
            raise ValueError(
                f"{route_id}: projected route has no committed sections"
            )
        expected_ids = tuple(
            row.section_id for row in route_sections
        )
        if set(expected_ids) != set(projected.section_ids):
            raise ValueError(
                f"{route_id}: projected route section membership is stale"
            )
        total = sum(
            row.section_total_pressure_drop_Pa for row in route_sections
        )
        if not math.isclose(
                total,
                float(projected.route_pressure_drop_total_Pa),
                rel_tol=0.0,
                abs_tol=1.0e-6,
        ):
            raise ValueError(
                f"{route_id}: projected route total does not equal sections"
            )
        required_added = _non_negative_v1(
            projected.required_added_dp_Pa,
            f"{route_id}: non-negative route addition required",
        )
        flow_basis = max(row.carried_flow_kg_s for row in route_sections)
        resistance = (
            required_added / (flow_basis ** 2)
            if required_added > 0.0
            else 0.0
        )
        routes.append(
            CommittedProportioningHydraulicRouteV1(
                route_id=route_id,
                route_label=(
                    _text_v1(old.route_label) or route_id
                ),
                basis=_required_text_v1(
                    old.basis,
                    f"{route_id}: committed route basis required",
                ),
                chosen_pressure_drop_Pa=_positive_v1(
                    projected.route_pressure_drop_total_Pa,
                    f"{route_id}: positive resized route pressure required",
                ),
                controlling=bool(projected.is_controlling),
                required_added_pressure_drop_Pa=required_added,
                preliminary_resistance_Pa_per_kg_s2=resistance,
                common_main_pressure_drop_Pa=None,
                leg_entry_pressure_drop_Pa=None,
                physical_main_entry_pressure_drop_Pa=None,
            )
        )

    controlling = tuple(row for row in routes if row.controlling)
    if len(controlling) != 1:
        raise ValueError(
            "Exactly one resized controlling route is required"
        )
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=section_tuple,
        routes=tuple(routes),
        status=(
            "Ready — accepted material/size schedule and recalculated "
            "hydraulic-input authority rebuilt"
        ),
        blockers=(),
        note=(
            "Frozen accepted material, pipe size, actual bore, roughness, "
            "flow, length, Local-K and Colebrook evidence after resize."
        ),
    )


def _build_point_allocation_authority_v1(
        *,
        old_authority: CommittedBalancingPointAllocationAuthorityV1,
        projection: ProportionedPipeResizingHydraulicProjectionV1,
        reconciliation: ResizedBalancingPointReconciliationV1,
) -> CommittedBalancingPointAllocationAuthorityV1:
    tolerance = _non_negative_v1(
        old_authority.tolerance_Pa,
        "Non-negative committed point-allocation tolerance required",
    )
    old_points = _unique_by_id_v1(
        old_authority.rows,
        attribute="balancing_point_id",
        label="committed balancing point",
    )
    new_points = _unique_by_id_v1(
        reconciliation.point_rows,
        attribute="balancing_point_id",
        label="resized balancing point",
    )
    if set(old_points) != set(new_points):
        raise ValueError(
            "Resized balancing-point identities do not match committed points"
        )

    rows: list[CommittedBalancingPointAllocationRowV1] = []
    for point_id in sorted(new_points):
        old = old_points[point_id]
        current = new_points[point_id]
        stable_pairs = (
            ("point_scope", old.point_scope, current.point_scope),
            ("point_role", old.point_role, current.point_role),
            ("parent point", old.parent_balancing_point_id,
             current.parent_balancing_point_id),
            ("anchor section", old.anchor_section_id,
             current.anchor_section_id),
        )
        for label, old_value, new_value in stable_pairs:
            if _text_v1(old_value) != _text_v1(new_value):
                raise ValueError(
                    f"{point_id}: stable {label} identity changed"
                )
        if set(old.downstream_route_ids) != set(
                current.allocation_route_ids
        ):
            raise ValueError(
                f"{point_id}: allocation route identity changed"
            )
        for route_id in tuple(current.projected_route_ids):
            if not _matches_projected_route_v1(
                    route_id,
                    tuple(row.route_id for row in projection.routes),
            ):
                raise ValueError(
                    f"{point_id}: projected route identity is unresolved"
                )
        allocated = _non_negative_v1(
            current.reconciled_allocated_dp_Pa,
            f"{point_id}: non-negative reconciled allocation required",
        )
        resistance = _non_negative_v1(
            current.reconciled_resistance_Pa_per_kg_s2,
            f"{point_id}: non-negative reconciled resistance required",
        )
        flow = _positive_v1(
            current.point_flow_kg_s,
            f"{point_id}: positive point flow required",
        )
        if not math.isclose(
                resistance,
                allocated / (flow ** 2),
                rel_tol=0.0,
                abs_tol=1.0e-6,
        ):
            raise ValueError(
                f"{point_id}: reconciled resistance is inconsistent"
            )
        rows.append(
            CommittedBalancingPointAllocationRowV1(
                balancing_point_id=point_id,
                point_scope=_text_v1(current.point_scope),
                point_role=_text_v1(current.point_role),
                label=_text_v1(current.label) or point_id,
                parent_balancing_point_id=_text_v1(
                    current.parent_balancing_point_id
                ),
                anchor_section_id=_text_v1(current.anchor_section_id),
                downstream_route_ids=tuple(current.allocation_route_ids),
                is_shared=bool(current.is_shared),
                is_route_exclusive=bool(current.is_route_exclusive),
                point_flow_kg_s=flow,
                allocated_added_pressure_drop_Pa=allocated,
                allocated_resistance_Pa_per_kg_s2=resistance,
                status=(
                    "Committed — resized hydraulic duty reconciled; "
                    "generic-Kvs review required"
                ),
            )
        )

    old_conservation = _unique_by_id_v1(
        old_authority.route_conservation,
        attribute="route_id",
        label="committed allocation route",
    )
    route_rows = _unique_by_id_v1(
        reconciliation.route_rows,
        attribute="allocation_route_id",
        label="resized allocation route",
    )
    if set(old_conservation) != set(route_rows):
        raise ValueError(
            "Resized allocation-route identities do not match committed routes"
        )
    projected_ids = tuple(row.route_id for row in projection.routes)
    projected_seen: set[str] = set()
    conservation: list[
        CommittedBalancingPointRouteConservationRowV1
    ] = []
    for allocation_id in sorted(route_rows):
        current = route_rows[allocation_id]
        projected_id = _text_v1(current.projected_route_id)
        if projected_id in projected_seen:
            raise ValueError(
                "Duplicate resized projected-route reconciliation identity"
            )
        projected_seen.add(projected_id)
        if projected_id not in projected_ids:
            raise ValueError(
                f"{allocation_id}: projected route identity is unresolved"
            )
        required = _non_negative_v1(
            current.required_added_dp_Pa,
            f"{allocation_id}: non-negative route requirement required",
        )
        allocated = _non_negative_v1(
            current.allocated_path_dp_Pa,
            f"{allocation_id}: non-negative allocated path required",
        )
        residual = _finite_v1(
            current.residual_Pa,
            f"{allocation_id}: finite conservation residual required",
        )
        if (
                not bool(current.conserved)
                or abs(required - allocated) > tolerance
                or abs(residual) > tolerance
        ):
            raise ValueError(
                f"{allocation_id}: resized point allocation is not conserved"
            )
        conservation.append(
            CommittedBalancingPointRouteConservationRowV1(
                route_id=allocation_id,
                required_added_pressure_drop_Pa=required,
                allocated_path_pressure_drop_Pa=allocated,
                difference_Pa=(
                    0.0 if abs(residual) <= tolerance else residual
                ),
                contributing_balancing_point_ids=tuple(
                    current.contributing_balancing_point_ids
                ),
                conserved=True,
                status=(
                    "Committed — resized point allocations conserve route duty"
                ),
            )
        )
    if set(projected_seen) != set(projected_ids):
        raise ValueError(
            "Every resized projected route requires conservation evidence"
        )
    return CommittedBalancingPointAllocationAuthorityV1(
        ready=True,
        tolerance_Pa=tolerance,
        rows=tuple(rows),
        route_conservation=tuple(conservation),
        status=(
            "Ready — resized balancing-point allocations and route "
            "conservation rebuilt"
        ),
        blockers=(),
        note=(
            "Frozen resized point duties only — former generic-Kvs bases "
            "are deliberately not reused."
        ),
    )


def _validate_stable_section_v1(old: Any, projected: Any) -> None:
    section_id = _text_v1(old.section_id)
    exact_pairs = (
        ("section scope", old.section_scope, projected.section_scope),
        ("route membership", tuple(old.route_ids), tuple(projected.route_ids)),
        ("order", int(old.order), int(projected.order)),
        ("from label", old.from_label, projected.from_label),
        ("to label", old.to_label, projected.to_label),
        ("current DN", int(old.dn), int(projected.current_dn)),
    )
    for label, old_value, new_value in exact_pairs:
        if old_value != new_value:
            raise ValueError(
                f"{section_id}: stable {label} evidence changed"
            )
    numeric_pairs = (
        ("flow", old.carried_flow_kg_s, projected.carried_flow_kg_s),
        ("length", old.length_m, projected.length_m),
        ("Local K", old.k_total, projected.k_total),
        (
            "current bore",
            old.internal_diameter_m,
            projected.current_internal_diameter_m,
        ),
    )
    for label, old_value, new_value in numeric_pairs:
        if old_value is None or not math.isclose(
                float(old_value),
                float(new_value),
                rel_tol=0.0,
                abs_tol=1.0e-12,
        ):
            raise ValueError(
                f"{section_id}: stable {label} evidence changed"
            )


def _unique_by_id_v1(
        values: Any,
        *,
        attribute: str,
        label: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in tuple(values or ()):
        identity = _text_v1(getattr(row, attribute, ""))
        if not identity:
            raise ValueError(f"Every {label} requires stable identity")
        if identity in result:
            raise ValueError(f"Duplicate {label} identity: {identity}")
        result[identity] = row
    if not result:
        raise ValueError(f"At least one {label} row required")
    return result


def _matches_projected_route_v1(
        value: object,
        projected_ids: tuple[str, ...],
) -> bool:
    identity = _text_v1(value)
    if identity in projected_ids:
        return True
    suffix = identity.rsplit(":", 1)[-1]
    matches = tuple(
        route_id
        for route_id in projected_ids
        if route_id.rsplit(":", 1)[-1] == suffix
    )
    return len(matches) == 1


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _required_text_v1(value: object, error: str) -> str:
    text = _text_v1(value)
    if not text:
        raise ValueError(error)
    return text


def _finite_v1(value: object, error: str) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError(error)
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(error) from None
    if not math.isfinite(number):
        raise ValueError(error)
    return number


def _positive_v1(value: object, error: str) -> float:
    number = _finite_v1(value, error)
    if number <= 0.0:
        raise ValueError(error)
    return number


def _non_negative_v1(value: object, error: str) -> float:
    number = _finite_v1(value, error)
    if number < 0.0:
        raise ValueError(error)
    return number


def _positive_int_v1(value: object, error: str) -> int:
    number = int(_finite_v1(value, error))
    if number <= 0:
        raise ValueError(error)
    return number


def _non_negative_int_v1(value: object, error: str) -> int:
    number = int(_finite_v1(value, error))
    if number < 0:
        raise ValueError(error)
    return number


def _blocked_v1(
        *blockers: str,
) -> ProportionedPipeScheduleCommitRebuildResultV1:
    clean = tuple(dict.fromkeys(
        _text_v1(value) for value in blockers if _text_v1(value)
    ))
    return ProportionedPipeScheduleCommitRebuildResultV1(
        ready=False,
        replacement_snapshot=None,
        blockers=clean,
        status=(
            "Blocked — " + "; ".join(clean)
            if clean
            else "Blocked — accepted pipe-schedule rebuild is not ready"
        ),
    )
