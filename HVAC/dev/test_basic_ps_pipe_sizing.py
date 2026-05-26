# ======================================================================
# HVAC/dev/test_basic_ps_pipe_sizing.py
# ======================================================================

from __future__ import annotations

from HVAC.dev.test_basic_ps_topology_sections import (
    _emitter,
    _room,
)
from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    build_basic_ps_pipe_sizing_v1,
)
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


def main() -> None:
    project = ProjectState(
        project_id="dev-basic-ps-pipe-sizing",
        name="DEV Basic PS Pipe Sizing",
    )

    project.rooms["room-001"] = _room("room-001", "Boiler / Heat Source")
    project.rooms["room-002"] = _room("room-002", "Hall")
    project.rooms["room-003"] = _room("room-003", "Kitchen")
    project.rooms["room-004"] = _room("room-004", "Lounge")
    project.rooms["room-005"] = _room("room-005", "Bedroom 1")
    project.rooms["room-006"] = _room("room-006", "Bathroom")

    route_room_ids = [
        "room-002",
        "room-003",
        "room-004",
        "room-005",
        "room-006",
    ]

    subleg_id = primary_subleg_id_for_leg("leg-001")

    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="room-001",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=list(route_room_ids),
                index_room_id="room-006",
                sublegs=[
                    HydronicSublegV1(
                        subleg_id=subleg_id,
                        label="Primary subleg",
                        origin_room_id="",
                        route_room_ids=list(route_room_ids),
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

    sections_projection = build_basic_ps_topology_sections_v1(
        project,
        leg_id="leg-001",
        design_delta_t_K=20.0,
    )

    sizing_projection = build_basic_ps_pipe_sizing_v1(
        sections_projection.sections,
    )

    print("\n======================================")
    print("Basic PS Pipe Sizing V1")
    print("======================================")

    print("\nRESULTS")
    for result in sizing_projection.results:
        markers: list[str] = []

        if result.is_index_room:
            markers.append("INDEX")

        if result.is_terminal:
            markers.append("TERMINAL")

        marker_text = f" [{' | '.join(markers)}]" if markers else ""

        print(
            f"{result.order:02d}. "
            f"{result.from_label} -> {result.to_room_label:<10} | "
            f"Q={result.carried_heat_W:.1f} W | "
            f"flow={result.carried_flow_kg_s:.4f} kg/s | "
            f"pipe={result.pipe_size_label:<5} | "
            f"v={result.velocity_m_s:.3f} m/s | "
            f"Re={result.reynolds_number:.0f} | "
            f"f={result.friction_factor:.4f} | "
            f"Pa/m={result.pressure_gradient_Pa_per_m:.1f} | "
            f"{result.status}"
            f"{marker_text}"
        )

    assert len(sizing_projection.results) == 5

    first = sizing_projection.results[0]
    last = sizing_projection.results[-1]

    assert first.carried_heat_W == 2800.0
    assert first.carried_flow_kg_s > 0.0
    assert first.velocity_m_s > 0.0
    assert first.reynolds_number > 0.0
    assert first.pressure_gradient_Pa_per_m > 0.0

    assert last.is_index_room is True
    assert last.is_terminal is True
    assert last.carried_heat_W == 300.0

    print("\nOK — basic PS pipe sizing passed.")


if __name__ == "__main__":
    main()