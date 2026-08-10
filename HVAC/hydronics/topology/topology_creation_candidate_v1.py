from __future__ import annotations

from dataclasses import dataclass
import re

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
from HVAC.project.project_state import ProjectState
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)
from HVAC.hydronics.topology.recursive_subleg_contract_v1 import (
    build_recursive_subleg_positions_v1,
)


@dataclass(frozen=True, slots=True)
class TopologyCreationCandidateV1:
    ready: bool
    topology: HydronicTopologyV1 | None = None
    leg_id: str = ""
    principal_subleg_id: str = ""
    created_subleg_id: str = ""
    parent_subleg_id: str = ""
    branch_origin_room_id: str = ""
    focus_kind: str = "principal_subleg"
    focus_target_id: str = ""
    initial_room_id: str = ""
    migration_applied: bool = False
    room_reallocated: bool = False
    blockers: tuple[str, ...] = ()
    status: str = "Topology creation candidate not built"


def build_add_leg_with_principal_candidate_v1(
    project_state: ProjectState,
    *,
    initial_room_id: str,
    leg_label: str = "",
    principal_label: str = "",
) -> TopologyCreationCandidateV1:
    """Build, but do not install, one complete Leg + Principal candidate."""

    prepared = _copy_and_check_room(project_state, initial_room_id)
    if isinstance(prepared, TopologyCreationCandidateV1):
        return prepared
    candidate, room_id, migration_applied, room_reallocated = prepared

    leg_number = _next_leg_number(candidate)
    leg_id = f"leg-{leg_number:03d}"
    principal_id = f"{leg_id}-primary-subleg"
    candidate.legs.append(
        HydronicLegV1(
            leg_id=leg_id,
            label=str(leg_label or "").strip() or f"Heating Leg {leg_number}",
            sublegs=[
                HydronicSublegV1(
                    subleg_id=principal_id,
                    label=(
                        str(principal_label or "").strip()
                        or "Principal subleg 1"
                    ),
                    origin_room_id=COMMON_MAIN_ORIGIN_ID,
                    route_room_ids=[room_id],
                    index_room_id=room_id,
                )
            ],
        )
    )
    return _validated_result(
        project_state,
        candidate,
        leg_id=leg_id,
        principal_subleg_id=principal_id,
        initial_room_id=room_id,
        migration_applied=migration_applied,
        room_reallocated=room_reallocated,
        status="Ready — complete Leg and first Principal creation candidate",
    )


def build_add_principal_subleg_candidate_v1(
    project_state: ProjectState,
    *,
    leg_id: str,
    initial_room_id: str,
    principal_label: str = "",
) -> TopologyCreationCandidateV1:
    """Build, but do not install, one additional Principal candidate."""

    prepared = _copy_and_check_room(project_state, initial_room_id)
    if isinstance(prepared, TopologyCreationCandidateV1):
        return prepared
    candidate, room_id, migration_applied, room_reallocated = prepared

    selected_leg_id = str(leg_id or "").strip()
    selected_leg = next(
        (leg for leg in candidate.legs if leg.leg_id == selected_leg_id),
        None,
    )
    if selected_leg is None:
        return _blocked(f"Unknown hydronic leg identity: {selected_leg_id}")

    principal_number = len(selected_leg.sublegs) + 1
    principal_id = _next_principal_id(selected_leg, principal_number)
    selected_leg.sublegs.append(
        HydronicSublegV1(
            subleg_id=principal_id,
            label=(
                str(principal_label or "").strip()
                or f"Principal subleg {principal_number}"
            ),
            origin_room_id=COMMON_MAIN_ORIGIN_ID,
            route_room_ids=[room_id],
            index_room_id=room_id,
        )
    )
    return _validated_result(
        project_state,
        candidate,
        leg_id=selected_leg_id,
        principal_subleg_id=principal_id,
        initial_room_id=room_id,
        migration_applied=migration_applied,
        room_reallocated=room_reallocated,
        status="Ready — additional Principal creation candidate",
    )


def build_add_branch_subleg_candidate_v1(
    project_state: ProjectState,
    *,
    parent_subleg_id: str,
    branch_origin_room_id: str,
    initial_room_id: str,
    branch_label: str = "",
) -> TopologyCreationCandidateV1:
    """Build one recursive Branch candidate beneath an exact parent."""

    parent_id = str(parent_subleg_id or "").strip()
    origin_room_id = str(branch_origin_room_id or "").strip()
    initial_id = str(initial_room_id or "").strip()
    if not parent_id:
        return _blocked("An exact parent subleg is required")
    if not origin_room_id:
        return _blocked("A branch-origin room is required")
    if initial_id == origin_room_id:
        return _blocked(
            "Branch first served room must differ from its parent "
            "take-off room"
        )

    prepared = _copy_and_check_room(project_state, initial_id)
    if isinstance(prepared, TopologyCreationCandidateV1):
        return prepared
    candidate, room_id, migration_applied, room_reallocated = prepared

    position = next(
        (
            item
            for item in build_recursive_subleg_positions_v1(candidate)
            if item.subleg_id == parent_id
        ),
        None,
    )
    if position is None:
        return _blocked(f"Unknown parent subleg identity: {parent_id}")
    if origin_room_id not in {
        str(value) for value in position.subleg.route_room_ids
    }:
        return _blocked(
            f"Branch origin {origin_room_id} is not on immediate parent "
            f"{parent_id}"
        )

    branch_number = len(position.subleg.sublegs) + 1
    branch_id = _next_branch_id(candidate, parent_id, branch_number)
    position.subleg.sublegs.append(
        HydronicSublegV1(
            subleg_id=branch_id,
            label=(
                str(branch_label or "").strip()
                or f"Branch subleg {branch_number}"
            ),
            origin_room_id=origin_room_id,
            route_room_ids=[room_id],
            index_room_id=room_id,
        )
    )
    return _validated_result(
        project_state,
        candidate,
        leg_id=position.leg_id,
        principal_subleg_id="",
        initial_room_id=room_id,
        migration_applied=migration_applied,
        room_reallocated=room_reallocated,
        status="Ready — recursive Branch creation candidate",
        created_subleg_id=branch_id,
        parent_subleg_id=parent_id,
        branch_origin_room_id=origin_room_id,
        focus_kind="branch_subleg",
    )
def topology_creation_room_ids_v1(
    project_state: ProjectState,
) -> tuple[str, ...]:
    topology = getattr(project_state, "hydronic_topology", None)
    if not isinstance(topology, HydronicTopologyV1):
        return ()
    heat_source = str(topology.heat_source_room_id or "")
    return tuple(
        str(room_id)
        for room_id in project_state.rooms
        if str(room_id) != heat_source
    )


def _copy_and_check_room(
    project_state: ProjectState,
    initial_room_id: str,
) -> tuple[HydronicTopologyV1, str, bool, bool] | TopologyCreationCandidateV1:
    if not isinstance(project_state, ProjectState):
        return _blocked("ProjectState is required")
    topology = getattr(project_state, "hydronic_topology", None)
    if not isinstance(topology, HydronicTopologyV1):
        return _blocked("Canonical HydronicTopologyV1 is required")

    room_id = str(initial_room_id or "").strip()
    if not room_id:
        return _blocked("An initial room is required")
    if room_id not in project_state.rooms:
        return _blocked(f"Unknown room identity: {room_id}")
    if room_id == str(topology.heat_source_room_id or ""):
        return _blocked("Heat-source room cannot seed a served subleg")
    current_validation = validate_canonical_hydronic_topology_v1(
        topology,
        known_room_ids=project_state.rooms,
    )
    if current_validation.ready:
        candidate = HydronicTopologyV1.from_dict(topology.to_dict())
        migration_applied = False
    else:
        migration = migrate_legacy_flat_sublegs_to_canonical_v1(
            topology,
            known_room_ids=project_state.rooms,
        )
        if not migration.ready or migration.topology is None:
            return _blocked(
                "Existing topology is not canonical and cannot be migrated safely",
                *migration.blockers,
            )
        candidate = migration.topology
        migration_applied = True

    detach = _detach_room_for_creation(candidate, room_id)
    if isinstance(detach, TopologyCreationCandidateV1):
        return detach
    return candidate, room_id, migration_applied, detach


def _validated_result(
    project_state: ProjectState,
    candidate: HydronicTopologyV1,
    *,
    leg_id: str,
    principal_subleg_id: str,
    initial_room_id: str,
    migration_applied: bool,
    room_reallocated: bool,
    status: str,
    created_subleg_id: str = "",
    parent_subleg_id: str = "",
    branch_origin_room_id: str = "",
    focus_kind: str = "principal_subleg",
) -> TopologyCreationCandidateV1:
    validation = validate_canonical_hydronic_topology_v1(
        candidate,
        known_room_ids=project_state.rooms,
    )
    if not validation.ready:
        return _blocked(*validation.blockers)
    return TopologyCreationCandidateV1(
        ready=True,
        topology=candidate,
        leg_id=leg_id,
        principal_subleg_id=principal_subleg_id,
        created_subleg_id=(created_subleg_id or principal_subleg_id),
        parent_subleg_id=parent_subleg_id,
        branch_origin_room_id=branch_origin_room_id,
        focus_kind=focus_kind,
        focus_target_id=(created_subleg_id or principal_subleg_id),
        initial_room_id=initial_room_id,
        migration_applied=migration_applied,
        room_reallocated=room_reallocated,
        status=(
            status
            + (
                "; accepted legacy topology migration included"
                if migration_applied
                else ""
            )
            + ("; selected room reallocated" if room_reallocated else "")
        ),
    )


def _next_leg_number(topology: HydronicTopologyV1) -> int:
    numbers = []
    for leg in topology.legs:
        match = re.fullmatch(r"leg-(\d+)", str(leg.leg_id or ""))
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def _next_principal_id(leg: HydronicLegV1, starting_number: int) -> str:
    existing = {subleg.subleg_id for subleg in leg.sublegs}
    number = max(2, int(starting_number))
    while True:
        candidate = f"{leg.leg_id}-principal-subleg-{number:03d}"
        if candidate not in existing:
            return candidate
        number += 1


def _next_branch_id(
    topology: HydronicTopologyV1,
    parent_subleg_id: str,
    starting_number: int,
) -> str:
    existing = {
        position.subleg_id
        for position in build_recursive_subleg_positions_v1(topology)
    }
    number = max(1, int(starting_number))
    while True:
        candidate = f"{parent_subleg_id}-branch-subleg-{number:03d}"
        if candidate not in existing:
            return candidate
        number += 1


def _detach_room_for_creation(
    topology: HydronicTopologyV1,
    room_id: str,
) -> bool | TopologyCreationCandidateV1:
    owner: HydronicSublegV1 | None = None
    owner_leg: HydronicLegV1 | None = None

    def walk(leg: HydronicLegV1, subleg: HydronicSublegV1) -> None:
        nonlocal owner, owner_leg
        if room_id in subleg.route_room_ids:
            owner = subleg
            owner_leg = leg
        for child in subleg.sublegs:
            walk(leg, child)

    for leg in topology.legs:
        for principal in leg.sublegs:
            walk(leg, principal)

    if owner is None or owner_leg is None:
        return False
    if len(owner.route_room_ids) <= 1:
        return _blocked(
            f"Room {room_id} is the only room on {owner.subleg_id}; "
            "choose another initial room"
        )
    if any(child.origin_room_id == room_id for child in owner.sublegs):
        return _blocked(
            f"Room {room_id} is a branch origin on {owner.subleg_id}; "
            "branch reassignment is deferred"
        )

    owner.route_room_ids.remove(room_id)
    if owner.index_room_id == room_id:
        owner.index_room_id = owner.route_room_ids[-1]

    conventional_id = primary_subleg_id_for_leg(owner_leg.leg_id)
    mirror_source = next(
        (
            subleg
            for subleg in owner_leg.sublegs
            if subleg.subleg_id == conventional_id
        ),
        owner_leg.sublegs[0] if owner_leg.sublegs else None,
    )
    if owner is mirror_source and (
        owner_leg.route_room_ids or owner_leg.index_room_id
    ):
        owner_leg.route_room_ids = list(owner.route_room_ids)
        owner_leg.index_room_id = owner.index_room_id
    return True


def _blocked(*blockers: str) -> TopologyCreationCandidateV1:
    cleaned = tuple(str(item) for item in blockers if str(item).strip())
    return TopologyCreationCandidateV1(
        ready=False,
        blockers=cleaned or ("Topology creation candidate is blocked",),
        status="Blocked — topology creation candidate was not built",
    )
