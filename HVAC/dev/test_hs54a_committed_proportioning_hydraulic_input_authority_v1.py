# ======================================================================
# H-S54-A — Committed proportioning hydraulic-input authority
# ======================================================================

from types import SimpleNamespace

from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    build_committed_proportioning_hydraulic_input_authority_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
    proportioned_basis_snapshot_from_dict_v1,
    proportioned_basis_snapshot_to_dict_v1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    RoutePressureSectionContributionV1,
)
from HVAC.project.project_state import ProjectState


def _section(section_id: str, scope: str):
    return RoutePressureSectionContributionV1(
        section_id=section_id,
        order=1,
        from_label="A",
        to_label="B",
        pressure_gradient_Pa_per_m=200.0,
        velocity_m_s=0.5,
        reynolds_number=10_000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=5,
        colebrook_converged=True,
        straight_pressure_drop_Pa=2_000.0,
        local_pressure_drop_Pa=100.0,
        section_total_pressure_drop_Pa=2_100.0,
        status="Colebrook evidence",
        section_scope=scope,
        carried_flow_kg_s=0.2,
        pipe_size_label="22 mm",
        dn=22,
        length_m=10.0,
        k_total=1.5,
    )


def main() -> None:
    common = _section("common-main-001", "common_main")
    route_a = _section("route-a-001", "route_section")
    route_b = _section("route-b-001", "route_section")
    projection = SimpleNamespace(
        rows=(
            SimpleNamespace(
                route_id="route-a",
                complete=True,
                sections=(common, route_a),
            ),
            SimpleNamespace(
                route_id="route-b",
                complete=True,
                sections=(common, route_b),
            ),
        )
    )
    chosen = (
        SimpleNamespace(
            route_id="route-a",
            route="Route A",
            basis="F&R",
            chosen_dp_pa=30_000.0,
            is_controlling=True,
            common_main_dp_pa=2_100.0,
            leg_entry_dp_pa=500.0,
            physical_main_entry_dp_pa=2_600.0,
        ),
        SimpleNamespace(
            route_id="route-b",
            route="Route B",
            basis="F&R",
            chosen_dp_pa=25_000.0,
            is_controlling=False,
            common_main_dp_pa=2_100.0,
            leg_entry_dp_pa=500.0,
            physical_main_entry_dp_pa=2_600.0,
        ),
    )
    resistance = SimpleNamespace(
        rows=(
            SimpleNamespace(
                route_id="route-a",
                required_added_dp="0.0 Pa",
                resistance_pa_per_kg_s2="0.0 Pa/(kg/s)²",
            ),
            SimpleNamespace(
                route_id="route-b",
                required_added_dp="5000.0 Pa",
                resistance_pa_per_kg_s2="125000.0 Pa/(kg/s)²",
            ),
        )
    )

    authority = (
        build_committed_proportioning_hydraulic_input_authority_v1(
            route_pressure_projection=projection,
            chosen_controlling_rows=chosen,
            resistance_basis=resistance,
        )
    )
    assert authority.ready is True, authority.status
    assert len(authority.sections) == 3
    common_frozen = next(
        row for row in authority.sections
        if row.section_id == "common-main-001"
    )
    assert common_frozen.route_ids == ("route-a", "route-b")
    assert common_frozen.dn == 22
    assert common_frozen.pipe_size_label == "22 mm"
    assert common_frozen.length_m == 10.0
    assert common_frozen.friction_method == "colebrook"
    assert len(authority.routes) == 2
    assert authority.routes[1].required_added_pressure_drop_Pa == 5000.0

    snapshot = ProportionedBasisSnapshotV1(
        hydraulic_input_authority=authority,
        hydraulic_input_authority_status=authority.status,
    )
    payload = proportioned_basis_snapshot_to_dict_v1(snapshot)
    restored = proportioned_basis_snapshot_from_dict_v1(payload)
    assert restored is not None
    assert restored.hydraulic_input_authority == authority

    project = ProjectState(project_id="hs54a", name="H-S54-A")
    project.hydronic_proportioned_basis_snapshot = snapshot
    project_restored = ProjectState.from_dict(project.to_dict())
    restored_snapshot = project_restored.hydronic_proportioned_basis_snapshot
    assert restored_snapshot is not None
    assert restored_snapshot.hydraulic_input_authority == authority

    incomplete = SimpleNamespace(
        rows=(
            SimpleNamespace(
                route_id="route-a",
                complete=False,
                sections=(common,),
            ),
        )
    )
    blocked = build_committed_proportioning_hydraulic_input_authority_v1(
        route_pressure_projection=incomplete,
        chosen_controlling_rows=chosen[:1],
        resistance_basis=resistance,
    )
    assert blocked.ready is False
    assert "complete route pressure evidence required" in blocked.status

    assert "No ProjectState mutation" not in authority.note
    assert "no recalculation" in authority.note.lower()
    print(
        "OK — H-S54-A committed proportioning hydraulic-input "
        "authority passed."
    )


if __name__ == "__main__":
    main()
