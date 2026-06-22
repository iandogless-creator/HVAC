# ======================================================================
# HVAC/dev/test_basic_ps_branch_flow_comparison_v1.py
# H-S24-E — Basic PS vs branch-aware carried-flow comparison
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.proportioning.basic_ps_branch_flow_comparison_v1 import (
    build_basic_ps_branch_flow_comparison_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.project.project_state import ProjectState


def _add_emitter(project: ProjectState, room_id: str, output_W: float) -> None:
    emitter_id = f"emitter-{room_id}"

    project.emitters[emitter_id] = EmitterV1(
        emitter_id=emitter_id,
        room_id=room_id,
        emitter_type="radiator",
        design_output_W=output_W,
    )


def _build_project() -> ProjectState:
    project = ProjectState(
        project_id="dev-hs24e-basic-vs-branch-aware",
        name="DEV H-S24-E Basic PS vs Branch Aware",
    )

    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
        design_flow_temp_c=75.0,
        design_return_temp_c=65.0,
    )

    for room_id, output_W in {
        "room-002": 200.0,
        "room-003": 300.0,
        "room-004": 400.0,
        "room-005": 500.0,
        "room-006": 600.0,
        "room-007": 700.0,
        "room-008": 800.0,
    }.items():
        _add_emitter(project, room_id, output_W)

    primary = HydronicSublegV1(
        subleg_id="leg-001-primary-subleg",
        label="Leg 1A Common subleg",
        origin_room_id="room-001",
        route_room_ids=["room-002", "room-003", "room-004"],
        index_room_id="room-004",
    )

    true_branch = HydronicSublegV1(
        subleg_id="leg-001-subleg-b",
        label="Leg 1B Branch subleg",
        origin_room_id="room-003",
        route_room_ids=["room-005", "room-006"],
        index_room_id="room-006",
    )

    terminal_continuation = HydronicSublegV1(
        subleg_id="leg-001-subleg-c",
        label="Leg 1C Terminal continuation",
        origin_room_id="room-004",
        route_room_ids=["room-007"],
        index_room_id="room-007",
    )

    early_branch = HydronicSublegV1(
        subleg_id="leg-001-subleg-d",
        label="Leg 1D Early riser branch",
        origin_room_id="room-002",
        route_room_ids=["room-008"],
        index_room_id="room-008",
    )

    primary.sublegs.append(true_branch)
    primary.sublegs.append(terminal_continuation)
    primary.sublegs.append(early_branch)

    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="room-001",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=["room-002", "room-003", "room-004"],
                index_room_id="room-004",
                sublegs=[primary],
            )
        ],
    )

    return project


def main() -> None:
    project = _build_project()

    primary = build_basic_ps_branch_flow_comparison_v1(
        project,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
    )

    print()
    print("H-S24-E — Basic PS vs branch-aware carried-flow comparison")
    print("=========================================================")
    print("PRIMARY ready:", primary.ready)
    print("PRIMARY status:", primary.status)

    for row in primary.rows:
        print(
            row.section_id,
            "| basic Q:", row.basic_carried_heat_W,
            "| branch-aware Q:", row.branch_aware_carried_heat_W,
            "| ΔQ:", row.heat_delta_W,
            "| basic rooms:", list(row.basic_downstream_room_ids),
            "| branch-aware rooms:", list(row.branch_aware_carried_room_ids),
            "| rolled-up:", list(row.branch_aware_rolled_up_room_ids),
            "| differs:", row.differs,
            "| status:", row.status,
        )

    assert primary.ready is True
    assert "3 differing section(s)" in primary.status
    assert len(primary.rows) == 3

    assert primary.rows[0].basic_carried_heat_W == 900.0
    assert primary.rows[0].branch_aware_carried_heat_W == 3500.0
    assert primary.rows[0].heat_delta_W == 2600.0
    assert primary.rows[0].differs is True

    assert primary.rows[1].basic_carried_heat_W == 700.0
    assert primary.rows[1].branch_aware_carried_heat_W == 2500.0
    assert primary.rows[1].heat_delta_W == 1800.0
    assert primary.rows[1].differs is True

    assert primary.rows[2].basic_carried_heat_W == 400.0
    assert primary.rows[2].branch_aware_carried_heat_W == 1100.0
    assert primary.rows[2].heat_delta_W == 700.0
    assert primary.rows[2].differs is True

    branch = build_basic_ps_branch_flow_comparison_v1(
        project,
        leg_id="leg-001",
        subleg_id="leg-001-subleg-b",
    )

    print()
    print("BRANCH ready:", branch.ready)
    print("BRANCH status:", branch.status)

    for row in branch.rows:
        print(
            row.section_id,
            "| basic Q:", row.basic_carried_heat_W,
            "| branch-aware Q:", row.branch_aware_carried_heat_W,
            "| ΔQ:", row.heat_delta_W,
            "| differs:", row.differs,
        )

    assert branch.ready is True
    assert "no differences" in branch.status
    assert len(branch.rows) == 2
    assert all(row.differs is False for row in branch.rows)

    print()
    print("OK — Basic PS / branch-aware carried-flow comparison passed.")


if __name__ == "__main__":
    main()
