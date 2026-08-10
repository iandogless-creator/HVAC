from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.core.room_state import RoomGeometryV1, RoomStateV1
from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.topology.topology_creation_candidate_v1 import (
    build_add_leg_with_principal_candidate_v1,
)
from HVAC.hydronics.topology.topology_room_placement_candidate_v1 import (
    PLACE_FROM_STAGING_ACTION,
    REORDER_WITHIN_SUBLEG_ACTION,
    RETURN_TO_STAGING_ACTION,
    TRANSFER_BETWEEN_SUBLEGS_ACTION,
    build_place_topology_room_candidate_v1,
    build_return_topology_room_to_staging_candidate_v1,
)
from HVAC.hydronics.topology.topology_unassigned_room_inventory_v1 import (
    build_topology_unassigned_room_inventory_v1,
)
from HVAC.hydronics.topology.transactional_topology_editor_v1 import (
    FOCUS_STAGING_ROOM,
    TOPOLOGY_STEPBACK_DIRECTORY,
    commit_validated_topology_candidate_v1,
)


def main() -> None:
    project = build_hydronic_20_room_multileg_project_v1()
    original = project.hydronic_topology.to_dict()

    reorder = build_place_topology_room_candidate_v1(
        project,
        room_id="room-l1a-001",
        target_subleg_id="leg-001-primary-subleg",
        target_order=3,
    )
    assert reorder.ready and reorder.changed, reorder.blockers
    assert reorder.action == REORDER_WITHIN_SUBLEG_ACTION
    assert reorder.target_order == 3
    assert reorder.topology.legs[0].sublegs[0].route_room_ids[:3] == [
        "room-l1a-002",
        "room-l1a-003",
        "room-l1a-001",
    ]
    assert project.hydronic_topology.to_dict() == original

    transfer = build_place_topology_room_candidate_v1(
        project,
        room_id="room-l2b-004",
        target_subleg_id="leg-001-subleg-b",
        target_order=2,
    )
    assert transfer.ready and transfer.changed, transfer.blockers
    assert transfer.action == TRANSFER_BETWEEN_SUBLEGS_ACTION
    target = transfer.topology.legs[0].sublegs[0].sublegs[0]
    assert target.route_room_ids[1] == "room-l2b-004"

    takeoff_move = build_place_topology_room_candidate_v1(
        project,
        room_id="room-l1a-002",
        target_subleg_id="leg-002-primary-subleg",
    )
    assert not takeoff_move.ready
    assert "dependent branch" in " ".join(takeoff_move.blockers).lower()

    plant_move = build_return_topology_room_to_staging_candidate_v1(
        project,
        room_id="room-boiler",
    )
    assert not plant_move.ready
    assert "plant/heat source" in " ".join(plant_move.blockers).lower()

    project.rooms["room-future-001"] = RoomStateV1(
        room_id="room-future-001",
        name="Future Study",
        geometry=RoomGeometryV1(length_m=3.0, width_m=2.5, height_m=2.4),
    )
    place = build_place_topology_room_candidate_v1(
        project,
        room_id="room-future-001",
        target_subleg_id="leg-002-primary-subleg",
        target_order=2,
    )
    assert place.ready and place.changed, place.blockers
    assert place.action == PLACE_FROM_STAGING_ACTION
    assert place.target_order == 2

    leg_project = build_hydronic_20_room_multileg_project_v1()
    leg_project.rooms["room-future-001"] = project.rooms["room-future-001"]
    new_leg = build_add_leg_with_principal_candidate_v1(
        leg_project,
        initial_room_id="room-future-001",
    )
    assert new_leg.ready, new_leg.blockers
    leg_project.hydronic_topology = new_leg.topology
    prune_leg = build_return_topology_room_to_staging_candidate_v1(
        leg_project,
        room_id="room-future-001",
    )
    assert prune_leg.ready and prune_leg.changed, prune_leg.blockers
    assert prune_leg.action == RETURN_TO_STAGING_ACTION
    assert prune_leg.pruned_leg_ids == ("leg-003",)
    assert prune_leg.pruned_subleg_ids == ("leg-003-primary-subleg",)
    assert len(prune_leg.topology.legs) == 2

    with TemporaryDirectory(prefix="hs67g2-") as temporary_directory:
        transaction_project = build_hydronic_20_room_multileg_project_v1()
        transaction_project.project_dir = Path(temporary_directory)
        returned = build_return_topology_room_to_staging_candidate_v1(
            transaction_project,
            room_id="room-l2b-005",
        )
        assert returned.ready and returned.changed, returned.blockers
        result = commit_validated_topology_candidate_v1(
            transaction_project,
            returned.topology,
            action_label="Return room to neutral topology staging",
            focus_kind=returned.focus_kind,
            focus_target_id=returned.focus_target_id,
        )
        assert result.ready and result.changed, result.blockers
        assert result.focus is not None
        assert result.focus.kind == FOCUS_STAGING_ROOM
        assert result.focus.room_id == "room-l2b-005"
        assert result.downstream_stale
        assert not transaction_project.hydronics_valid
        inventory = build_topology_unassigned_room_inventory_v1(
            transaction_project
        )
        assert inventory.ready, inventory.blockers
        assert inventory.staging_room_ids == ("room-l2b-005",)
        stepbacks = Path(temporary_directory) / TOPOLOGY_STEPBACK_DIRECTORY
        assert (stepbacks / "project.stepback.1.json").is_file()

    print(
        "OK — H-S67-G2 validates transactional room placement, transfer, "
        "reorder and return-to-staging with safe empty-container pruning."
    )


if __name__ == "__main__":
    main()
