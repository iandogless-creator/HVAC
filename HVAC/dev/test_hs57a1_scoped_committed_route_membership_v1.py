# ======================================================================
# H-S57-A1 — Scoped committed route-membership repair
# ======================================================================

from __future__ import annotations

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


def _route(route_id: str, label: str):
    return CommittedProportioningHydraulicRouteV1(
        route_id=route_id,
        route_label=label,
        basis="F&R",
        chosen_pressure_drop_Pa=30_000.0,
        controlling=False,
        required_added_pressure_drop_Pa=1_000.0,
        preliminary_resistance_Pa_per_kg_s2=10_000.0,
        common_main_pressure_drop_Pa=2_000.0,
        leg_entry_pressure_drop_Pa=1_000.0,
        physical_main_entry_pressure_drop_Pa=500.0,
    )


def _section(route_ids: tuple[str, ...]):
    return CommittedProportioningHydraulicSectionV1(
        section_id="common-main-to-leg-001-section-001",
        section_scope="common_main",
        route_ids=route_ids,
        order=1,
        from_label="Boiler / Heat Source",
        to_label="Leg 1",
        carried_flow_kg_s=0.4,
        pipe_size_label="22 mm",
        dn=22,
        length_m=5.0,
        k_total=1.5,
        velocity_m_s=0.6,
        reynolds_number=20_000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=5,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=200.0,
        straight_pressure_drop_Pa=1_000.0,
        local_pressure_drop_Pa=100.0,
        section_total_pressure_drop_Pa=1_100.0,
    )


def _snapshot(section):
    authority = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=(section,),
        routes=(
            _route(
                "leg-001-primary-subleg",
                "Leg 1A Common subleg",
            ),
            _route(
                "leg-001-subleg-b",
                "Leg 1B Branch subleg",
            ),
        ),
        status="Ready",
    )
    return ProportionedBasisSnapshotV1(
        hydraulic_input_authority=authority,
    )


def main() -> None:
    result = build_committed_basis_section_hydraulic_result_v1(
        _snapshot(
            _section(
                (
                    "leg-001:leg-001-primary-subleg",
                    "leg-001:leg-001-subleg-b",
                )
            )
        )
    )

    assert result.ready is True
    assert result.blockers == ()
    assert result.unique_section_count == 1
    assert result.route_count == 2
    assert len(result.rows) == 2
    assert [row.committed_route_id for row in result.rows] == [
        "leg-001-primary-subleg",
        "leg-001-subleg-b",
    ]
    assert all(row.shared_across_routes for row in result.rows)
    assert result.rows[0].route_ids == (
        "leg-001:leg-001-primary-subleg",
        "leg-001:leg-001-subleg-b",
    )

    bad = build_committed_basis_section_hydraulic_result_v1(
        _snapshot(
            _section(
                (
                    "leg-999:leg-001-primary-subleg",
                    "leg-001:missing-route",
                )
            )
        )
    )
    assert bad.ready is False
    assert any(
        "unknown committed route membership "
        "leg-999:leg-001-primary-subleg" in blocker
        for blocker in bad.blockers
    )
    assert any(
        "unknown committed route membership leg-001:missing-route"
        in blocker
        for blocker in bad.blockers
    )

    print(
        "OK — H-S57-A1 scoped committed route membership repair passed."
    )


if __name__ == "__main__":
    main()
