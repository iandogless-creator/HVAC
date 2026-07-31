from __future__ import annotations

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.hydronics.proportioning.proportioned_pipe_size_candidate_evaluation_v1 import (
    build_proportioned_pipe_size_candidate_evaluation_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_sizing_authority_v1 import (
    DEFAULT_PROPORTIONED_MAX_DN_V1,
    ProportionedPipeSizingAuthorityV1,
    ProportionedPipeSizingCandidateV1,
    ProportionedPipeSizingCriteriaV1,
    ProportionedPipeSizingSectionAuthorityV1,
)


def _candidates() -> tuple[ProportionedPipeSizingCandidateV1, ...]:
    material = get_material("copper")
    assert material is not None
    return tuple(
        ProportionedPipeSizingCandidateV1(
            material_key="copper",
            material_label=str(material.name),
            dn=int(dn),
            pipe_size_label=f"{int(dn)} mm",
            outside_diameter_m=float(size.od_mm) / 1000.0,
            internal_diameter_m=float(size.id_mm) / 1000.0,
            roughness_m=float(material.roughness_mm) / 1000.0,
        )
        for dn, size in sorted(material.sizes.items())
        if 10 <= int(dn) <= 54
    )


def _section(
        section_id: str,
        *,
        flow_kg_s: float,
) -> ProportionedPipeSizingSectionAuthorityV1:
    return ProportionedPipeSizingSectionAuthorityV1(
        section_id=section_id,
        section_scope="COMMON_MAIN",
        route_ids=("route-a",),
        order=1,
        from_label="Boiler / Heat Source",
        to_label="Heating Leg 1 take-off",
        carried_flow_kg_s=flow_kg_s,
        length_m=8.0,
        k_total=0.0,
        current_dn=35,
        current_pipe_size_label="35 mm",
        current_velocity_m_s=0.5,
        current_pressure_gradient_Pa_per_m=100.0,
        effective_max_velocity_m_s=0.7,
        max_velocity_source="H-S61-B1 test criterion",
        effective_max_pressure_gradient_Pa_per_m=200.0,
        max_pressure_gradient_source="H-S61-B1 test criterion",
        current_dn_in_candidate_family=True,
        current_velocity_within_limit=True,
        current_pressure_gradient_within_limit=True,
        status="Ready — committed section sizing authority",
    )


def _authority(
        section: ProportionedPipeSizingSectionAuthorityV1,
) -> ProportionedPipeSizingAuthorityV1:
    criteria = ProportionedPipeSizingCriteriaV1(
        default_max_velocity_m_s=0.7,
        max_pressure_gradient_Pa_per_m=200.0,
    )
    candidates = _candidates()
    return ProportionedPipeSizingAuthorityV1(
        ready=True,
        criteria=criteria,
        candidates=candidates,
        sections=(section,),
        section_count=1,
        status="Ready — H-S61-B1 authority",
    )


def main() -> None:
    assert DEFAULT_PROPORTIONED_MAX_DN_V1 == 54
    assert [row.dn for row in _candidates()] == [
        10, 15, 22, 28, 35, 42, 54,
    ]

    extended = build_proportioned_pipe_size_candidate_evaluation_v1(
        _authority(_section("extended-to-dn54", flow_kg_s=1.0))
    )
    assert extended.ready is True, extended.status
    assert extended.sections[0].recommended_dn == 54
    assert extended.sections[0].candidate_range_exhausted is False
    assert extended.candidate_range_exhausted_count == 0

    exhausted = build_proportioned_pipe_size_candidate_evaluation_v1(
        _authority(_section("exhausted-at-dn54", flow_kg_s=2.0))
    )
    assert exhausted.ready is False
    assert exhausted.sections[0].recommended_dn is None
    assert exhausted.sections[0].candidate_range_exhausted is True
    assert exhausted.candidate_range_exhausted_count == 1
    assert "range exhausted at 54 mm" in exhausted.sections[0].status
    assert "range exhausted" in exhausted.status
    assert "DN54" in exhausted.blockers[0]

    print(
        "OK — H-S61-B1 extended copper candidate range and "
        "exhaustion evidence passed."
    )


if __name__ == "__main__":
    main()
