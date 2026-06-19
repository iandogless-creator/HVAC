# ======================================================================
# HVAC/dev/test_basic_ps_environment_delta_t_v1.py
# H-S21-B — Environment flow/return drives Basic PS mass-flow basis
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    build_basic_ps_topology_sections_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)
from HVAC.project.project_state import ProjectState


def _room(room_id: str, name: str) -> RoomStateV1:
    return RoomStateV1(
        room_id=room_id,
        name=name,
    )


def _emitter(
    emitter_id: str,
    room_id: str,
    heat_W: float,
) -> EmitterV1:
    emitter = EmitterV1(
        emitter_id=emitter_id,
        room_id=room_id,
    )

    for attr_name in (
        "design_heat_output_W",
        "design_output_W",
        "nominal_output_W",
        "heat_output_W",
        "output_W",
        "design_heat_W",
        "load_W",
        "design_load_W",
        "q_W",
        "heat_W",
        "watts",
    ):
        if hasattr(emitter, attr_name):
            setattr(emitter, attr_name, heat_W)
            return emitter

    raise AttributeError(
        "EmitterV1 has no recognised heat-output field for DEV test"
    )


def _build_project() -> ProjectState:
    project = ProjectState(
        project_id="dev-basic-ps-environment-delta-t",
        name="DEV Basic PS Environment Delta T",
    )

    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
        design_flow_temp_c=75.0,
        design_return_temp_c=65.0,
    )

    project.rooms["room-001"] = _room("room-001", "Boiler / Heat Source")
    project.rooms["room-002"] = _room("room-002", "Hall")
    project.rooms["room-003"] = _room("room-003", "Kitchen")
    project.rooms["room-004"] = _room("room-004", "Lounge")
    project.rooms["room-005"] = _room("room-005", "Bedroom 1")
    project.rooms["room-006"] = _room("room-006", "Bathroom")

    subleg_id = primary_subleg_id_for_leg("leg-001")

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
                    "room-005",
                    "room-006",
                ],
                index_room_id="room-006",
                sublegs=[
                    HydronicSublegV1(
                        subleg_id=subleg_id,
                        label="Primary subleg",
                        origin_room_id="",
                        route_room_ids=[
                            "room-002",
                            "room-003",
                            "room-004",
                            "room-005",
                            "room-006",
                        ],
                        index_room_id="room-006",
                        sublegs=[],
                    )
                ],
            )
        ],
    )

    project.emitters["emitter-hall"] = _emitter(
        "emitter-hall",
        "room-002",
        400.0,
    )
    project.emitters["emitter-kitchen"] = _emitter(
        "emitter-kitchen",
        "room-003",
        600.0,
    )
    project.emitters["emitter-lounge"] = _emitter(
        "emitter-lounge",
        "room-004",
        1000.0,
    )
    project.emitters["emitter-bedroom-1"] = _emitter(
        "emitter-bedroom-1",
        "room-005",
        500.0,
    )
    project.emitters["emitter-bathroom"] = _emitter(
        "emitter-bathroom",
        "room-006",
        300.0,
    )

    return project


def main() -> None:
    project = _build_project()

    projection = build_basic_ps_topology_sections_v1(
        project,
        leg_id="leg-001",
    )

    first = projection.sections[0]

    expected_delta_t_K = 10.0
    expected_flow_kg_s = first.carried_heat_W / (
        4180.0 * expected_delta_t_K
    )

    print("\n======================================")
    print("Basic PS Environment ΔT Test")
    print("======================================")
    print(f"design_delta_t_K = {projection.design_delta_t_K}")
    print(f"first carried_heat_W = {first.carried_heat_W:.1f} W")
    print(f"first carried_flow_kg_s = {first.carried_flow_kg_s:.6f} kg/s")
    print(f"expected_flow_kg_s = {expected_flow_kg_s:.6f} kg/s")

    assert projection.design_delta_t_K == expected_delta_t_K
    assert abs(first.carried_flow_kg_s - expected_flow_kg_s) < 1e-12

    print("\nOK — Environment flow/return drives Basic PS mass-flow basis.")


if __name__ == "__main__":
    main()
