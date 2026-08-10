from __future__ import annotations

from HVAC.core.room_state import RoomGeometryV1, RoomStateV1
from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.topology.canonical_topology_validation_migration_v1 import (
    migrate_legacy_flat_sublegs_to_canonical_v1,
)
from HVAC.hydronics.topology.topology_unassigned_room_inventory_v1 import (
    ASSIGNED_TOPOLOGY_DISPOSITION,
    FIXED_HEAT_SOURCE_DISPOSITION,
    UNASSIGNED_STAGING_DISPOSITION,
    build_topology_unassigned_room_inventory_v1,
)


def main() -> None:
    project = build_hydronic_20_room_multileg_project_v1()

    baseline = build_topology_unassigned_room_inventory_v1(project)
    assert baseline.ready, baseline.blockers
    assert baseline.migration_projection_used
    assert baseline.fixed_heat_source is not None
    assert baseline.fixed_heat_source.room_id == "room-boiler"
    assert baseline.fixed_heat_source.disposition == FIXED_HEAT_SOURCE_DISPOSITION
    assert len(baseline.assigned_rooms) == 20
    assert baseline.staging_rooms == ()

    exact_branch_room = baseline.require_room("room-l1b-001")
    assert exact_branch_room.disposition == ASSIGNED_TOPOLOGY_DISPOSITION
    assert exact_branch_room.leg_id == "leg-001"
    assert exact_branch_room.subleg_id == "leg-001-subleg-b"
    assert exact_branch_room.subleg_kind == "branch"
    assert exact_branch_room.route_order == 1

    project.rooms["room-future-001"] = RoomStateV1(
        room_id="room-future-001",
        name="Future Study",
        geometry=RoomGeometryV1(length_m=3.0, width_m=2.5, height_m=2.4),
    )
    with_new_room = build_topology_unassigned_room_inventory_v1(project)
    assert with_new_room.ready, with_new_room.blockers
    assert with_new_room.staging_room_ids == ("room-future-001",)
    staged = with_new_room.require_room("room-future-001")
    assert staged.disposition == UNASSIGNED_STAGING_DISPOSITION
    assert staged.room_label == "Future Study"

    project.rooms["room-future-001"].name = "Renamed Future Study"
    renamed = build_topology_unassigned_room_inventory_v1(project)
    assert renamed.require_room("room-future-001").room_label == (
        "Renamed Future Study"
    )

    migration = migrate_legacy_flat_sublegs_to_canonical_v1(
        project.hydronic_topology,
        known_room_ids=project.rooms,
    )
    assert migration.ready and migration.topology is not None
    project.hydronic_topology = migration.topology
    branch = project.hydronic_topology.legs[1].sublegs[0].sublegs[0]
    removed_room_id = branch.route_room_ids.pop()
    branch.index_room_id = branch.route_room_ids[-1]
    returned = build_topology_unassigned_room_inventory_v1(project)
    assert returned.ready, returned.blockers
    assert not returned.migration_projection_used
    assert set(returned.staging_room_ids) == {
        "room-future-001",
        removed_room_id,
    }

    duplicate_project = build_hydronic_20_room_multileg_project_v1()
    duplicate_project.hydronic_topology.legs[1].sublegs[0].route_room_ids.append(
        "room-l1a-001"
    )
    duplicate = build_topology_unassigned_room_inventory_v1(duplicate_project)
    assert not duplicate.ready
    assert "allocated to both" in " ".join(duplicate.blockers).lower()

    print(
        "OK — H-S67-G1 derives fixed, exact assigned and neutral staging "
        "room dispositions without separate persistence."
    )


if __name__ == "__main__":
    main()
