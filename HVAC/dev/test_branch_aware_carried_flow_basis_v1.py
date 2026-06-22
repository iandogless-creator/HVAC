# ======================================================================
# HVAC/dev/test_branch_aware_carried_flow_basis_v1.py
# H-S24-C — Branch-aware carried-flow basis test
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.proportioning.branch_aware_carried_flow_basis_v1 import (
    build_branch_aware_carried_flow_basis_v1,
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


def _flow(output_W: float) -> float:
    return output_W / (4180.0 * 10.0)


def main() -> None:
    project = ProjectState(
        project_id="dev-hs24c-branch-aware-flow",
        name="DEV H-S24-C Branch Aware Flow",
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

    basis = build_branch_aware_carried_flow_basis_v1(project)

    print()
    print("H-S24-C — Branch-aware carried-flow basis")
    print("=========================================")
    print("ready:", basis.ready)
    print("status:", basis.status)

    for row in basis.rows:
        print(
            row.section_id,
            "| kind:", row.subleg_kind,
            "| from:", row.from_label,
            "| to:", row.to_room_id,
            "| own:", list(row.own_downstream_room_ids),
            "| roll-up:", list(row.rolled_up_room_ids),
            "| carried:", list(row.carried_room_ids),
            "| Q:", row.carried_heat_W,
            "| flow:", (
                f"{row.carried_flow_kg_s:.6f}"
                if row.carried_flow_kg_s is not None
                else "—"
            ),
            "| status:", row.status,
        )

    assert basis.ready is True
    assert basis.status == "Branch-aware carried-flow basis ready"

    primary_rows = [
        row
        for row in basis.rows
        if row.subleg_id == "leg-001-primary-subleg"
    ]

    assert len(primary_rows) == 3

    # Primary section 1:
    # own rooms 002+003+004 = 900 W
    # true branch 005+006 = 1100 W
    # terminal continuation 007 = 700 W
    # early/riser branch 008 = 800 W
    # total = 3500 W
    assert primary_rows[0].carried_heat_W == 3500.0
    assert primary_rows[0].rolled_up_room_ids == (
        "room-005",
        "room-006",
        "room-007",
        "room-008",
    )
    assert abs(primary_rows[0].carried_flow_kg_s - _flow(3500.0)) < 1e-9
    assert "Early take-off / riser-capable branch" in primary_rows[0].status

    # Primary section 2:
    # own rooms 003+004 = 700 W
    # true branch 005+006 = 1100 W
    # terminal continuation 007 = 700 W
    # total = 2500 W
    assert primary_rows[1].carried_heat_W == 2500.0
    assert primary_rows[1].rolled_up_room_ids == (
        "room-005",
        "room-006",
        "room-007",
    )
    assert abs(primary_rows[1].carried_flow_kg_s - _flow(2500.0)) < 1e-9
    assert (
        "Late take-off — parent downstream terminal emitter only"
        in primary_rows[1].status
    )

    # Primary section 3:
    # own room 004 = 400 W
    # true branch is downstream of take-off, so not included
    # terminal continuation 007 is included
    # total = 1100 W
    assert primary_rows[2].carried_heat_W == 1100.0
    assert primary_rows[2].rolled_up_room_ids == ("room-007",)
    assert abs(primary_rows[2].carried_flow_kg_s - _flow(1100.0)) < 1e-9
    assert "Continuation from parent terminal" in primary_rows[2].status

    early_rows = [
        row
        for row in basis.rows
        if row.subleg_id == "leg-001-subleg-d"
    ]

    assert len(early_rows) == 1
    assert early_rows[0].subleg_kind == "branch subleg"
    assert early_rows[0].carried_heat_W == 800.0

    continuation_rows = [
        row
        for row in basis.rows
        if row.subleg_id == "leg-001-subleg-c"
    ]

    assert len(continuation_rows) == 1
    assert continuation_rows[0].subleg_kind == "continuation subleg"
    assert continuation_rows[0].carried_heat_W == 700.0

    print()
    print("OK — branch-aware carried-flow basis passed.")


if __name__ == "__main__":
    main()
