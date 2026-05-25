# ======================================================================
# HVAC/dev/test_basic_ps_topology_sections.py
# ======================================================================

from __future__ import annotations

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
    return emitter


def main() -> None:
    project = ProjectState(
        project_id="dev-basic-ps-topology-sections",
        name="DEV Basic PS Topology Sections",
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

    projection = build_basic_ps_topology_sections_v1(
        project,
        leg_id="leg-001",
        design_delta_t_K=20.0,
    )

    print("\n======================================")
    print("Basic PS Topology Sections V1")
    print("======================================")

    print(f"leg_id = {projection.leg_id}")
    print(f"subleg_id = {projection.subleg_id}")
    print(f"design_delta_t_K = {projection.design_delta_t_K}")

    print("\nSECTIONS")
    for section in projection.sections:
        markers: list[str] = []

        if section.is_index_room:
            markers.append("INDEX")

        if section.is_terminal:
            markers.append("TERMINAL")

        marker_text = f" [{' | '.join(markers)}]" if markers else ""

        print(
            f"{section.order:02d}. "
            f"{section.from_label} -> {section.to_room_label:<10} | "
            f"downstream={list(section.downstream_room_ids)} | "
            f"emitters={list(section.downstream_emitter_ids)} | "
            f"Q={section.carried_heat_W:.1f} W | "
            f"flow={section.carried_flow_kg_s:.4f} kg/s"
            f"{marker_text}"
        )

    assert len(projection.sections) == 5

    assert projection.sections[0].from_label == "Common main / leg entry"
    assert projection.sections[0].to_room_id == "room-002"
    assert projection.sections[0].carried_heat_W == 2800.0

    assert projection.sections[1].to_room_id == "room-003"
    assert projection.sections[1].carried_heat_W == 2400.0

    assert projection.sections[2].to_room_id == "room-004"
    assert projection.sections[2].carried_heat_W == 1800.0

    assert projection.sections[3].to_room_id == "room-005"
    assert projection.sections[3].carried_heat_W == 800.0

    assert projection.sections[4].to_room_id == "room-006"
    assert projection.sections[4].carried_heat_W == 300.0
    assert projection.sections[4].is_index_room is True
    assert projection.sections[4].is_terminal is True

    print("\nOK — basic PS topology section projection passed.")


if __name__ == "__main__":
    main()