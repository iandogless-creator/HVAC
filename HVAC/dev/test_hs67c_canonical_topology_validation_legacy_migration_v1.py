from __future__ import annotations

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.proportioning.branch_aware_carried_flow_basis_v1 import (
    build_branch_aware_carried_flow_basis_v1,
)
from HVAC.hydronics.topology.canonical_topology_validation_migration_v1 import (
    COMMON_MAIN_ORIGIN_ID,
    migrate_legacy_flat_sublegs_to_canonical_v1,
    validate_canonical_hydronic_topology_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)


def _flow_signature(project) -> tuple[tuple, ...]:
    evidence = build_branch_aware_carried_flow_basis_v1(project)
    assert evidence.ready, evidence.blockers
    return tuple(
        (
            row.section_id,
            row.parent_subleg_id,
            row.carried_room_ids,
            row.carried_heat_W,
        )
        for row in evidence.rows
    )


def main() -> None:
    project = build_hydronic_20_room_multileg_project_v1()
    original = project.hydronic_topology
    before_signature = _flow_signature(project)
    original_top_level_ids = [
        [subleg.subleg_id for subleg in leg.sublegs]
        for leg in original.legs
    ]

    migrated = migrate_legacy_flat_sublegs_to_canonical_v1(
        original,
        known_room_ids=project.rooms,
    )
    assert migrated.ready, migrated.blockers
    assert migrated.topology is not None
    assert set(migrated.migrated_branch_subleg_ids) == {
        "leg-001-subleg-b",
        "leg-002-subleg-b",
    }

    # Candidate construction never mutates the loaded legacy topology.
    assert [
        [subleg.subleg_id for subleg in leg.sublegs]
        for leg in original.legs
    ] == original_top_level_ids

    candidate = migrated.topology
    for leg in candidate.legs:
        assert len(leg.sublegs) == 1
        principal = leg.sublegs[0]
        assert principal.origin_room_id == COMMON_MAIN_ORIGIN_ID
        assert len(principal.sublegs) == 1
        assert principal.sublegs[0].subleg_id.endswith("subleg-b")

    validation = validate_canonical_hydronic_topology_v1(
        candidate,
        known_room_ids=project.rooms,
    )
    assert validation.ready, validation.blockers
    assert validation.warnings

    project.hydronic_topology = candidate
    assert _flow_signature(project) == before_signature

    round_tripped = HydronicTopologyV1.from_dict(candidate.to_dict())
    assert validate_canonical_hydronic_topology_v1(
        round_tripped,
        known_room_ids=project.rooms,
    ).ready

    # Multiple principals are canonical, not branches in disguise.
    multiple_principals = HydronicTopologyV1(
        heat_source_room_id="boiler",
        legs=[
            HydronicLegV1(
                leg_id="leg-many",
                label="Many principals",
                sublegs=[
                    HydronicSublegV1(
                        subleg_id="principal-a",
                        label="Principal A",
                        origin_room_id=COMMON_MAIN_ORIGIN_ID,
                        route_room_ids=["room-a"],
                    ),
                    HydronicSublegV1(
                        subleg_id="principal-b",
                        label="Principal B",
                        origin_room_id=COMMON_MAIN_ORIGIN_ID,
                        route_room_ids=["room-b"],
                    ),
                ],
            )
        ],
    )
    assert validate_canonical_hydronic_topology_v1(
        multiple_principals,
        known_room_ids={"boiler", "room-a", "room-b"},
    ).ready
    unchanged = migrate_legacy_flat_sublegs_to_canonical_v1(
        multiple_principals,
        known_room_ids={"boiler", "room-a", "room-b"},
    )
    assert unchanged.ready
    assert not unchanged.migrated_branch_subleg_ids

    # Never guess when a legacy flat branch origin has two possible parents.
    ambiguous = HydronicTopologyV1.from_dict(multiple_principals.to_dict())
    ambiguous.legs[0].sublegs[1].route_room_ids = ["room-a"]
    ambiguous.legs[0].sublegs.append(
        HydronicSublegV1(
            subleg_id="flat-branch",
            label="Flat branch",
            origin_room_id="room-a",
            route_room_ids=["room-c"],
        )
    )
    blocked = migrate_legacy_flat_sublegs_to_canonical_v1(
        ambiguous,
        known_room_ids={"boiler", "room-a", "room-c"},
    )
    assert not blocked.ready
    assert any("more than one possible parent" in row for row in blocked.blockers)

    invalid_origin = HydronicTopologyV1.from_dict(candidate.to_dict())
    invalid_origin.legs[0].sublegs[0].sublegs[0].origin_room_id = "not-parent"
    invalid = validate_canonical_hydronic_topology_v1(
        invalid_origin,
        known_room_ids=project.rooms,
    )
    assert not invalid.ready
    assert any("not on immediate parent" in row for row in invalid.blockers)

    print(
        "OK — H-S67-C canonical topology validation and unambiguous "
        "legacy flat Principal → Branch migration passed."
    )


if __name__ == "__main__":
    main()
