from __future__ import annotations

from dataclasses import replace
import inspect

from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import (
    ProportionedPipeResizingHydraulicProjectionV1,
    ProportionedResizedRouteHydraulicProjectionV1,
    ProportionedResizedSectionHydraulicProjectionV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_resizing_schedule_acceptance_intent_v1 import (
    ProportionedPipeResizingScheduleAcceptanceIntentV1,
    build_proportioned_pipe_resizing_schedule_fingerprint_v1,
    proportioned_pipe_resizing_schedule_acceptance_intent_from_dict_v1,
    proportioned_pipe_resizing_schedule_acceptance_intent_to_dict_v1,
    resolve_proportioned_pipe_resizing_schedule_acceptance_v1,
)
from HVAC.hydronics.proportioning.resized_balancing_point_reconciliation_v1 import (
    ResizedBalancingPointReconciliationRowV1,
    ResizedBalancingPointReconciliationV1,
    ResizedBalancingRouteReconciliationRowV1,
)
from HVAC.project.project_state import ProjectState


def _section(
        section_id: str,
        *,
        order: int,
        current_dn: int,
        projected_dn: int,
        total_dp: float,
) -> ProportionedResizedSectionHydraulicProjectionV1:
    return ProportionedResizedSectionHydraulicProjectionV1(
        section_id=section_id,
        section_scope="route_section",
        route_ids=("route-a",),
        order=order,
        from_label=f"{section_id}-from",
        to_label=f"{section_id}-to",
        carried_flow_kg_s=0.15,
        length_m=5.0,
        k_total=2.0,
        current_dn=current_dn,
        current_pipe_size_label=f"{current_dn} mm",
        projected_dn=projected_dn,
        projected_pipe_size_label=f"{projected_dn} mm",
        recommendation="INCREASE",
        internal_diameter_m=0.020,
        velocity_m_s=0.48,
        maximum_velocity_m_s=1.0,
        velocity_within_limit=True,
        pressure_gradient_Pa_per_m=180.0,
        maximum_pressure_gradient_Pa_per_m=200.0,
        pressure_gradient_within_limit=True,
        straight_pressure_drop_Pa=900.0,
        local_pressure_drop_Pa=total_dp - 900.0,
        section_total_pressure_drop_Pa=total_dp,
        reynolds_number=9500.0,
        friction_factor=0.032,
        friction_method="colebrook",
        colebrook_iteration_count=6,
        colebrook_converged=True,
        status="Projected section",
        current_material_key="copper",
        current_material_label="Copper EN1057",
        current_internal_diameter_m=0.020,
        projected_material_key="copper",
        projected_material_label="Copper EN1057",
    )


def _projection() -> ProportionedPipeResizingHydraulicProjectionV1:
    sections = (
        _section(
            "section-b",
            order=2,
            current_dn=15,
            projected_dn=22,
            total_dp=1071.0,
        ),
        _section(
            "section-a",
            order=1,
            current_dn=22,
            projected_dn=28,
            total_dp=79.0,
        ),
    )
    return ProportionedPipeResizingHydraulicProjectionV1(
        ready=True,
        sections=sections,
        routes=(
            ProportionedResizedRouteHydraulicProjectionV1(
                route_id="route-a",
                section_ids=("section-a", "section-b"),
                section_count=2,
                straight_pressure_drop_total_Pa=979.0,
                local_pressure_drop_total_Pa=171.0,
                route_pressure_drop_total_Pa=1150.0,
                controlling_target_Pa=1200.0,
                required_added_dp_Pa=50.0,
                rank=1,
                is_controlling=True,
                status="Projected route",
            ),
        ),
        section_count=2,
        route_count=1,
        controlling_route_id="route-a",
        controlling_target_Pa=1200.0,
        status="Ready",
    )


def _reconciliation() -> ResizedBalancingPointReconciliationV1:
    return ResizedBalancingPointReconciliationV1(
        ready=True,
        point_rows=(
            ResizedBalancingPointReconciliationRowV1(
                balancing_point_id="point-a",
                point_scope="subleg",
                point_role="route_exclusive",
                label="Point A",
                parent_balancing_point_id="",
                anchor_section_id="section-b",
                allocation_route_ids=("route-a",),
                projected_route_ids=("route-a",),
                is_shared=False,
                is_route_exclusive=True,
                point_flow_kg_s=0.15,
                previous_allocated_dp_Pa=20.0,
                previous_resistance_Pa_per_kg_s2=888.9,
                reconciled_allocated_dp_Pa=50.0,
                reconciled_resistance_Pa_per_kg_s2=2222.2,
                allocation_change_dp_Pa=30.0,
                valve_duty_required=True,
                status="Reconciled point",
            ),
        ),
        route_rows=(
            ResizedBalancingRouteReconciliationRowV1(
                projected_route_id="route-a",
                allocation_route_id="leg-001:route-a",
                resized_hydraulic_dp_Pa=1150.0,
                controlling_target_Pa=1200.0,
                required_added_dp_Pa=50.0,
                allocated_path_dp_Pa=50.0,
                residual_Pa=-0.0,
                contributing_balancing_point_ids=("point-a",),
                conserved=True,
                status="Conserved",
            ),
        ),
        point_count=1,
        route_count=1,
        valve_duty_point_count=1,
        status="Ready",
    )


def main() -> None:
    projection = _projection()
    reconciliation = _reconciliation()

    fingerprint = (
        build_proportioned_pipe_resizing_schedule_fingerprint_v1(
            resized_hydraulics=projection,
            resized_point_reconciliation=reconciliation,
        )
    )
    assert len(fingerprint) == 64
    assert fingerprint == (
        build_proportioned_pipe_resizing_schedule_fingerprint_v1(
            resized_hydraulics=replace(
                projection,
                sections=tuple(reversed(projection.sections)),
            ),
            resized_point_reconciliation=reconciliation,
        )
    )

    pending = resolve_proportioned_pipe_resizing_schedule_acceptance_v1(
        None,
        resized_hydraulics=projection,
        resized_point_reconciliation=reconciliation,
    )
    assert pending.ready is False
    assert pending.accepted is False
    assert "manual proposed material/size schedule acceptance required" in (
        pending.status.lower()
    )

    intent = ProportionedPipeResizingScheduleAcceptanceIntentV1()
    accepted = intent.accept_current_schedule(
        resized_hydraulics=projection,
        resized_point_reconciliation=reconciliation,
    )
    assert accepted.schedule_fingerprint == fingerprint
    assert [row.section_id for row in accepted.sections] == [
        "section-a",
        "section-b",
    ]
    assert accepted.sections[0].current_dn == 22
    assert accepted.sections[0].accepted_dn == 28
    assert accepted.current_material_key == "copper"
    assert accepted.accepted_material_key == "copper"

    resolved = resolve_proportioned_pipe_resizing_schedule_acceptance_v1(
        intent,
        resized_hydraulics=projection,
        resized_point_reconciliation=reconciliation,
    )
    assert resolved.ready is True, resolved.status
    assert resolved.accepted is True
    assert all(row.matches_current_schedule for row in resolved.rows)

    payload = (
        proportioned_pipe_resizing_schedule_acceptance_intent_to_dict_v1(
            intent
        )
    )
    restored = (
        proportioned_pipe_resizing_schedule_acceptance_intent_from_dict_v1(
            payload
        )
    )
    assert restored.accepted_schedule == accepted

    project = ProjectState(project_id="hs61f", name="H-S61-F")
    project.hydronic_proportioned_pipe_resizing_schedule_acceptance_intent = (
        intent
    )
    project_payload = project.to_dict()
    raw = project_payload[
        "hydronic_proportioned_pipe_resizing_schedule_acceptance_intent"
    ]
    assert raw["accepted_schedule"]["schedule_fingerprint"] == fingerprint
    assert raw["accepted_schedule"]["current_material_key"] == "copper"
    assert raw["accepted_schedule"]["accepted_material_key"] == "copper"
    project_restored = ProjectState.from_dict(project_payload)
    assert (
        project_restored
        .hydronic_proportioned_pipe_resizing_schedule_acceptance_intent
        .accepted_schedule
        == accepted
    )
    blank = ProjectState.from_dict(
        ProjectState(project_id="blank", name="Blank").to_dict()
    )
    assert (
        blank
        .hydronic_proportioned_pipe_resizing_schedule_acceptance_intent
        is None
    )

    changed_section = replace(
        projection.sections[0],
        projected_dn=28,
        projected_pipe_size_label="28 mm",
    )
    changed_projection = replace(
        projection,
        sections=(changed_section, projection.sections[1]),
    )
    stale_dn = resolve_proportioned_pipe_resizing_schedule_acceptance_v1(
        intent,
        resized_hydraulics=changed_projection,
        resized_point_reconciliation=reconciliation,
    )
    assert stale_dn.ready is False
    assert "fingerprint does not match" in stale_dn.status

    changed_material_sections = (
        replace(
            projection.sections[0],
            projected_material_key="mlcp",
            projected_material_label="MLCP",
            projected_dn=20,
            projected_pipe_size_label="20×2 mm",
            internal_diameter_m=0.016,
        ),
        replace(
            projection.sections[1],
            projected_material_key="mlcp",
            projected_material_label="MLCP",
            projected_dn=26,
            projected_pipe_size_label="26×3 mm",
            internal_diameter_m=0.020,
        ),
    )
    stale_material = resolve_proportioned_pipe_resizing_schedule_acceptance_v1(
        intent,
        resized_hydraulics=replace(
            projection,
            sections=changed_material_sections,
        ),
        resized_point_reconciliation=reconciliation,
    )
    assert stale_material.ready is False
    assert "fingerprint does not match" in stale_material.status

    changed_loss = replace(
        projection.sections[0],
        local_pressure_drop_Pa=172.0,
        section_total_pressure_drop_Pa=1072.0,
    )
    stale_loss = resolve_proportioned_pipe_resizing_schedule_acceptance_v1(
        intent,
        resized_hydraulics=replace(
            projection,
            sections=(changed_loss, projection.sections[1]),
        ),
        resized_point_reconciliation=reconciliation,
    )
    assert stale_loss.ready is False

    changed_point = replace(
        reconciliation.point_rows[0],
        reconciled_allocated_dp_Pa=51.0,
    )
    stale_point = resolve_proportioned_pipe_resizing_schedule_acceptance_v1(
        intent,
        resized_hydraulics=projection,
        resized_point_reconciliation=replace(
            reconciliation,
            point_rows=(changed_point,),
        ),
    )
    assert stale_point.ready is False

    malformed = (
        proportioned_pipe_resizing_schedule_acceptance_intent_from_dict_v1(
            {
                "accepted_schedule": {
                    "schedule_fingerprint": fingerprint,
                    "sections": [
                        {
                            "section_id": "duplicate",
                            "current_dn": 15,
                            "accepted_dn": 22,
                        },
                        {
                            "section_id": "duplicate",
                            "current_dn": 15,
                            "accepted_dn": 28,
                        },
                    ],
                }
            }
        )
    )
    assert malformed.accepted_schedule is None

    assert intent.clear_acceptance() is True
    assert intent.clear_acceptance() is False

    blocked_projection = replace(
        projection,
        ready=False,
        blockers=("No sizing authority",),
    )
    try:
        intent.accept_current_schedule(
            resized_hydraulics=blocked_projection,
            resized_point_reconciliation=reconciliation,
        )
    except ValueError as exc:
        assert "H-S61-C" in str(exc)
    else:
        raise AssertionError("Blocked H-S61-C evidence was accepted")

    source = inspect.getsource(
        ProportionedPipeResizingScheduleAcceptanceIntentV1
    )
    assert "accepted_schedule" in source
    assert "No committed DN replacement" in resolved.exclusions
    assert "No ProjectState pipe-size mutation" in resolved.exclusions

    print(
        "OK — H-S61-F manual proposed DN schedule acceptance "
        "authority passed."
    )


if __name__ == "__main__":
    main()
