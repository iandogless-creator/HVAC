# ======================================================================
# H-S54-B1 — zero-iteration and optional route-breakdown acceptance
# ======================================================================

from types import SimpleNamespace

from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    build_committed_proportioning_hydraulic_input_authority_v1,
    committed_proportioning_hydraulic_input_authority_from_dict_v1,
    committed_proportioning_hydraulic_input_authority_to_dict_v1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    RoutePressureSectionContributionV1,
)


def main() -> None:
    section = RoutePressureSectionContributionV1(
        section_id="route-section-zero-iteration",
        order=1,
        from_label="A",
        to_label="B",
        pressure_gradient_Pa_per_m=200.0,
        velocity_m_s=0.5,
        reynolds_number=10_000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=0,
        colebrook_converged=True,
        straight_pressure_drop_Pa=2_000.0,
        local_pressure_drop_Pa=0.0,
        section_total_pressure_drop_Pa=2_000.0,
        status="Converged without iterative correction",
        section_scope="route_section",
        carried_flow_kg_s=0.2,
        pipe_size_label="22 mm",
        dn=22,
        length_m=10.0,
        k_total=0.0,
    )
    route_projection = SimpleNamespace(
        rows=(
            SimpleNamespace(
                route_id="route-a",
                complete=True,
                sections=(section,),
            ),
        )
    )
    chosen = (
        SimpleNamespace(
            route_id="route-a",
            route="Route A",
            basis="F&R",
            chosen_dp_pa=20_000.0,
            is_controlling=True,
            common_main_dp_pa=None,
            leg_entry_dp_pa=None,
            physical_main_entry_dp_pa=None,
        ),
    )
    resistance = SimpleNamespace(
        rows=(
            SimpleNamespace(
                route_id="route-a",
                required_added_dp="0.0 Pa",
                resistance_pa_per_kg_s2="0.0 Pa/(kg/s)²",
            ),
        )
    )

    authority = (
        build_committed_proportioning_hydraulic_input_authority_v1(
            route_pressure_projection=route_projection,
            chosen_controlling_rows=chosen,
            resistance_basis=resistance,
        )
    )
    assert authority.ready is True, authority.status
    assert authority.sections[0].colebrook_iteration_count == 0
    assert authority.routes[0].common_main_pressure_drop_Pa is None
    assert authority.routes[0].leg_entry_pressure_drop_Pa is None
    assert authority.routes[0].physical_main_entry_pressure_drop_Pa is None

    payload = (
        committed_proportioning_hydraulic_input_authority_to_dict_v1(
            authority
        )
    )
    restored = (
        committed_proportioning_hydraulic_input_authority_from_dict_v1(
            payload
        )
    )
    assert restored == authority

    missing_resistance = SimpleNamespace(
        rows=(
            SimpleNamespace(
                route_id="route-a",
                required_added_dp="0.0 Pa",
                resistance_pa_per_kg_s2="—",
            ),
        )
    )
    blocked = build_committed_proportioning_hydraulic_input_authority_v1(
        route_pressure_projection=route_projection,
        chosen_controlling_rows=chosen,
        resistance_basis=missing_resistance,
    )
    assert blocked.ready is False
    assert "preliminary_resistance_Pa_per_kg_s2" in blocked.status

    print(
        "OK — H-S54-B1 zero-iteration and optional route-breakdown "
        "authority repair passed."
    )


if __name__ == "__main__":
    main()
