from __future__ import annotations

import inspect

from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import (
    build_proportioned_pipe_resizing_hydraulic_projection_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_size_candidate_evaluation_v1 import (
    build_proportioned_pipe_size_candidate_evaluation_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_sizing_authority_v1 import (
    ProportionedPipeSizingAuthorityV1,
    ProportionedPipeSizingCandidateV1,
    ProportionedPipeSizingCriteriaV1,
    ProportionedPipeSizingSectionAuthorityV1,
)


def _candidates() -> tuple[ProportionedPipeSizingCandidateV1, ...]:
    dimensions = (
        (10, 0.012, 0.010),
        (15, 0.015, 0.013),
        (22, 0.022, 0.020),
        (28, 0.028, 0.026),
        (35, 0.035, 0.032),
    )
    return tuple(
        ProportionedPipeSizingCandidateV1(
            material_key="copper",
            material_label="Copper EN1057",
            dn=dn,
            pipe_size_label=f"{dn} mm",
            outside_diameter_m=od,
            internal_diameter_m=internal,
            roughness_m=0.0000015,
        )
        for dn, od, internal in dimensions
    )


def _section(
        *,
        section_id: str,
        route_ids: tuple[str, ...],
        order: int,
        flow: float,
        length: float,
        k_total: float,
        current_dn: int,
) -> ProportionedPipeSizingSectionAuthorityV1:
    return ProportionedPipeSizingSectionAuthorityV1(
        section_id=section_id,
        section_scope="route_section",
        route_ids=route_ids,
        order=order,
        from_label=f"{section_id}-from",
        to_label=f"{section_id}-to",
        carried_flow_kg_s=flow,
        length_m=length,
        k_total=k_total,
        current_dn=current_dn,
        current_pipe_size_label=f"{current_dn} mm",
        current_velocity_m_s=0.5,
        current_pressure_gradient_Pa_per_m=100.0,
        effective_max_velocity_m_s=1.0,
        max_velocity_source="Environment default",
        effective_max_pressure_gradient_Pa_per_m=200.0,
        max_pressure_gradient_source="Accepted Proportioned criterion",
        current_dn_in_candidate_family=True,
        current_velocity_within_limit=True,
        current_pressure_gradient_within_limit=True,
        status="Ready — committed section sizing authority",
    )


def _authority() -> ProportionedPipeSizingAuthorityV1:
    criteria = ProportionedPipeSizingCriteriaV1(
        material_key="copper",
        material_source="Committed section material",
        default_max_velocity_m_s=1.0,
        max_velocity_source="Environment / local override",
        max_pressure_gradient_Pa_per_m=200.0,
        max_pressure_gradient_source="Accepted Proportioned criterion",
        minimum_dn=10,
        maximum_dn=35,
        density_kg_m3=998.0,
        dynamic_viscosity_Pa_s=0.001,
        friction_method="colebrook",
        colebrook_tolerance=1.0e-6,
        colebrook_max_iterations=100,
    )
    sections = (
        _section(
            section_id="shared",
            route_ids=("route-a", "route-b"),
            order=1,
            flow=0.200,
            length=10.0,
            k_total=1.5,
            current_dn=15,
        ),
        _section(
            section_id="route-a-only",
            route_ids=("route-a",),
            order=2,
            flow=0.150,
            length=5.0,
            k_total=3.0,
            current_dn=15,
        ),
        _section(
            section_id="route-b-only",
            route_ids=("route-b",),
            order=3,
            flow=0.020,
            length=6.0,
            k_total=2.0,
            current_dn=22,
        ),
    )
    return ProportionedPipeSizingAuthorityV1(
        ready=True,
        criteria=criteria,
        candidates=_candidates(),
        sections=sections,
        section_count=len(sections),
        status="Ready — H-S61-A authority",
        blockers=(),
    )


def main() -> None:
    authority = _authority()
    recommendations = (
        build_proportioned_pipe_size_candidate_evaluation_v1(authority)
    )
    assert recommendations.ready is True

    before_authority = repr(authority)
    before_recommendations = repr(recommendations)

    result = build_proportioned_pipe_resizing_hydraulic_projection_v1(
        authority=authority,
        candidate_evaluation=recommendations,
    )
    repeated = build_proportioned_pipe_resizing_hydraulic_projection_v1(
        authority=authority,
        candidate_evaluation=recommendations,
    )

    assert result == repeated
    assert repr(authority) == before_authority
    assert repr(recommendations) == before_recommendations
    assert result.ready is True
    assert result.section_count == 3
    assert result.route_count == 2

    by_section = {row.section_id: row for row in result.sections}
    assert by_section["shared"].projected_dn == 28
    assert by_section["route-a-only"].projected_dn == 22
    assert by_section["route-b-only"].projected_dn == 10

    for section in result.sections:
        assert section.velocity_within_limit is True
        assert section.pressure_gradient_within_limit is True
        assert section.colebrook_converged is True
        assert section.friction_method == "colebrook"
        assert abs(
            section.straight_pressure_drop_Pa
            - section.pressure_gradient_Pa_per_m * section.length_m
        ) < 1.0e-6
        expected_local = (
            section.k_total
            * 998.0
            * section.velocity_m_s**2
            / 2.0
        )
        assert abs(section.local_pressure_drop_Pa - expected_local) < 1.0e-6
        assert abs(
            section.section_total_pressure_drop_Pa
            - section.straight_pressure_drop_Pa
            - section.local_pressure_drop_Pa
        ) < 1.0e-6

    routes = {row.route_id: row for row in result.routes}
    route_a = routes["route-a"]
    route_b = routes["route-b"]
    shared = by_section["shared"]
    a_only = by_section["route-a-only"]
    b_only = by_section["route-b-only"]

    assert route_a.section_ids == ("shared", "route-a-only")
    assert route_b.section_ids == ("shared", "route-b-only")
    assert abs(
        route_a.route_pressure_drop_total_Pa
        - shared.section_total_pressure_drop_Pa
        - a_only.section_total_pressure_drop_Pa
    ) < 1.0e-6
    assert abs(
        route_b.route_pressure_drop_total_Pa
        - shared.section_total_pressure_drop_Pa
        - b_only.section_total_pressure_drop_Pa
    ) < 1.0e-6

    controlling = [row for row in result.routes if row.is_controlling]
    assert len(controlling) == 1
    assert controlling[0].required_added_dp_Pa == 0.0
    assert result.controlling_route_id == controlling[0].route_id
    assert result.controlling_target_Pa == (
        controlling[0].route_pressure_drop_total_Pa
    )
    assert all(row.required_added_dp_Pa >= 0.0 for row in result.routes)
    assert {
        row.rank for row in result.routes
    } == {1, 2}

    missing = build_proportioned_pipe_resizing_hydraulic_projection_v1(
        authority=authority,
        candidate_evaluation=None,
    )
    assert missing.ready is False
    assert "H-S61-B" in missing.status

    source = inspect.getsource(
        build_proportioned_pipe_resizing_hydraulic_projection_v1
    )
    module_source = inspect.getsource(
        __import__(
            "HVAC.hydronics.proportioning."
            "proportioned_pipe_resizing_hydraulic_projection_v1",
            fromlist=["*"],
        )
    )
    assert "K × ρv²/2" in source
    assert "calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1" in (
        module_source
    )
    assert "ProjectState" not in source

    print(
        "OK — H-S61-C Proportioned pipe-resizing hydraulic projection "
        "passed."
    )


if __name__ == "__main__":
    main()
