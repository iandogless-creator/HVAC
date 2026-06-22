# ======================================================================
# HVAC/dev/test_branch_takeoff_room_allocation_basis_v1.py
# H-S24-B — Branch take-off / room allocation basis test
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.branch_takeoff_room_allocation_basis_v1 import (
    build_branch_takeoff_room_allocation_basis_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    project = ProjectState(
        project_id="dev-hs24b-branch-takeoff-basis",
        name="DEV H-S24-B Branch Take-off Basis",
    )

    primary = HydronicSublegV1(
        subleg_id="leg-001-primary-subleg",
        label="Leg 1A Common subleg",
        origin_room_id="room-001",
        route_room_ids=[
            "room-002",
            "room-003",
            "room-004",
        ],
        index_room_id="room-004",
    )

    branch = HydronicSublegV1(
        subleg_id="leg-001-subleg-b",
        label="Leg 1B Branch subleg",
        origin_room_id="room-003",
        route_room_ids=[
            "room-005",
            "room-006",
        ],
        index_room_id="room-006",
    )

    primary.sublegs.append(branch)

    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="room-001",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=[
                    "room-002",
                    "room-003",
                    "room-004",
                ],
                index_room_id="room-004",
                sublegs=[primary],
            )
        ],
    )

    basis = build_branch_takeoff_room_allocation_basis_v1(project)

    print()
    print("H-S24-B — Branch take-off / room allocation basis")
    print("=================================================")
    print("ready:", basis.ready)
    print("status:", basis.status)

    for row in basis.rows:
        print(
            row.leg_id,
            "|",
            row.subleg_id,
            "| kind:",
            row.subleg_kind,
            "| parent:",
            row.parent_subleg_id or "—",
            "| take-off:",
            row.takeoff_room_id or "—",
            "| rooms:",
            list(row.ordered_room_ids),
            "| terminal:",
            row.terminal_room_id or "—",
            "| status:",
            row.status,
        )

    assert basis.ready is True
    assert basis.status == "Branch take-off / room allocation basis ready"
    assert len(basis.rows) == 2

    primary_row = basis.rows[0]
    assert primary_row.subleg_id == "leg-001-primary-subleg"
    assert primary_row.subleg_kind == "primary/common subleg"
    assert primary_row.parent_subleg_id == ""
    assert primary_row.takeoff_basis == "common main / leg entry"
    assert primary_row.room_count == 3
    assert primary_row.terminal_room_id == "room-004"
    assert primary_row.status == "Primary subleg room allocation ready"

    branch_row = basis.rows[1]
    assert branch_row.subleg_id == "leg-001-subleg-b"
    assert branch_row.subleg_kind == "branch subleg"
    assert branch_row.parent_subleg_id == "leg-001-primary-subleg"
    assert branch_row.takeoff_room_id == "room-003"
    assert branch_row.takeoff_basis == "origin_room_id / branch take-off basis"
    assert branch_row.ordered_room_ids == ("room-005", "room-006")
    assert branch_row.terminal_room_id == "room-006"
    assert branch_row.status == "Branch take-off basis ready"

    print()
    print("OK — branch take-off / room allocation basis passed.")


if __name__ == "__main__":
    main()
