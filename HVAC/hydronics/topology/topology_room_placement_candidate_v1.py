from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.topology.canonical_topology_validation_migration_v1 import (
    migrate_legacy_flat_sublegs_to_canonical_v1,
    validate_canonical_hydronic_topology_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)
from HVAC.hydronics.topology.recursive_subleg_contract_v1 import (
    RecursiveSublegPositionV1,
    build_recursive_subleg_positions_v1,
)
from HVAC.hydronics.topology.transactional_topology_editor_v1 import (
    FOCUS_ROOM,
    FOCUS_STAGING_ROOM,
)


PLACE_FROM_STAGING_ACTION = "place_from_staging"
REORDER_WITHIN_SUBLEG_ACTION = "reorder_within_subleg"
TRANSFER_BETWEEN_SUBLEGS_ACTION = "transfer_between_sublegs"
RETURN_TO_STAGING_ACTION = "return_to_staging"


@dataclass(frozen=True, slots=True)
class TopologyRoomPlacementCandidateV1:
    """One separately validated room placement candidate."""

    ready: bool
    changed: bool = False
    topology: HydronicTopologyV1 | None = None
    action: str = ""
    room_id: str = ""
    source_leg_id: str = ""
    source_subleg_id: str = ""
    target_leg_id: str = ""
    target_subleg_id: str = ""
    target_order: int = 0
    pruned_leg_ids: tuple[str, ...] = ()
    pruned_subleg_ids: tuple[str, ...] = ()
    migration_applied: bool = False
    focus_kind: str = ""
    focus_target_id: str = ""
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Topology room placement candidate not built"


def build_place_topology_room_candidate_v1(
    project_state: Any,
    *,
    room_id: str,
    target_subleg_id: str,
    target_order: int | None = None,
) -> TopologyRoomPlacementCandidateV1:
    """Place, transfer or reorder one room at an exact final route order."""

    prepared = _prepare(project_state, room_id)
    if isinstance(prepared, TopologyRoomPlacementCandidateV1):
        return prepared
    candidate, stable_room_id, migration_applied, warnings = prepared
    original_dict = project_state.hydronic_topology.to_dict()

    positions = build_recursive_subleg_positions_v1(candidate)
    target = next(
        (
            position
            for position in positions
            if position.subleg_id == str(target_subleg_id or "").strip()
        ),
        None,
    )
    if target is None:
        return _blocked(
            f"Unknown target subleg identity: {target_subleg_id}",
            room_id=stable_room_id,
        )
    source = _room_owner(positions, stable_room_id)
    same_subleg = bool(
        source is not None and source.subleg_id == target.subleg_id
    )
    if source is not None and not same_subleg:
        dependent = _dependent_branch_ids(source.subleg, stable_room_id)
        if dependent:
            return _blocked(
                f"Room {stable_room_id} is the take-off for dependent Branch "
                f"subleg(s): {', '.join(dependent)}; move or remove those "
                "Branches first",
                room_id=stable_room_id,
            )

    source_leg_id = source.leg_id if source is not None else ""
    source_subleg_id = source.subleg_id if source is not None else ""
    pruned_legs: list[str] = []
    pruned_sublegs: list[str] = []
    if source is not None:
        if same_subleg:
            source.subleg.route_room_ids.remove(stable_room_id)
        else:
            detach_blocker = _detach_room(
                candidate,
                source,
                stable_room_id,
                pruned_leg_ids=pruned_legs,
                pruned_subleg_ids=pruned_sublegs,
            )
            if detach_blocker:
                return _blocked(detach_blocker, room_id=stable_room_id)

    positions = build_recursive_subleg_positions_v1(candidate)
    target = next(
        (position for position in positions if position.subleg_id == target.subleg_id),
        None,
    )
    if target is None:
        return _blocked(
            "Target subleg was removed while detaching the source room",
            room_id=stable_room_id,
        )
    insertion_index = _resolve_insertion_index(
        target_order,
        remaining_count=len(target.subleg.route_room_ids),
    )
    if insertion_index is None:
        return _blocked(
            f"Target order must be between 1 and "
            f"{len(target.subleg.route_room_ids) + 1}, or omitted to append",
            room_id=stable_room_id,
        )
    target.subleg.route_room_ids.insert(insertion_index, stable_room_id)
    if not str(target.subleg.index_room_id or ""):
        target.subleg.index_room_id = stable_room_id

    _sync_legacy_leg_mirrors(candidate)
    validation = validate_canonical_hydronic_topology_v1(
        candidate,
        known_room_ids=project_state.rooms,
    )
    if not validation.ready:
        return _blocked(*validation.blockers, room_id=stable_room_id)

    action = (
        PLACE_FROM_STAGING_ACTION
        if source is None
        else (
            REORDER_WITHIN_SUBLEG_ACTION
            if same_subleg
            else TRANSFER_BETWEEN_SUBLEGS_ACTION
        )
    )
    changed = original_dict != candidate.to_dict()
    return TopologyRoomPlacementCandidateV1(
        ready=True,
        changed=changed,
        topology=candidate,
        action=action,
        room_id=stable_room_id,
        source_leg_id=source_leg_id,
        source_subleg_id=source_subleg_id,
        target_leg_id=target.leg_id,
        target_subleg_id=target.subleg_id,
        target_order=insertion_index + 1,
        pruned_leg_ids=tuple(pruned_legs),
        pruned_subleg_ids=tuple(pruned_sublegs),
        migration_applied=migration_applied,
        focus_kind=FOCUS_ROOM,
        focus_target_id=stable_room_id,
        warnings=tuple(validation.warnings) + warnings,
        status=(
            "Ready — exact topology room placement candidate"
            if changed
            else "Ready — requested room placement is unchanged"
        ),
    )


def build_return_topology_room_to_staging_candidate_v1(
    project_state: Any,
    *,
    room_id: str,
) -> TopologyRoomPlacementCandidateV1:
    """Remove one room from topology while preserving all room data."""

    prepared = _prepare(project_state, room_id)
    if isinstance(prepared, TopologyRoomPlacementCandidateV1):
        return prepared
    candidate, stable_room_id, migration_applied, warnings = prepared
    original_dict = project_state.hydronic_topology.to_dict()
    positions = build_recursive_subleg_positions_v1(candidate)
    source = _room_owner(positions, stable_room_id)
    if source is None:
        return TopologyRoomPlacementCandidateV1(
            ready=True,
            changed=False,
            topology=candidate,
            action=RETURN_TO_STAGING_ACTION,
            room_id=stable_room_id,
            migration_applied=migration_applied,
            focus_kind=FOCUS_STAGING_ROOM,
            focus_target_id=stable_room_id,
            warnings=warnings,
            status="Ready — room is already in neutral staging",
        )
    dependent = _dependent_branch_ids(source.subleg, stable_room_id)
    if dependent:
        return _blocked(
            f"Room {stable_room_id} is the take-off for dependent Branch "
            f"subleg(s): {', '.join(dependent)}; move or remove those "
            "Branches first",
            room_id=stable_room_id,
        )

    pruned_legs: list[str] = []
    pruned_sublegs: list[str] = []
    detach_blocker = _detach_room(
        candidate,
        source,
        stable_room_id,
        pruned_leg_ids=pruned_legs,
        pruned_subleg_ids=pruned_sublegs,
    )
    if detach_blocker:
        return _blocked(detach_blocker, room_id=stable_room_id)
    if not candidate.legs:
        return _blocked(
            "The final populated Leg cannot be removed from accepted topology; "
            "an empty draft topology boundary is deferred",
            room_id=stable_room_id,
        )

    _sync_legacy_leg_mirrors(candidate)
    validation = validate_canonical_hydronic_topology_v1(
        candidate,
        known_room_ids=project_state.rooms,
    )
    if not validation.ready:
        return _blocked(*validation.blockers, room_id=stable_room_id)
    return TopologyRoomPlacementCandidateV1(
        ready=True,
        changed=(original_dict != candidate.to_dict()),
        topology=candidate,
        action=RETURN_TO_STAGING_ACTION,
        room_id=stable_room_id,
        source_leg_id=source.leg_id,
        source_subleg_id=source.subleg_id,
        pruned_leg_ids=tuple(pruned_legs),
        pruned_subleg_ids=tuple(pruned_sublegs),
        migration_applied=migration_applied,
        focus_kind=FOCUS_STAGING_ROOM,
        focus_target_id=stable_room_id,
        warnings=tuple(validation.warnings) + warnings,
        status=(
            "Ready — room returns to neutral staging; room, Heat-Loss and "
            "emitter data remain unchanged"
        ),
    )


def _prepare(project_state: Any, room_id: str):
    rooms = getattr(project_state, "rooms", None)
    topology = getattr(project_state, "hydronic_topology", None)
    stable_room_id = str(room_id or "").strip()
    if not isinstance(rooms, dict):
        return _blocked("ProjectState rooms mapping is required")
    if not isinstance(topology, HydronicTopologyV1):
        return _blocked("Canonical HydronicTopologyV1 is required")
    if stable_room_id not in rooms:
        return _blocked(f"Unknown room identity: {stable_room_id}")
    if stable_room_id == str(topology.heat_source_room_id or ""):
        return _blocked("Plant/Heat Source room cannot be moved or staged")

    validation = validate_canonical_hydronic_topology_v1(
        topology,
        known_room_ids=rooms,
    )
    if validation.ready:
        return (
            HydronicTopologyV1.from_dict(topology.to_dict()),
            stable_room_id,
            False,
            tuple(validation.warnings),
        )
    migration = migrate_legacy_flat_sublegs_to_canonical_v1(
        topology,
        known_room_ids=rooms,
    )
    if not migration.ready or migration.topology is None:
        return _blocked(
            "Existing topology is neither canonical nor safely migratable",
            *validation.blockers,
            *migration.blockers,
        )
    return (
        migration.topology,
        stable_room_id,
        True,
        tuple(migration.warnings),
    )


def _room_owner(
    positions: tuple[RecursiveSublegPositionV1, ...],
    room_id: str,
) -> RecursiveSublegPositionV1 | None:
    return next(
        (
            position
            for position in positions
            if room_id in {str(value) for value in position.subleg.route_room_ids}
        ),
        None,
    )


def _dependent_branch_ids(
    subleg: HydronicSublegV1,
    room_id: str,
) -> tuple[str, ...]:
    return tuple(
        child.subleg_id
        for child in subleg.sublegs
        if str(child.origin_room_id or "") == room_id
    )


def _detach_room(
    topology: HydronicTopologyV1,
    source: RecursiveSublegPositionV1,
    room_id: str,
    *,
    pruned_leg_ids: list[str],
    pruned_subleg_ids: list[str],
) -> str:
    subleg = source.subleg
    if len(subleg.route_room_ids) > 1:
        subleg.route_room_ids.remove(room_id)
        if str(subleg.index_room_id or "") == room_id:
            subleg.index_room_id = subleg.route_room_ids[-1]
        return ""
    if subleg.sublegs:
        return (
            f"Room {room_id} is the sole room on {subleg.subleg_id}, which "
            "still owns child Branch sublegs"
        )

    pruned_subleg_ids.append(subleg.subleg_id)
    if source.parent_subleg_id:
        parent = next(
            (
                position.subleg
                for position in build_recursive_subleg_positions_v1(topology)
                if position.subleg_id == source.parent_subleg_id
            ),
            None,
        )
        if parent is None:
            return f"Immediate parent of {subleg.subleg_id} is unavailable"
        parent.sublegs.remove(subleg)
        return ""

    leg = next(
        (item for item in topology.legs if item.leg_id == source.leg_id),
        None,
    )
    if leg is None:
        return f"Owning Leg {source.leg_id} is unavailable"
    leg.sublegs.remove(subleg)
    if not leg.sublegs:
        topology.legs.remove(leg)
        pruned_leg_ids.append(leg.leg_id)
    return ""


def _resolve_insertion_index(
    target_order: int | None,
    *,
    remaining_count: int,
) -> int | None:
    if target_order in (None, 0):
        return remaining_count
    try:
        final_order = int(target_order)
    except (TypeError, ValueError):
        return None
    if final_order < 1 or final_order > remaining_count + 1:
        return None
    return final_order - 1


def _sync_legacy_leg_mirrors(topology: HydronicTopologyV1) -> None:
    for leg in topology.legs:
        conventional_id = primary_subleg_id_for_leg(leg.leg_id)
        source = next(
            (
                subleg
                for subleg in leg.sublegs
                if subleg.subleg_id == conventional_id
            ),
            leg.sublegs[0] if leg.sublegs else None,
        )
        if source is None:
            leg.route_room_ids = []
            leg.index_room_id = None
        else:
            leg.route_room_ids = list(source.route_room_ids)
            leg.index_room_id = source.index_room_id


def _blocked(
    *blockers: str,
    room_id: str = "",
) -> TopologyRoomPlacementCandidateV1:
    cleaned = tuple(dict.fromkeys(str(value) for value in blockers if str(value).strip()))
    return TopologyRoomPlacementCandidateV1(
        ready=False,
        room_id=room_id,
        blockers=cleaned or ("Topology room placement is blocked",),
        status="Blocked — topology room placement candidate is not trustworthy",
    )
