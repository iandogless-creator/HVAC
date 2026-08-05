# ======================================================================
# H-S66-M — Scoped RR physical-loop runtime handoff into H-S66-L
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
)
from HVAC.heatloss.physics.committed_pipe_external_arrangement_runtime_handoff_v1 import (
    build_committed_pipe_external_arrangement_runtime_handoff_v1,
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
            _section("direct-only", 1, ("direct",)),
            _section("reverse-only", 2, ("reverse",)),
            _section("mixed-common", 3, ("direct", "reverse")),
        ),
        routes=(
            _route("direct", "F&R"),
            _route("reverse", "F+RR"),
        ),
        status="Ready — fixture",
    )


def _row(route_id: str, mode: str) -> SimpleNamespace:
    return SimpleNamespace(
        route_id=route_id,
        rr_added_length_basis_mode=mode,
    )


def main() -> None:
    authority = _authority()
    evidence = (
        _row("direct", "manual_allowance"),
        _row("reverse", "physical_loop_zero_extra"),
    )
    authority_before = repr(authority)
    evidence_before = repr(evidence)

    result = build_committed_pipe_external_arrangement_runtime_handoff_v1(
        committed_authority=authority,
        return_path_comparison_rows=evidence,
    )
    repeated = build_committed_pipe_external_arrangement_runtime_handoff_v1(
        committed_authority=authority,
        return_path_comparison_rows=evidence,
    )

    assert result == repeated
    assert repr(authority) == authority_before
    assert repr(evidence) == evidence_before
    assert result.ready is True, result.status
    assert result.blockers == ()
    assert result.committed_reverse_return_route_count == 1
    assert result.matched_rr_evidence_route_count == 1
    assert result.authority is not None
    assert result.authority.ready is True
    by_id = {row.section_id: row for row in result.authority.sections}
    assert by_id["direct-only"].external_arrangement == (
        STACKED_FLOW_RETURN_PAIR_V1
    )
    assert by_id["reverse-only"].external_arrangement == (
        STACKED_FLOW_RETURN_PAIR_V1
    )
    assert by_id["mixed-common"].external_arrangement == (
        STACKED_FLOW_RETURN_PAIR_V1
    )

    separate = build_committed_pipe_external_arrangement_runtime_handoff_v1(
        committed_authority=authority,
        return_path_comparison_rows=(
            _row("reverse", "manual_allowance"),
        ),
    )
    assert separate.ready is True, separate.status
    separate_by_id = {
        row.section_id: row for row in separate.authority.sections
    }
    assert separate_by_id["direct-only"].external_arrangement == (
        STACKED_FLOW_RETURN_PAIR_V1
    )
    assert separate_by_id["reverse-only"].external_arrangement == (
        SEPARATE_PIPE_V1
    )
    assert separate_by_id["mixed-common"].external_arrangement == (
        SEPARATE_PIPE_V1
    )

    duplicate_same = (
        build_committed_pipe_external_arrangement_runtime_handoff_v1(
            committed_authority=authority,
            return_path_comparison_rows=(
                _row("reverse", "downstream_proxy"),
                _row("reverse", "downstream_proxy"),
            ),
        )
    )
    assert duplicate_same.ready is True, duplicate_same.status

    conflicting = build_committed_pipe_external_arrangement_runtime_handoff_v1(
        committed_authority=authority,
        return_path_comparison_rows=(
            _row("reverse", "physical_loop_zero_extra"),
            _row("reverse", "manual_allowance"),
        ),
    )
    assert conflicting.ready is False
    assert "conflicting scoped RR physical-loop evidence" in conflicting.status

    missing = build_committed_pipe_external_arrangement_runtime_handoff_v1(
        committed_authority=authority,
        return_path_comparison_rows=(_row("direct", "manual_allowance"),),
    )
    assert missing.ready is False
    assert "current scoped RR physical-loop evidence is required" in (
        missing.status
    )

    invalid = build_committed_pipe_external_arrangement_runtime_handoff_v1(
        committed_authority=authority,
        return_path_comparison_rows=(_row("reverse", "invented_mode"),),
    )
    assert invalid.ready is False
    assert invalid.authority is not None
    assert "must be physical_loop_zero_extra" in invalid.status

    direct_only_authority = replace(
        authority,
        sections=(_section("direct-only", 1, ("direct",)),),
        routes=(_route("direct", "F&R"),),
    )
    direct_only = build_committed_pipe_external_arrangement_runtime_handoff_v1(
        committed_authority=direct_only_authority,
        return_path_comparison_rows=(),
    )
    assert direct_only.ready is True, direct_only.status
    assert direct_only.committed_reverse_return_route_count == 0
    assert direct_only.matched_rr_evidence_route_count == 0

    unavailable = build_committed_pipe_external_arrangement_runtime_handoff_v1(
        committed_authority=replace(authority, ready=False),
        return_path_comparison_rows=evidence,
    )
    assert unavailable.ready is False
    assert unavailable.authority is None
    assert "hydraulic-input authority is not ready" in unavailable.status

    source = Path(
        "HVAC/heatloss/physics/"
        "committed_pipe_external_arrangement_runtime_handoff_v1.py"
    ).read_text(encoding="utf-8")
    assert "HVAC.gui_v3" not in source
    assert "from HVAC.project" not in source
    assert "project_state" not in source.lower()
    assert "split(\":\"" not in source
    assert "h_conv" not in source
    assert "spacing_m" not in source

    print(
        "OK — H-S66-M scoped RR physical-loop runtime handoff into "
        "H-S66-L passed."
    )


if __name__ == "__main__":
    main()
