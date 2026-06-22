# ======================================================================
# HVAC/dev/test_branch_aware_route_summary_audit_v1.py
# H-S25-A — Branch-aware route summary / topology authority audit
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
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


def _flow(output_W: float) -> float:
    return output_W / (4180.0 * 10.0)


def main() -> None:
    project = ProjectState(
        project_id="dev-hs25a-branch-aware-route-audit",
        name="DEV H-S25-A Branch Aware Route Audit",
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

    audit = build_branch_aware_route_summary_audit_v1(project)

    print()
    print("H-S25-A — Branch-aware route summary / topology authority audit")
    print("==============================================================")
    print("ready:", audit.ready)
    print("status:", audit.status)

    for row in audit.rows:
        print(
            row.leg_id,
            "|",
            row.subleg_id,
            "| role:",
            row.role,
            "| parent:",
            row.parent_subleg_id or "—",
            "| origin:",
            row.origin_room_id or "—",
            "| class:",
            row.takeoff_classification,
            "| route rooms:",
            list(row.route_room_ids),
            "| entry rooms:",
            list(row.entry_carried_room_ids),
            "| entry Q:",
            row.entry_carried_heat_W,
            "| entry flow:",
            (
                f"{row.entry_carried_flow_kg_s:.6f}"
                if row.entry_carried_flow_kg_s is not None
                else "—"
            ),
            "| matches Basic PS:",
            row.basic_ps_matches_branch_aware,
            "| status:",
            row.status,
        )

    assert audit.ready is True
    assert audit.status == "Branch-aware route summary audit ready"
    assert len(audit.rows) == 4

    rows = {row.subleg_id: row for row in audit.rows}

    primary_row = rows["leg-001-primary-subleg"]
    assert primary_row.role == "primary/common subleg"
    assert primary_row.entry_carried_heat_W == 3500.0
    assert abs(primary_row.entry_carried_flow_kg_s - _flow(3500.0)) < 1e-9
    assert primary_row.basic_ps_matches_branch_aware is True

    late = rows["leg-001-subleg-b"]
    assert late.role == "branch subleg"
    assert late.parent_subleg_id == "leg-001-primary-subleg"
    assert late.takeoff_classification == (
        "Late take-off — parent downstream terminal emitter only"
    )
    assert late.entry_carried_heat_W == 1100.0
    assert abs(late.entry_carried_flow_kg_s - _flow(1100.0)) < 1e-9
    assert late.basic_ps_matches_branch_aware is True

    continuation = rows["leg-001-subleg-c"]
    assert continuation.role == "continuation subleg"
    assert continuation.takeoff_classification == "Continuation from parent terminal"
    assert continuation.entry_carried_heat_W == 700.0
    assert continuation.basic_ps_matches_branch_aware is True

    early = rows["leg-001-subleg-d"]
    assert early.role == "branch subleg"
    assert early.takeoff_classification == "Early take-off / riser-capable branch"
    assert early.entry_carried_heat_W == 800.0
    assert early.basic_ps_matches_branch_aware is True

    print()
    print("OK — branch-aware route summary / topology authority audit passed.")


if __name__ == "__main__":
    main()
