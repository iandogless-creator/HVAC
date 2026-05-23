# ======================================================================
# HVAC/dev/test_topology_arranger_projection.py
# ======================================================================

from __future__ import annotations

from HVAC.core.room_state import RoomStateV1
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.topology_arranger_projection_v1 import (
    build_topology_arranger_projection_v1,
)
from HVAC.project.project_state import ProjectState


def _room(room_id: str, name: str) -> RoomStateV1:
    return RoomStateV1(
        room_id=room_id,
        name=name,
    )


def main() -> None:
    project = ProjectState(
        project_id="dev-topology-arranger-projection",
        name="DEV Topology Arranger Projection",
    )

    project.rooms["room-001"] = _room("room-001", "Boiler / Heat Source")
    project.rooms["room-002"] = _room("room-002", "Hall")
    project.rooms["room-003"] = _room("room-003", "Kitchen")
    project.rooms["room-004"] = _room("room-004", "Lounge")
    project.rooms["room-005"] = _room("room-005", "Bedroom 1")
    project.rooms["room-006"] = _room("room-006", "Bathroom")

    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="room-001",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=[
                    "room-002",
                    "room-003",
                    "room-005",
                    "room-006",
                    "room-004",
                ],
                index_room_id="room-004",
            )
        ],
    )

    projection = build_topology_arranger_projection_v1(
        project,
        leg_id="leg-001",
    )

    print("\n======================================")
    print("Topology Arranger Projection V1")
    print("======================================")

    print(f"leg_id = {projection.leg_id}")
    print(f"leg_label = {projection.leg_label}")
    print(f"heat_source_room_id = {projection.heat_source_room_id}")
    print(f"selected_index_room_id = {projection.selected_index_room_id}")

    print("\nROWS")
    for row in projection.rows:
        markers: list[str] = []

        if row.is_index:
            markers.append("INDEX")

        if row.is_terminal:
            markers.append("TERMINAL")

        marker_text = f" [{' | '.join(markers)}]" if markers else ""

        print(
            f"{row.order:02d}. {row.room_id:<8} | "
            f"{row.label}{marker_text}"
        )

    assert projection.leg_id == "leg-001"
    assert projection.selected_index_room_id == "room-004"
    assert len(projection.rows) == 5

    assert projection.rows[0].room_id == "room-002"
    assert projection.rows[0].label == "Hall"
    assert projection.rows[0].order == 1
    assert projection.rows[0].is_index is False
    assert projection.rows[0].is_terminal is False

    assert projection.rows[-1].room_id == "room-004"
    assert projection.rows[-1].label == "Lounge"
    assert projection.rows[-1].is_index is True
    assert projection.rows[-1].is_terminal is True

    print("\nOK — topology arranger projection passed.")


if __name__ == "__main__":
    main()