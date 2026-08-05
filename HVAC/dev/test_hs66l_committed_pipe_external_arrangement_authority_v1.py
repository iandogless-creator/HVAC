# ======================================================================
# H-S66-L — Committed pipe external-arrangement authority
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
    build_committed_pipe_external_arrangement_authority_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
    CommittedProportioningHydraulicSectionV1,
)


def _section(
        section_id: str,
        order: int,
        route_ids: tuple[str, ...],
) -> CommittedProportioningHydraulicSectionV1:
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="common" if len(route_ids) > 1 else "route-exclusive",
        route_ids=route_ids,
        order=order,
        from_label="A",
        to_label="B",
        carried_flow_kg_s=0.1,
        pipe_size_label="22 mm",
        dn=22,
        length_m=3.0,
        k_total=0.0,
        velocity_m_s=0.4,
        reynolds_number=5000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=4,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=100.0,
        straight_pressure_drop_Pa=300.0,
        local_pressure_drop_Pa=0.0,
        section_total_pressure_drop_Pa=300.0,
        material_key="copper",
        material_label="Copper EN1057",
        internal_diameter_m=0.0202,
        material_roughness_m=0.0000015,
    )


def _route(route_id: str, basis: str) -> CommittedProportioningHydraulicRouteV1:
    return CommittedProportioningHydraulicRouteV1(
        route_id=route_id,
        route_label=route_id,
        basis=basis,
        chosen_pressure_drop_Pa=1000.0,
        controlling=False,
        required_added_pressure_drop_Pa=0.0,
        preliminary_resistance_Pa_per_kg_s2=0.0,
        common_main_pressure_drop_Pa=0.0,
        leg_entry_pressure_drop_Pa=0.0,
        physical_main_entry_pressure_drop_Pa=0.0,
    )


def _authority() -> CommittedProportioningHydraulicInputAuthorityV1:
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=(
            _section("mixed-common", 3, ("direct", "reverse")),
            _section("direct-only", 1, ("direct",)),
            _section("reverse-only", 2, ("reverse",)),
        ),
        routes=(
            _route("direct", "F&R"),
            _route("reverse", "F+RR"),
        ),
        status="Ready — fixture",
    )


def main() -> None:
    authority = _authority()
    before = repr(authority)
    result = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=authority,
        rr_added_length_basis_mode_by_route_id={
            "reverse": "physical_loop_zero_extra",
        },
    )
    repeated = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=authority,
        rr_added_length_basis_mode_by_route_id={
            "reverse": "physical_loop_zero_extra",
        },
    )

    assert result == repeated
    assert repr(authority) == before
    assert result.ready is True, result.status
    assert result.section_count == 3
    assert result.blockers == ()
    assert [row.section_id for row in result.sections] == [
        "direct-only",
        "reverse-only",
        "mixed-common",
    ]

    by_id = {row.section_id: row for row in result.sections}
    assert (
        by_id["direct-only"].external_arrangement
        == STACKED_FLOW_RETURN_PAIR_V1
    )
    assert by_id["direct-only"].route_bases == ("F&R",)
    assert (
        by_id["reverse-only"].external_arrangement
        == STACKED_FLOW_RETURN_PAIR_V1
    )
    assert by_id["reverse-only"].route_bases == ("F+RR",)
    assert by_id["reverse-only"].rr_added_length_basis_modes == (
        "physical_loop_zero_extra",
    )
    assert (
        by_id["mixed-common"].external_arrangement
        == STACKED_FLOW_RETURN_PAIR_V1
    )
    assert by_id["mixed-common"].route_bases == ("F&R", "F+RR")

    non_perfect_rr = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=authority,
        rr_added_length_basis_mode_by_route_id={
            "reverse": "downstream_proxy",
        },
    )
    non_perfect_by_id = {
        row.section_id: row for row in non_perfect_rr.sections
    }
    assert (
        non_perfect_by_id["direct-only"].external_arrangement
        == STACKED_FLOW_RETURN_PAIR_V1
    )
    assert (
        non_perfect_by_id["reverse-only"].external_arrangement
        == SEPARATE_PIPE_V1
    )
    assert (
        non_perfect_by_id["mixed-common"].external_arrangement
        == SEPARATE_PIPE_V1
    )
    assert "takes precedence" in non_perfect_by_id["mixed-common"].source

    direct_words = replace(authority, routes=(_route("direct", "DIRECT_RETURN"), _route("reverse", "REVERSE_RETURN")))
    words = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=direct_words,
        rr_added_length_basis_mode_by_route_id={
            "reverse": "physical_loop_zero_extra",
        },
    )
    assert words.ready is True
    assert words.sections[0].external_arrangement == STACKED_FLOW_RETURN_PAIR_V1
    assert (
        words.sections[1].external_arrangement
        == STACKED_FLOW_RETURN_PAIR_V1
    )

    missing_route = replace(
        authority,
        routes=authority.routes[:1],
    )
    blocked_missing = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=missing_route,
        rr_added_length_basis_mode_by_route_id={
            "reverse": "physical_loop_zero_extra",
        },
    )
    assert blocked_missing.ready is False
    assert blocked_missing.sections == ()
    assert "chosen route basis missing for reverse" in blocked_missing.status

    invalid_basis = replace(
        authority,
        routes=(
            authority.routes[0],
            replace(authority.routes[1], basis="UNDECIDED"),
        ),
    )
    blocked_basis = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=invalid_basis,
        rr_added_length_basis_mode_by_route_id={
            "reverse": "physical_loop_zero_extra",
        },
    )
    assert blocked_basis.ready is False
    assert "must be F&R or F+RR" in blocked_basis.status

    unavailable = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=replace(authority, ready=False),
        rr_added_length_basis_mode_by_route_id={
            "reverse": "physical_loop_zero_extra",
        },
    )
    assert unavailable.ready is False
    assert unavailable.sections == ()
    assert unavailable.blockers[0] == (
        "Committed proportioning hydraulic-input authority is not ready"
    )

    missing_rr_basis = (
        build_committed_pipe_external_arrangement_authority_v1(
            committed_authority=authority,
            rr_added_length_basis_mode_by_route_id={},
        )
    )
    assert missing_rr_basis.ready is False
    assert "reverse: RR physical-loop basis is required" in (
        missing_rr_basis.blockers
    )

    stale_rr_basis = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=authority,
        rr_added_length_basis_mode_by_route_id={
            "reverse": "manual_allowance",
            "stale": "physical_loop_zero_extra",
        },
    )
    assert stale_rr_basis.ready is False
    assert "has no committed F+RR route" in stale_rr_basis.status

    source = Path(
        "HVAC/heatloss/physics/"
        "committed_pipe_external_arrangement_authority_v1.py"
    ).read_text(encoding="utf-8")
    assert "HVAC.gui_v3" not in source
    assert "from HVAC.project" not in source
    assert "h_conv" not in source
    assert "spacing_m" not in source
    assert "heat_loss" not in source

    print(
        "OK — H-S66-L committed stacked/perfect-RR external-arrangement "
        "authority passed."
    )


if __name__ == "__main__":
    main()
