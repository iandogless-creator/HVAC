# ======================================================================
# H-S61-A — Proportioned pipe-sizing authority and criteria test
# ======================================================================

from __future__ import annotations

from dataclasses import replace

from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
    CommittedProportioningHydraulicSectionV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_sizing_authority_v1 import (
    ProportionedPipeSizingCriteriaV1,
    build_proportioned_pipe_sizing_authority_v1,
)


def _section(
        section_id: str,
        *,
        dn: int,
        velocity: float,
        gradient: float,
        order: int,
):
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="route_section",
        route_ids=("route-a",),
        order=order,
        from_label=f"{section_id}-from",
        to_label=f"{section_id}-to",
        carried_flow_kg_s=0.15,
        pipe_size_label=f"{dn} mm",
        dn=dn,
        length_m=5.0,
        k_total=1.5,
        velocity_m_s=velocity,
        reynolds_number=10_000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=5,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=gradient,
        straight_pressure_drop_Pa=gradient * 5.0,
        local_pressure_drop_Pa=50.0,
        section_total_pressure_drop_Pa=(gradient * 5.0) + 50.0,
    )


def _route():
    return CommittedProportioningHydraulicRouteV1(
        route_id="route-a",
        route_label="Route A",
        basis="F&R",
        chosen_pressure_drop_Pa=10_000.0,
        controlling=True,
        required_added_pressure_drop_Pa=0.0,
        preliminary_resistance_Pa_per_kg_s2=0.0,
        common_main_pressure_drop_Pa=1_000.0,
        leg_entry_pressure_drop_Pa=500.0,
        physical_main_entry_pressure_drop_Pa=1_500.0,
    )


def _snapshot(*, sections=None):
    authority = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=tuple(
            sections
            if sections is not None
            else (
                _section(
                    "section-high-gradient",
                    dn=15,
                    velocity=0.95,
                    gradient=1_359.4,
                    order=1,
                ),
                _section(
                    "section-within-limits",
                    dn=22,
                    velocity=0.55,
                    gradient=180.0,
                    order=2,
                ),
            )
        ),
        routes=(_route(),),
        status="Ready",
    )
    return ProportionedBasisSnapshotV1(
        hydraulic_input_authority=authority,
        hydraulic_input_authority_status=authority.status,
    )


def main() -> None:
    snapshot = _snapshot()
    criteria = ProportionedPipeSizingCriteriaV1()
    before = repr(snapshot)

    result = build_proportioned_pipe_sizing_authority_v1(
        snapshot,
        criteria=criteria,
        section_max_velocity_overrides_m_s={
            "section-high-gradient": 1.05,
        },
    )
    assert result.ready is True, result.status
    assert result.criteria == criteria
    assert result.section_count == 2
    assert [row.dn for row in result.candidates] == [
        10, 15, 22, 28, 35, 42, 54,
    ]
    dn15 = next(row for row in result.candidates if row.dn == 15)
    assert dn15.material_key == "copper"
    assert dn15.material_label == "Copper EN1057"
    assert dn15.internal_diameter_m == 0.0136
    assert dn15.roughness_m == 0.0000015
    dn42 = next(row for row in result.candidates if row.dn == 42)
    dn54 = next(row for row in result.candidates if row.dn == 54)
    assert dn42.internal_diameter_m == 0.040
    assert dn54.internal_diameter_m == 0.0516

    high = next(
        row
        for row in result.sections
        if row.section_id == "section-high-gradient"
    )
    assert high.effective_max_velocity_m_s == 1.05
    assert high.max_velocity_source == "Local section override"
    assert high.current_velocity_within_limit is True
    assert high.current_pressure_gradient_within_limit is False
    assert "Δp/m exceeds accepted maximum" in high.status

    within = next(
        row
        for row in result.sections
        if row.section_id == "section-within-limits"
    )
    assert within.effective_max_velocity_m_s == 1.0
    assert within.current_velocity_within_limit is True
    assert within.current_pressure_gradient_within_limit is True
    assert "satisfies accepted criteria" in within.status
    assert "No candidate pipe size selected" in result.exclusions
    assert repr(snapshot) == before
    assert (
        build_proportioned_pipe_sizing_authority_v1(
            snapshot,
            criteria=criteria,
            section_max_velocity_overrides_m_s={
                "section-high-gradient": 1.05,
            },
        )
        == result
    )

    orphan = build_proportioned_pipe_sizing_authority_v1(
        snapshot,
        criteria=criteria,
        section_max_velocity_overrides_m_s={"section-missing": 1.1},
    )
    assert orphan.ready is False
    assert "has no committed section" in orphan.status

    outside_family = _snapshot(
        sections=(
            _section(
                "section-dn67",
                dn=67,
                velocity=0.3,
                gradient=80.0,
                order=1,
            ),
        )
    )
    blocked_family = build_proportioned_pipe_sizing_authority_v1(
        outside_family,
        criteria=criteria,
    )
    assert blocked_family.ready is False
    assert "outside the current copper material family" in (
        blocked_family.status
    )

    unknown_material = build_proportioned_pipe_sizing_authority_v1(
        snapshot,
        criteria=replace(criteria, material_key="unknown"),
    )
    assert unknown_material.ready is False
    assert "Unknown pipe material" in unknown_material.status

    invalid_gradient = build_proportioned_pipe_sizing_authority_v1(
        snapshot,
        criteria=replace(
            criteria,
            max_pressure_gradient_Pa_per_m=0.0,
        ),
    )
    assert invalid_gradient.ready is False
    assert "Maximum pressure gradient" in invalid_gradient.status

    missing = build_proportioned_pipe_sizing_authority_v1(
        None,
        criteria=criteria,
    )
    assert missing.ready is False
    assert "committed proportioning snapshot required" in missing.status

    print(
        "OK — H-S61-A Proportioned pipe-sizing authority and "
        "criteria passed."
    )


if __name__ == "__main__":
    main()
