# ======================================================================
# H-S66-N1C1 — Canonical committed-route identity bridge
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
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
        route_ids: tuple[str, ...],
) -> CommittedProportioningHydraulicSectionV1:
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="route-exclusive",
        route_ids=route_ids,
        order=1,
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


def _route(
        route_id: str,
        basis: str,
) -> CommittedProportioningHydraulicRouteV1:
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


def _authority(
        *,
        section_route_ids: tuple[str, ...],
        routes: tuple[CommittedProportioningHydraulicRouteV1, ...],
) -> CommittedProportioningHydraulicInputAuthorityV1:
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=(_section("section-001", section_route_ids),),
        routes=routes,
        status="Ready — fixture",
    )


def main() -> None:
    legacy = _authority(
        section_route_ids=(
            "leg-001:leg-001-primary-subleg",
            "leg-002:leg-002-primary-subleg",
        ),
        routes=(
            _route("leg-001-primary-subleg", "F&R"),
            _route("leg-002-primary-subleg", "F+RR"),
        ),
    )
    before = repr(legacy)
    bridged = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=legacy,
        rr_added_length_basis_mode_by_route_id={
            "leg-002-primary-subleg": "physical_loop_zero_extra",
        },
    )
    repeated = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=legacy,
        rr_added_length_basis_mode_by_route_id={
            "leg-002-primary-subleg": "physical_loop_zero_extra",
        },
    )
    assert bridged == repeated
    assert repr(legacy) == before
    assert bridged.ready is True, bridged.status
    row = bridged.sections[0]
    assert row.route_ids == (
        "leg-001:leg-001-primary-subleg",
        "leg-002:leg-002-primary-subleg",
    )
    assert row.route_bases == ("F&R", "F+RR")
    assert row.rr_added_length_basis_modes == (
        "physical_loop_zero_extra",
    )
    assert row.external_arrangement == STACKED_FLOW_RETURN_PAIR_V1

    exact_precedence = _authority(
        section_route_ids=("leg-001:physical-route",),
        routes=(
            _route("leg-001:physical-route", "F&R"),
            _route("leg-002:physical-route", "F+RR"),
        ),
    )
    exact = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=exact_precedence,
        rr_added_length_basis_mode_by_route_id={
            "leg-002:physical-route": "manual_allowance",
        },
    )
    assert exact.ready is True, exact.status
    assert exact.sections[0].route_bases == ("F&R",)
    assert exact.sections[0].external_arrangement == (
        STACKED_FLOW_RETURN_PAIR_V1
    )

    ambiguous = _authority(
        section_route_ids=("legacy:physical-route",),
        routes=(
            _route("leg-001:physical-route", "F&R"),
            _route("leg-002:physical-route", "F&R"),
        ),
    )
    blocked_ambiguous = (
        build_committed_pipe_external_arrangement_authority_v1(
            committed_authority=ambiguous,
            rr_added_length_basis_mode_by_route_id={},
        )
    )
    assert blocked_ambiguous.ready is False
    assert blocked_ambiguous.sections == ()
    assert "committed route identity is ambiguous" in (
        blocked_ambiguous.status
    )

    collapsed = _authority(
        section_route_ids=("leg-001:physical-route", "physical-route"),
        routes=(_route("physical-route", "F&R"),),
    )
    blocked_collapsed = (
        build_committed_pipe_external_arrangement_authority_v1(
            committed_authority=collapsed,
            rr_added_length_basis_mode_by_route_id={},
        )
    )
    assert blocked_collapsed.ready is False
    assert "duplicate committed route membership after canonical bridge" in (
        blocked_collapsed.status
    )

    missing = replace(
        legacy,
        routes=(_route("unrelated-route", "F&R"),),
    )
    blocked_missing = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=missing,
        rr_added_length_basis_mode_by_route_id={},
    )
    assert blocked_missing.ready is False
    assert "chosen route basis missing for" in blocked_missing.status

    source = Path(
        "HVAC/heatloss/physics/"
        "committed_pipe_external_arrangement_authority_v1.py"
    ).read_text(encoding="utf-8")
    assert "_committed_route_identity_candidates_v1" in source
    assert 'rsplit(":", 1)[-1]' in source
    assert "route_label" not in source[source.index(
        "def _committed_route_identity_candidates_v1"
    ):source.index("def _normalise_route_basis_v1")]
    assert "HVAC.gui_v3" not in source
    assert "from HVAC.project" not in source

    print(
        "OK — H-S66-N1C1 canonical committed-route identity bridge into "
        "external-arrangement authority passed."
    )


if __name__ == "__main__":
    main()
