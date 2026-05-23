# ======================================================================
# HVAC/dev/test_dev_hydronic_topology_builder.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.room_state import RoomStateV1
from HVAC.hydronics.topology.dev_hydronic_topology_builder_v1 import (
    DevHydronicTopologyBuilderV1,
)


def _room(room_id: str, label: str) -> RoomStateV1:
    return RoomStateV1(
        room_id=room_id,
        name=label,
    )


def main() -> None:
    project = ProjectState(
        project_id="dev-hydronic-topology-test",
        name="DEV Hydronic Topology Test",
    )

    project.rooms["room-001"] = _room("room-001", "Boiler / Heat Source")
    project.rooms["room-002"] = _room("room-002", "Bathroom")
    project.rooms["room-003"] = _room("room-003", "Bedroom 1")
    project.rooms["room-004"] = _room("room-004", "Lounge")
    project.rooms["room-005"] = _room("room-005", "Kitchen")
    project.rooms["room-006"] = _room("room-006", "Hall")

    topology = DevHydronicTopologyBuilderV1.install_single_leg_on_project(
        project,
        heat_source_room_id="room-001",
        overwrite=True,
    )

    print("\n==============================")
    print("DEV Hydronic Topology Builder")
    print("==============================\n")

    print(f"heat_source_room_id = {topology.heat_source_room_id}")

    for leg in topology.legs:
        print(f"\n{leg.leg_id} | {leg.label}")
        print(f"index_room_id = {leg.index_room_id}")

        for order, room_id in enumerate(leg.route_room_ids, start=1):
            room = project.rooms.get(room_id)
            label = getattr(room, "name", room_id)
            index_marker = " [INDEX]" if room_id == leg.index_room_id else ""
            print(f"{order:02d}. {room_id} | {label}{index_marker}")

    print("\nall_route_room_ids =", topology.all_route_room_ids())
    print("contains room-001 =", topology.contains_room_id("room-001"))
    print("contains room-006 =", topology.contains_room_id("room-006"))


if __name__ == "__main__":
    main()