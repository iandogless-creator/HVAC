from __future__ import annotations

from HVAC.hydronics.topology.canonical_topology_validation_migration_v1 import (
    validate_canonical_hydronic_topology_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    REMOTE_HEAT_SOURCE_LOCATION_MODE_V1,
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    topology = HydronicTopologyV1(
        heat_source_room_id="",
        heat_source_location_mode=REMOTE_HEAT_SOURCE_LOCATION_MODE_V1,
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                sublegs=[
                    HydronicSublegV1(
                        subleg_id="leg-001-primary-subleg",
                        label="Principal subleg",
                        origin_room_id="common-main",
                        route_room_ids=["room-001", "room-002"],
                        index_room_id="room-002",
                    )
                ],
            )
        ],
    )
    routes_before = topology.all_route_room_ids()
    validation = validate_canonical_hydronic_topology_v1(
        topology,
        known_room_ids={"room-001", "room-002"},
    )
    assert validation.ready, validation.blockers

    project = ProjectState(
        project_id="hs68a2b2",
        name="Remote Heat Source no-room round-trip",
        hydronic_topology=topology,
    )
    restored = ProjectState.from_dict(project.to_dict())
    restored_topology = restored.hydronic_topology
    assert restored_topology is not None
    assert restored_topology.heat_source_location_mode == "remote"
    assert restored_topology.heat_source_room_id == ""
    assert restored_topology.all_route_room_ids() == routes_before

    # The topology has no host-room reference; no ProjectState room deletion
    # or route mutation is part of this persistence contract.
    assert restored_topology.contains_room_id("room-001")
    assert not restored_topology.contains_room_id("room-boiler")

    print(
        "OK — H-S68-A2B2 remote Heat Source persists with no room "
        "assignment; canonical routes remain unchanged and no room deletion "
        "is inferred."
    )


if __name__ == "__main__":
    main()
