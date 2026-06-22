# ======================================================================
# HVAC/dev/test_hs25b_branch_aware_audit_replaces_branch_summary_ui_v1.py
# H-S25-B — Surface branch-aware route authority audit in UI table slot
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.proportioning.branch_aware_route_summary_audit_v1 import (
    build_branch_aware_route_summary_audit_v1,
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
        project_id="dev-hs25b-ui-audit",
        name="DEV H-S25-B UI Audit",
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

    branch = HydronicSublegV1(
        subleg_id="leg-001-subleg-b",
        label="Leg 1B Branch subleg",
        origin_room_id="room-003",
        route_room_ids=["room-005", "room-006"],
        index_room_id="room-006",
    )

    continuation = HydronicSublegV1(
        subleg_id="leg-001-subleg-c",
        label="Leg 1C Terminal continuation",
        origin_room_id="room-004",
        route_room_ids=["room-007"],
        index_room_id="room-007",
    )

    early = HydronicSublegV1(
        subleg_id="leg-001-subleg-d",
        label="Leg 1D Early riser branch",
        origin_room_id="room-002",
        route_room_ids=["room-008"],
        index_room_id="room-008",
    )

    primary.sublegs.append(branch)
    primary.sublegs.append(continuation)
    primary.sublegs.append(early)

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
    audit = build_branch_aware_route_summary_audit_v1(project)

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )

    rows = adapter._build_proportioning_rows(audit)

    print()
    print("H-S25-B — Branch-aware audit surfaced in UI summary slot")
    print("=======================================================")

    for row in rows:
        print(
            row["group"],
            "|",
            row["role"],
            "| from:",
            row["from"],
            "| to:",
            row["to"],
            "| flow:",
            row["flow"],
            "| basis:",
            row["basis"],
            "| status:",
            row["status"],
        )

    assert len(rows) == 4

    primary = rows[0]
    assert primary["group"] == "Heating Leg 1"
    assert primary["role"] == "primary/common subleg"
    assert primary["from"] == "Common main / leg entry"
    assert primary["to"] == "Leg 1A Common subleg"
    assert primary["flow"] == "0.0837 kg/s"
    assert "entry Q 3500.0 W" in primary["basis"]
    assert "entry rooms 7" in primary["basis"]
    assert "Topology and Basic PS agree" in primary["status"]

    branch_rows = [row for row in rows if row["role"] == "branch subleg"]
    assert len(branch_rows) == 2

    assert any(
        "Late take-off — parent downstream terminal emitter only" in row["basis"]
        for row in branch_rows
    )

    assert any(
        "Early take-off / riser-capable branch" in row["basis"]
        for row in branch_rows
    )

    continuation_rows = [
        row for row in rows if row["role"] == "continuation subleg"
    ]
    assert len(continuation_rows) == 1
    assert "Continuation from parent terminal" in continuation_rows[0]["basis"]

    print()
    print("OK — branch-aware audit replaces old branch summary UI content.")


if __name__ == "__main__":
    main()
