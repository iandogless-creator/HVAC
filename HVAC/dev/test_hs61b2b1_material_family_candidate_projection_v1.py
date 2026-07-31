# ======================================================================
# H-S61-B2B1 — material-family candidate and projection identity
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import (
    build_proportioned_pipe_resizing_hydraulic_projection_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_size_candidate_evaluation_v1 import (
    build_proportioned_pipe_size_candidate_evaluation_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_sizing_authority_v1 import (
    ProportionedPipeSizingAuthorityV1,
    ProportionedPipeSizingCriteriaV1,
    ProportionedPipeSizingSectionAuthorityV1,
    _candidate_family_v1,
)


def _section() -> ProportionedPipeSizingSectionAuthorityV1:
    return ProportionedPipeSizingSectionAuthorityV1(
        section_id="section-a",
        section_scope="route_section",
        route_ids=("route-a",),
        order=1,
        from_label="Boiler / Heat Source",
        to_label="Room A",
        carried_flow_kg_s=0.050,
        length_m=8.0,
        k_total=2.0,
        current_dn=22,
        current_pipe_size_label="22 mm",
        current_velocity_m_s=0.16,
        current_pressure_gradient_Pa_per_m=20.0,
        effective_max_velocity_m_s=1.0,
        max_velocity_source="Environment design criterion",
        effective_max_pressure_gradient_Pa_per_m=200.0,
        max_pressure_gradient_source="Accepted Proportioned criterion",
        current_dn_in_candidate_family=True,
        current_velocity_within_limit=True,
        current_pressure_gradient_within_limit=True,
        status="Ready — current copper section",
        current_material_key="copper",
        current_material_label="Copper EN1057",
        current_internal_diameter_m=0.020,
    )


def _criteria(material_key: str) -> ProportionedPipeSizingCriteriaV1:
    return ProportionedPipeSizingCriteriaV1(
        current_material_key="copper",
        current_material_source="H-S61-B2A current family",
        material_key=material_key,
        material_source="H-S61-B2A proposed family",
        default_max_velocity_m_s=1.0,
        max_velocity_source="Environment design criterion",
        max_pressure_gradient_Pa_per_m=200.0,
        max_pressure_gradient_source="Accepted Proportioned criterion",
        minimum_dn=10,
        maximum_dn=54,
    )


def main() -> None:
    mlcp_criteria = _criteria("mlcp")
    mlcp_candidates, blockers = _candidate_family_v1(mlcp_criteria)
    assert blockers == []
    assert [row.dn for row in mlcp_candidates] == [16, 20, 26, 32]
    assert [row.pipe_size_label for row in mlcp_candidates] == [
        "16×2 mm",
        "20×2 mm",
        "26×3 mm",
        "32×3 mm",
    ]
    assert {row.material_key for row in mlcp_candidates} == {"mlcp"}
    assert [round(row.internal_diameter_m * 1000.0) for row in mlcp_candidates] == [
        12,
        16,
        20,
        26,
    ]
    assert all(abs(row.roughness_m - 0.000007) < 1.0e-12 for row in mlcp_candidates)
    assert 22 not in {row.dn for row in mlcp_candidates}

    authority = ProportionedPipeSizingAuthorityV1(
        ready=True,
        criteria=mlcp_criteria,
        candidates=mlcp_candidates,
        sections=(_section(),),
        section_count=1,
        status="Ready — current copper / proposed MLCP",
    )
    evaluation = build_proportioned_pipe_size_candidate_evaluation_v1(
        authority
    )
    assert evaluation.ready is True, evaluation.status
    result = evaluation.sections[0]
    assert result.current_material_key == "copper"
    assert result.recommended_material_key == "mlcp"
    assert result.recommended_pipe_size_label in {
        "16×2 mm",
        "20×2 mm",
        "26×3 mm",
        "32×3 mm",
    }
    assert result.recommended_internal_diameter_m is not None
    assert all(
        row.material_key == "mlcp"
        for row in result.candidate_evaluations
    )

    projection = build_proportioned_pipe_resizing_hydraulic_projection_v1(
        authority=authority,
        candidate_evaluation=evaluation,
    )
    assert projection.ready is True, projection.status
    projected = projection.sections[0]
    assert projected.current_material_key == "copper"
    assert projected.current_pipe_size_label == "22 mm"
    assert abs(projected.current_internal_diameter_m - 0.020) < 1.0e-12
    assert projected.projected_material_key == "mlcp"
    assert "×" in projected.projected_pipe_size_label
    assert projected.internal_diameter_m > 0.0

    pex_candidates, pex_blockers = _candidate_family_v1(_criteria("pex"))
    assert pex_blockers == []
    assert [row.dn for row in pex_candidates] == [16, 20, 26]
    assert [row.pipe_size_label for row in pex_candidates] == [
        "16×2 mm",
        "20×2 mm",
        "26×3 mm",
    ]
    assert {row.material_key for row in pex_candidates} == {"pex"}

    print(
        "OK — H-S61-B2B1 family-aware MLCP/PEX candidate and "
        "projection identity passed."
    )


if __name__ == "__main__":
    main()
