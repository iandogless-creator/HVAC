# ======================================================================
# HVAC/dev/test_basic_ps_uses_branch_aware_flow_basis_v1.py
# H-S24-F — Basic PS uses branch-aware carried-flow basis
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    build_basic_ps_topology_sections_v1,
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


def _expected_flow(output_W: float) -> float:
    return output_W / (4180.0 * 10.0)


def _build_project() -> ProjectState:
    project = ProjectState(
        project_id="dev-hs24f-basic-ps-branch-aware",
        name="DEV H-S24-F Basic PS Branch Aware",
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

    projection = build_basic_ps_topology_sections_v1(
        project,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
    )

    print()
    print("H-S24-F — Basic PS uses branch-aware carried-flow basis")
    print("=======================================================")
    print("status:", projection.status)

    for section in projection.sections:
        print(
            section.section_id,
            "| downstream:", list(section.downstream_room_ids),
            "| Q:", section.carried_heat_W,
            "| flow:", f"{section.carried_flow_kg_s:.6f}",
            "| status:", section.status,
        )

    assert len(projection.sections) == 3

    first, second, third = projection.sections

    assert first.carried_heat_W == 3500.0
    assert first.downstream_room_ids == (
        "room-002",
        "room-003",
        "room-004",
        "room-005",
        "room-006",
        "room-007",
        "room-008",
    )
    assert abs(first.carried_flow_kg_s - _expected_flow(3500.0)) < 1e-9

    assert second.carried_heat_W == 2500.0
    assert second.downstream_room_ids == (
        "room-003",
        "room-004",
        "room-005",
        "room-006",
        "room-007",
    )
    assert abs(second.carried_flow_kg_s - _expected_flow(2500.0)) < 1e-9

    assert third.carried_heat_W == 1100.0
    assert third.downstream_room_ids == (
        "room-004",
        "room-007",
    )
    assert abs(third.carried_flow_kg_s - _expected_flow(1100.0)) < 1e-9

    assert all(
        "Branch-aware carried-flow basis" in section.status
        for section in projection.sections
    )

    print()
    print("OK — Basic PS branch-aware carried-flow integration passed.")


if __name__ == "__main__":
    main()
