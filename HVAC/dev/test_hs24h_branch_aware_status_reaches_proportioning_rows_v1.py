# ======================================================================
# HVAC/dev/test_hs24h_branch_aware_status_reaches_proportioning_rows_v1.py
# H-S24-H — Surface branch-aware basis in Proportioning UI rows
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
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
        project_id="dev-hs24h-ui-status",
        name="DEV H-S24-H UI Status",
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

    projection = build_basic_ps_readonly_projection_v1(
        project,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
        section_lengths_m={
            "leg-001-primary-subleg-section-001": 1.0,
            "leg-001-primary-subleg-section-002": 1.0,
            "leg-001-primary-subleg-section-003": 1.0,
        },
    )

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = project

    rows = adapter._build_proportioning_basic_ps_sections(projection)

    print()
    print("H-S24-H — Branch-aware basis shown in Proportioning rows")
    print("========================================================")

    for row in rows:
        print(
            row["section_id"],
            "| Q:", row["q_carried"],
            "| flow:", row["flow_kg_s"],
            "| status:", row["status"],
        )

    assert len(rows) == 3

    first_status = rows[0]["status"]
    second_status = rows[1]["status"]
    third_status = rows[2]["status"]

    assert "Branch-aware carried-flow basis" in first_status
    assert "Early take-off / riser-capable branch" in first_status
    assert "Late take-off — parent downstream terminal emitter only" in first_status
    assert "Continuation from parent terminal" in first_status

    assert "Branch-aware carried-flow basis" in second_status
    assert "Downstream of branch take-off" in second_status

    assert "Branch-aware carried-flow basis" in third_status
    assert "Continuation from parent terminal" in third_status

    assert rows[0]["q_carried"] == "3500.0 W"
    assert rows[1]["q_carried"] == "2500.0 W"
    assert rows[2]["q_carried"] == "1100.0 W"

    print()
    print("OK — branch-aware status reaches Proportioning Basic PS rows.")


if __name__ == "__main__":
    main()
