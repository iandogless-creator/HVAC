from __future__ import annotations

import inspect

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
            outside_diameter_m=outside_diameter_m,
            internal_diameter_m=internal_diameter_m,
            roughness_m=0.0000015,
        )
        for dn, outside_diameter_m, internal_diameter_m in dimensions
    )


def _criteria(
        maximum_gradient: float = 200.0,
) -> ProportionedPipeSizingCriteriaV1:
    return ProportionedPipeSizingCriteriaV1(
        material_key="copper",
        material_source="Committed H-S54-A section material",
        default_max_velocity_m_s=1.0,
        max_velocity_source="Environment / local section override",
        max_pressure_gradient_Pa_per_m=maximum_gradient,
        max_pressure_gradient_source="Accepted Proportioned sizing criterion",
        minimum_dn=10,
        maximum_dn=35,
        density_kg_m3=998.0,
        dynamic_viscosity_Pa_s=0.001,
        friction_method="colebrook",
        colebrook_tolerance=1.0e-6,
        colebrook_max_iterations=100,
    )


def _section(
        *,
        section_id: str,
        order: int,
        flow: float,
        current_dn: int,
        maximum_gradient: float = 200.0,
) -> ProportionedPipeSizingSectionAuthorityV1:
    return ProportionedPipeSizingSectionAuthorityV1(
        section_id=section_id,
        section_scope="ROUTE",
        route_ids=("leg-001-primary-subleg",),
        order=order,
        from_label="A",
        to_label="B",
        carried_flow_kg_s=flow,
        length_m=5.0,
        k_total=2.0,
        current_dn=current_dn,
        current_pipe_size_label=f"{current_dn} mm",
        current_velocity_m_s=0.5,
        current_pressure_gradient_Pa_per_m=100.0,
        effective_max_velocity_m_s=1.0,
        max_velocity_source="Environment default",
        effective_max_pressure_gradient_Pa_per_m=maximum_gradient,
        max_pressure_gradient_source="Accepted Proportioned sizing criterion",
        current_dn_in_candidate_family=True,
        current_velocity_within_limit=True,
        current_pressure_gradient_within_limit=True,
        status="Ready — committed section sizing authority",
    )


def _authority(
        *,
        sections: tuple[ProportionedPipeSizingSectionAuthorityV1, ...],
        maximum_gradient: float = 200.0,
) -> ProportionedPipeSizingAuthorityV1:
    return ProportionedPipeSizingAuthorityV1(
        ready=True,
        criteria=_criteria(maximum_gradient),
        candidates=_candidates(),
        sections=sections,
        section_count=len(sections),
        status="Ready — H-S61-A authority",
        blockers=(),
    )


def main() -> None:
    authority = _authority(
        sections=(
            _section(
                section_id="section-medium",
                order=2,
                flow=0.150,
                current_dn=15,
            ),
            _section(
                section_id="section-low",
                order=1,
                flow=0.020,
                current_dn=22,
            ),
            _section(
                section_id="section-retain",
                order=3,
                flow=0.150,
                current_dn=22,
            ),
        )
    )
    before = repr(authority)

    result = build_proportioned_pipe_size_candidate_evaluation_v1(authority)
    repeated = build_proportioned_pipe_size_candidate_evaluation_v1(authority)

    assert result == repeated
    assert repr(authority) == before
    assert result.ready is True
    assert result.section_count == 3
    assert result.evaluated_candidate_count == 15
    assert result.recommended_change_count == 2

    # Stable section ordering and ascending candidate ordering are part of the
    # deterministic result contract.
    low, medium, retain = result.sections
    assert low.section_id == "section-low"
    assert medium.section_id == "section-medium"
    assert retain.section_id == "section-retain"
    assert [
        row.candidate_dn for row in medium.candidate_evaluations
    ] == [10, 15, 22, 28, 35]

    assert low.recommended_dn == 10
    assert low.recommendation == "DECREASE"
    assert low.candidate_evaluations[0].eligible is True

    assert medium.recommended_dn == 22
    assert medium.recommendation == "INCREASE"
    assert medium.candidate_evaluations[0].eligible is False
    assert medium.candidate_evaluations[1].eligible is False
    assert medium.candidate_evaluations[2].eligible is True
    assert medium.candidate_evaluations[2].velocity_within_limit is True
    assert (
        medium.candidate_evaluations[2].pressure_gradient_within_limit
        is True
    )
    assert medium.candidate_evaluations[2].friction_method == "colebrook"
    assert medium.candidate_evaluations[2].colebrook_converged is True

    assert retain.recommended_dn == 22
    assert retain.recommendation == "RETAIN"

    strict = _authority(
        sections=(
            _section(
                section_id="section-strict",
                order=1,
                flow=0.150,
                current_dn=35,
                maximum_gradient=1.0,
            ),
        ),
        maximum_gradient=1.0,
    )
    blocked = build_proportioned_pipe_size_candidate_evaluation_v1(strict)
    assert blocked.ready is False
    assert blocked.sections[0].recommended_dn is None
    assert blocked.sections[0].recommendation == "BLOCKED"
    assert len(blocked.sections[0].candidate_evaluations) == 5
    assert all(
        not row.eligible
        for row in blocked.sections[0].candidate_evaluations
    )
    assert blocked.blockers

    missing = build_proportioned_pipe_size_candidate_evaluation_v1(None)
    assert missing.ready is False
    assert "H-S61-A" in missing.status

    source = inspect.getsource(
        build_proportioned_pipe_size_candidate_evaluation_v1
    )
    module_source = inspect.getsource(
        __import__(
            "HVAC.hydronics.proportioning."
            "proportioned_pipe_size_candidate_evaluation_v1",
            fromlist=["*"],
        )
    )
    assert "smallest candidate DN" in source
    assert (
        "calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1"
        in module_source
    )
    assert "ProjectState" not in source

    print(
        "OK — H-S61-B Proportioned pipe-size candidate evaluation passed."
    )


if __name__ == "__main__":
    main()
