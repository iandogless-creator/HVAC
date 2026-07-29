from __future__ import annotations

from dataclasses import replace

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


def _section(section_id, route_ids, order, *, iterations=5):
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope=(
            "common_main" if len(route_ids) > 1 else "route_section"
        ),
        route_ids=route_ids,
        order=order,
        from_label=f"{section_id}-from",
        to_label=f"{section_id}-to",
        carried_flow_kg_s=0.2,
        pipe_size_label="22 mm",
        dn=22,
        length_m=10.0,
        k_total=1.5,
        velocity_m_s=0.5,
        reynolds_number=10_000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=iterations,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=200.0,
        straight_pressure_drop_Pa=2_000.0,
        local_pressure_drop_Pa=100.0,
        section_total_pressure_drop_Pa=2_100.0,
    )


def _route(route_id, label):
    return CommittedProportioningHydraulicRouteV1(
        route_id=route_id,
        route_label=label,
        basis="F&R",
        chosen_pressure_drop_Pa=4_200.0,
        controlling=route_id == "route-a",
        required_added_pressure_drop_Pa=(
            0.0 if route_id == "route-a" else 100.0
        ),
        preliminary_resistance_Pa_per_kg_s2=1.0,
        common_main_pressure_drop_Pa=2_100.0,
        leg_entry_pressure_drop_Pa=0.0,
        physical_main_entry_pressure_drop_Pa=2_100.0,
    )


def _snapshot(*, sections=None, routes=None):
    authority = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=tuple(
            sections
            if sections is not None
            else (
                _section(
                    "common-main-001",
                    ("route-a", "route-b"),
                    0,
                ),
                _section("route-a-001", ("route-a",), 1),
                _section(
                    "route-b-001",
                    ("route-b",),
                    1,
                    iterations=0,
                ),
            )
        ),
        routes=tuple(
            routes
            if routes is not None
            else (
                _route("route-a", "Route A"),
                _route("route-b", "Route B"),
            )
        ),
        status="Ready",
    )
    return ProportionedBasisSnapshotV1(
        hydraulic_input_authority=authority,
        hydraulic_input_authority_status=authority.status,
    )


def main() -> None:
    snapshot = _snapshot()
    before = repr(snapshot)
    result = build_committed_basis_section_hydraulic_result_v1(snapshot)

    assert result.ready is True, result.status
    assert result.unique_section_count == 3
    assert result.route_count == 2
    assert len(result.rows) == 4
    assert [row.committed_route_id for row in result.rows] == [
        "route-a",
        "route-a",
        "route-b",
        "route-b",
    ]
    shared = [
        row
        for row in result.rows
        if row.section_id == "common-main-001"
    ]
    assert len(shared) == 2
    assert all(row.shared_across_routes for row in shared)
    assert shared[0].route_ids == ("route-a", "route-b")
    assert shared[0].committed_route_label == "Route A"
    assert shared[1].committed_route_label == "Route B"

    route_b = next(
        row
        for row in result.rows
        if row.section_id == "route-b-001"
    )
    assert route_b.colebrook_iteration_count == 0
    assert route_b.dn == 22
    assert route_b.carried_flow_kg_s == 0.2
    assert route_b.section_total_pressure_drop_Pa == 2_100.0
    assert "No route total recomputed" in result.exclusions
    assert "No live hydraulic or Basic PS preview used" in result.exclusions
    assert repr(snapshot) == before
    assert (
        build_committed_basis_section_hydraulic_result_v1(snapshot)
        == result
    )

    authority = snapshot.hydraulic_input_authority
    assert authority is not None
    unknown = replace(
        snapshot,
        hydraulic_input_authority=replace(
            authority,
            sections=(
                replace(
                    authority.sections[0],
                    route_ids=("route-missing",),
                ),
                *authority.sections[1:],
            ),
        ),
    )
    blocked_unknown = (
        build_committed_basis_section_hydraulic_result_v1(unknown)
    )
    assert blocked_unknown.ready is False
    assert "unknown committed route membership" in blocked_unknown.status

    duplicate = replace(
        snapshot,
        hydraulic_input_authority=replace(
            authority,
            sections=(*authority.sections, authority.sections[0]),
        ),
    )
    blocked_duplicate = (
        build_committed_basis_section_hydraulic_result_v1(duplicate)
    )
    assert blocked_duplicate.ready is False
    assert "Duplicate committed section" in blocked_duplicate.status

    missing_route_sections = _snapshot(
        sections=(_section("route-a-only", ("route-a",), 0),)
    )
    blocked_missing = (
        build_committed_basis_section_hydraulic_result_v1(
            missing_route_sections
        )
    )
    assert blocked_missing.ready is False
    assert "route-b: at least one committed section required" in (
        blocked_missing.status
    )

    not_ready = replace(
        snapshot,
        hydraulic_input_authority=replace(
            authority,
            ready=False,
            blockers=("Frozen input incomplete",),
        ),
    )
    blocked_authority = (
        build_committed_basis_section_hydraulic_result_v1(not_ready)
    )
    assert blocked_authority.ready is False
    assert "Frozen input incomplete" in blocked_authority.status

    absent = build_committed_basis_section_hydraulic_result_v1(None)
    assert absent.ready is False
    assert "committed proportioning snapshot required" in absent.status

    print(
        "OK — H-S57-A committed-basis section hydraulic result passed."
    )


if __name__ == "__main__":
    main()
