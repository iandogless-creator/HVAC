# ======================================================================
# HVAC/dev/test_hydronic_topology_editor.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.hydronic_topology_editor_v1 import (
    HydronicTopologyEditorV1,
)


def _print_leg(topology: HydronicTopologyV1, leg_id: str) -> None:
    leg = HydronicTopologyEditorV1.require_leg(topology, leg_id)

    print(f"\n{leg.leg_id} | {leg.label}")
    print(f"index_room_id = {leg.index_room_id}")

    for order, room_id in enumerate(leg.route_room_ids, start=1):
        marker = " [INDEX]" if room_id == leg.index_room_id else ""
        print(f"{order:02d}. {room_id}{marker}")


def main() -> None:
    topology = HydronicTopologyV1(
        heat_source_room_id="room-001",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=[
                    "room-002",  # Hall
                    "room-003",  # Kitchen
                    "room-004",  # Lounge
                    "room-005",  # Bedroom 1
                    "room-006",  # Bathroom
                ],
                index_room_id="room-006",
            )
        ],
    )

    print("\n======================================")
    print("Hydronic Topology Editor V1")
    print("======================================")

    print("\nBEFORE")
    _print_leg(topology, "leg-001")

    HydronicTopologyEditorV1.move_room_to_leg_terminal(
        topology=topology,
        leg_id="leg-001",
        room_id="room-004",  # Lounge
        set_index=True,
    )

    print("\nAFTER — move Lounge to terminal/index")
    _print_leg(topology, "leg-001")

    leg = HydronicTopologyEditorV1.require_leg(topology, "leg-001")

    expected_route = [
        "room-002",
        "room-003",
        "room-005",
        "room-006",
        "room-004",
    ]

    assert leg.route_room_ids == expected_route
    assert leg.index_room_id == "room-004"
    HydronicTopologyEditorV1.move_room_up(
        topology=topology,
        leg_id="leg-001",
        room_id="room-004",  # Lounge
    )

    print("\nAFTER — move Lounge up one position")
    _print_leg(topology, "leg-001")

    assert leg.route_room_ids == [
        "room-002",
        "room-003",
        "room-005",
        "room-004",
        "room-006",
    ]

    HydronicTopologyEditorV1.move_room_down(
        topology=topology,
        leg_id="leg-001",
        room_id="room-004",  # Lounge
    )

    print("\nAFTER — move Lounge down one position")
    _print_leg(topology, "leg-001")

    assert leg.route_room_ids == [
        "room-002",
        "room-003",
        "room-005",
        "room-006",
        "room-004",
    ]
    print("\nOK — hydronic topology editor route movement passed.")


if __name__ == "__main__":
    main()