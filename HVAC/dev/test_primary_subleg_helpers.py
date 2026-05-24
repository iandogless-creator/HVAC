# ======================================================================
# HVAC/dev/test_primary_subleg_helpers.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    ensure_primary_sublegs_for_topology,
    primary_route_room_ids_for_leg,
    primary_subleg_for_leg_id,
    set_primary_index_room_id_for_leg,
    set_primary_route_room_ids_for_leg,
)


def main() -> None:
    topology = HydronicTopologyV1(
        heat_source_room_id="room-001",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=[
                    "room-002",
                    "room-003",
                    "room-004",
                ],
                index_room_id="room-004",
                sublegs=[],
            )
        ],
    )

    print("\n======================================")
    print("Primary Subleg Helpers V1")
    print("======================================")

    ensure_primary_sublegs_for_topology(topology)

    primary = primary_subleg_for_leg_id(topology, "leg-001")

    print(f"primary.subleg_id = {primary.subleg_id}")
    print(f"primary.label = {primary.label}")
    print(f"primary.route_room_ids = {primary.route_room_ids}")
    print(f"primary.index_room_id = {primary.index_room_id}")

    assert primary.subleg_id == "leg-001-primary-subleg"
    assert primary.label == "Primary subleg"
    assert primary.route_room_ids == ["room-002", "room-003", "room-004"]
    assert primary.index_room_id == "room-004"

    assert primary_route_room_ids_for_leg(topology, "leg-001") == [
        "room-002",
        "room-003",
        "room-004",
    ]

    set_primary_route_room_ids_for_leg(
        topology,
        "leg-001",
        ["room-003", "room-002", "room-004"],
    )

    print(
        "after route set, primary.route_room_ids =",
        primary_route_room_ids_for_leg(topology, "leg-001"),
    )

    assert primary_route_room_ids_for_leg(topology, "leg-001") == [
        "room-003",
        "room-002",
        "room-004",
    ]

    # Transitional compatibility mirror.
    leg = topology.legs[0]
    assert leg.route_room_ids == [
        "room-003",
        "room-002",
        "room-004",
    ]

    set_primary_index_room_id_for_leg(
        topology,
        "leg-001",
        "room-003",
    )

    primary = primary_subleg_for_leg_id(topology, "leg-001")

    print(f"after index set, primary.index_room_id = {primary.index_room_id}")
    print(f"after index set, legacy leg.index_room_id = {leg.index_room_id}")

    assert primary.index_room_id == "room-003"
    assert leg.index_room_id == "room-003"

    print("\nOK — primary subleg helpers passed.")


if __name__ == "__main__":
    main()