from __future__ import annotations

from HVAC.hydronics.topology.canonical_topology_validation_migration_v1 import (
    validate_canonical_hydronic_topology_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    REMOTE_HEAT_SOURCE_LOCATION_MODE_V1,
    SERVED_ROOM_HEAT_SOURCE_LOCATION_MODE_V1,
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
# Persisted canonical origin token used by the topology contract.
COMMON_MAIN_ORIGIN_ID = "common-main"


def _topology(mode: str) -> HydronicTopologyV1:
    return HydronicTopologyV1(
        heat_source_room_id="room-host",
        heat_source_location_mode=mode,
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                sublegs=[
                    HydronicSublegV1(
                        subleg_id="leg-001-primary-subleg",
                        label="Principal subleg",
                        origin_room_id=COMMON_MAIN_ORIGIN_ID,
                        route_room_ids=["room-host", "room-terminal"],
                        index_room_id="room-terminal",
                    )
                ],
            )
        ],
    )


def main() -> None:
    known_rooms = {"room-host", "room-terminal"}

    remote = _topology(REMOTE_HEAT_SOURCE_LOCATION_MODE_V1)
    remote_routes_before = remote.all_route_room_ids()
    remote_validation = validate_canonical_hydronic_topology_v1(
        remote,
        known_room_ids=known_rooms,
    )
    assert not remote_validation.ready
    assert any(
        "heat-source room cannot be a served route room" in blocker
        for blocker in remote_validation.blockers
    )
    assert remote.all_route_room_ids() == remote_routes_before

    remote_no_host = _topology(REMOTE_HEAT_SOURCE_LOCATION_MODE_V1)
    remote_no_host.heat_source_room_id = ""
    remote_no_host_routes = remote_no_host.all_route_room_ids()
    remote_no_host_validation = validate_canonical_hydronic_topology_v1(
        remote_no_host,
        known_room_ids=known_rooms,
    )
    assert remote_no_host_validation.ready, (
        remote_no_host_validation.blockers
    )
    assert remote_no_host.all_route_room_ids() == remote_no_host_routes

    served = _topology(SERVED_ROOM_HEAT_SOURCE_LOCATION_MODE_V1)
    served_routes_before = served.all_route_room_ids()
    served_validation = validate_canonical_hydronic_topology_v1(
        served,
        known_room_ids=known_rooms,
    )
    assert served_validation.ready, served_validation.blockers
    assert served.all_route_room_ids() == served_routes_before

    saved = served.to_dict()
    assert saved["heat_source_location_mode"] == "served_room"
    loaded = HydronicTopologyV1.from_dict(saved)
    assert loaded.heat_source_location_mode == "served_room"
    assert loaded.all_route_room_ids() == served_routes_before

    legacy = dict(saved)
    legacy.pop("heat_source_location_mode")
    legacy_loaded = HydronicTopologyV1.from_dict(legacy)
    assert legacy_loaded.heat_source_location_mode == "remote"

    invalid = dict(saved)
    invalid["heat_source_location_mode"] = "cupboard"
    try:
        HydronicTopologyV1.from_dict(invalid)
    except ValueError as exc:
        assert "Unknown Heat Source location mode" in str(exc)
    else:
        raise AssertionError("Unknown Heat Source location mode was accepted")

    served.heat_source_location_mode = "cupboard"
    invalid_validation = validate_canonical_hydronic_topology_v1(
        served,
        known_room_ids=known_rooms,
    )
    assert not invalid_validation.ready
    assert any(
        "Unknown Heat Source location mode" in blocker
        for blocker in invalid_validation.blockers
    )

    print(
        "OK — H-S68-A2A persists explicit remote/served-room Heat Source "
        "location semantics; legacy topology remains remote, canonical "
        "validation is conditional and no route membership is mutated."
    )


if __name__ == "__main__":
    main()
