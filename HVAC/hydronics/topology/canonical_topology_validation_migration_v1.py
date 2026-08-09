from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)
from HVAC.hydronics.topology.recursive_subleg_contract_v1 import (
    BRANCH_SUBLEG_KIND,
    PRINCIPAL_SUBLEG_KIND,
    RecursiveSublegPositionV1,
    build_recursive_subleg_positions_v1,
)


COMMON_MAIN_ORIGIN_ID = "common-main"


@dataclass(frozen=True, slots=True)
class CanonicalTopologyValidationV1:
    ready: bool
    positions: tuple[RecursiveSublegPositionV1, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Canonical topology validation not run"


@dataclass(frozen=True, slots=True)
class CanonicalTopologyMigrationV1:
    ready: bool
    topology: HydronicTopologyV1 | None = None
    migrated_branch_subleg_ids: tuple[str, ...] = ()
    created_principal_subleg_ids: tuple[str, ...] = ()
    normalized_principal_subleg_ids: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Canonical topology migration not run"


def validate_canonical_hydronic_topology_v1(
    topology: HydronicTopologyV1,
    *,
    known_room_ids: Iterable[str] | None = None,
) -> CanonicalTopologyValidationV1:
    """Validate one accepted Leg -> Principal -> Branch topology candidate."""

    if not isinstance(topology, HydronicTopologyV1):
        return _validation_blocked("Topology is not HydronicTopologyV1")

    blockers: list[str] = []
    warnings: list[str] = []
    known_rooms = (
        {str(room_id) for room_id in known_room_ids}
        if known_room_ids is not None
        else None
    )

    heat_source_room_id = str(topology.heat_source_room_id or "").strip()
    if not heat_source_room_id:
        blockers.append("Heat-source room identity is required")
    elif known_rooms is not None and heat_source_room_id not in known_rooms:
        blockers.append(
            f"Unknown heat-source room identity: {heat_source_room_id}"
        )

    if not topology.legs:
        blockers.append("At least one hydronic leg is required")

    leg_ids: set[str] = set()
    for leg in topology.legs:
        leg_id = str(leg.leg_id or "").strip()
        if not leg_id:
            blockers.append("Every hydronic leg requires a non-empty leg_id")
        elif leg_id in leg_ids:
            blockers.append(f"Duplicate hydronic leg identity: {leg_id}")
        else:
            leg_ids.add(leg_id)

        if not str(leg.label or "").strip():
            blockers.append(f"{leg_id or 'Unnamed leg'}: label is required")
        if not leg.sublegs:
            blockers.append(
                f"{leg_id or 'Unnamed leg'}: at least one principal subleg is required"
            )

    try:
        positions = build_recursive_subleg_positions_v1(topology)
    except (TypeError, ValueError) as exc:
        return _validation_blocked(str(exc), blockers=blockers)

    sublegs_by_id: dict[str, HydronicSublegV1] = {}
    room_owner_by_id: dict[str, str] = {}

    for position in positions:
        subleg = position.subleg
        subleg_id = str(subleg.subleg_id or "").strip()
        display_id = subleg_id or "Unnamed subleg"

        if not subleg_id:
            blockers.append("Every subleg requires a non-empty subleg_id")
        elif subleg_id in sublegs_by_id:
            blockers.append(f"Duplicate hydronic subleg identity: {subleg_id}")
        else:
            sublegs_by_id[subleg_id] = subleg

        if not str(subleg.label or "").strip():
            blockers.append(f"{display_id}: label is required")

        route_room_ids = [
            str(room_id or "").strip() for room_id in subleg.route_room_ids
        ]
        if not route_room_ids:
            blockers.append(f"{display_id}: at least one room is required")

        local_room_ids: set[str] = set()
        for room_id in route_room_ids:
            if not room_id:
                blockers.append(f"{display_id}: empty room identity is not allowed")
                continue
            if room_id in local_room_ids:
                blockers.append(f"{display_id}: duplicate room identity {room_id}")
                continue
            local_room_ids.add(room_id)

            existing_owner = room_owner_by_id.get(room_id)
            if existing_owner is not None:
                blockers.append(
                    f"Room {room_id} is allocated to both {existing_owner} and {display_id}"
                )
            else:
                room_owner_by_id[room_id] = display_id

            if room_id == heat_source_room_id:
                blockers.append(
                    f"{display_id}: heat-source room cannot be a served route room"
                )
            if known_rooms is not None and room_id not in known_rooms:
                blockers.append(f"{display_id}: unknown room identity {room_id}")

        index_room_id = str(subleg.index_room_id or "").strip()
        if index_room_id and index_room_id not in local_room_ids:
            blockers.append(
                f"{display_id}: index room {index_room_id} is not on its route"
            )

        origin_room_id = str(subleg.origin_room_id or "").strip()
        if position.kind == PRINCIPAL_SUBLEG_KIND:
            if origin_room_id != COMMON_MAIN_ORIGIN_ID:
                blockers.append(
                    f"{display_id}: principal subleg origin must be common-main"
                )
        elif position.kind == BRANCH_SUBLEG_KIND:
            parent = sublegs_by_id.get(str(position.parent_subleg_id or ""))
            if parent is None:
                blockers.append(f"{display_id}: immediate parent is unavailable")
            elif not origin_room_id:
                blockers.append(f"{display_id}: branch origin room is required")
            elif origin_room_id not in {
                str(room_id) for room_id in parent.route_room_ids
            }:
                blockers.append(
                    f"{display_id}: origin {origin_room_id} is not on immediate "
                    f"parent {parent.subleg_id}"
                )

    for leg in topology.legs:
        legacy_rooms = [str(room_id) for room_id in leg.route_room_ids]
        legacy_index = str(leg.index_room_id or "").strip()
        if not legacy_rooms and not legacy_index:
            continue

        conventional_id = primary_subleg_id_for_leg(leg.leg_id)
        mirror_source = next(
            (
                subleg
                for subleg in leg.sublegs
                if subleg.subleg_id == conventional_id
            ),
            leg.sublegs[0] if leg.sublegs else None,
        )
        if mirror_source is None:
            blockers.append(f"{leg.leg_id}: legacy mirror has no principal source")
            continue
        if legacy_rooms and legacy_rooms != list(mirror_source.route_room_ids):
            blockers.append(
                f"{leg.leg_id}: legacy room mirror differs from principal subleg"
            )
        if legacy_index and legacy_index != str(mirror_source.index_room_id or ""):
            blockers.append(
                f"{leg.leg_id}: legacy index mirror differs from principal subleg"
            )
        warnings.append(
            f"{leg.leg_id}: transitional legacy leg route/index mirror retained"
        )

    blockers = _unique(blockers)
    warnings = _unique(warnings)
    ready = not blockers
    return CanonicalTopologyValidationV1(
        ready=ready,
        positions=positions,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        status=(
            "Ready — canonical recursive hydronic topology is valid"
            if ready
            else "Blocked — canonical recursive hydronic topology is invalid"
        ),
    )


def migrate_legacy_flat_sublegs_to_canonical_v1(
    topology: HydronicTopologyV1,
    *,
    known_room_ids: Iterable[str] | None = None,
) -> CanonicalTopologyMigrationV1:
    """Build, validate and return a separate canonical topology candidate."""

    if not isinstance(topology, HydronicTopologyV1):
        return _migration_blocked("Topology is not HydronicTopologyV1")

    try:
        candidate = HydronicTopologyV1.from_dict(topology.to_dict())
    except (RecursionError, TypeError, ValueError) as exc:
        return _migration_blocked(f"Topology cannot be copied safely: {exc}")

    migrated: list[str] = []
    created: list[str] = []
    normalized: list[str] = []
    blockers: list[str] = []

    for leg in candidate.legs:
        conventional_id = primary_subleg_id_for_leg(leg.leg_id)
        if not leg.sublegs and leg.route_room_ids:
            leg.sublegs.append(
                HydronicSublegV1(
                    subleg_id=conventional_id,
                    label="Principal subleg",
                    origin_room_id=COMMON_MAIN_ORIGIN_ID,
                    route_room_ids=list(leg.route_room_ids),
                    index_room_id=leg.index_room_id,
                    sublegs=[],
                )
            )
            created.append(conventional_id)

        principals: list[HydronicSublegV1] = []
        pending: list[HydronicSublegV1] = []
        for subleg in leg.sublegs:
            origin = str(subleg.origin_room_id or "").strip()
            if (
                subleg.subleg_id == conventional_id
                or origin == COMMON_MAIN_ORIGIN_ID
            ):
                if origin != COMMON_MAIN_ORIGIN_ID:
                    subleg.origin_room_id = COMMON_MAIN_ORIGIN_ID
                    normalized.append(subleg.subleg_id)
                principals.append(subleg)
            else:
                pending.append(subleg)

        if not principals:
            blockers.append(
                f"{leg.leg_id}: no principal subleg can be resolved safely"
            )
            continue

        leg.sublegs[:] = principals
        while pending:
            available_parents = _flatten_sublegs(principals)
            progressed = False
            unresolved: list[HydronicSublegV1] = []

            for subleg in pending:
                origin = str(subleg.origin_room_id or "").strip()
                matches = [
                    parent
                    for parent in available_parents
                    if origin and origin in {
                        str(room_id) for room_id in parent.route_room_ids
                    }
                ]
                if len(matches) == 1:
                    matches[0].sublegs.append(subleg)
                    migrated.append(subleg.subleg_id)
                    progressed = True
                elif len(matches) > 1:
                    blockers.append(
                        f"{leg.leg_id}/{subleg.subleg_id}: branch origin "
                        f"{origin} matches more than one possible parent"
                    )
                else:
                    unresolved.append(subleg)

            pending = unresolved
            if not progressed:
                for subleg in pending:
                    blockers.append(
                        f"{leg.leg_id}/{subleg.subleg_id}: branch origin "
                        f"{subleg.origin_room_id or '—'} has no unique parent"
                    )
                break

    if blockers:
        return _migration_blocked(
            *blockers,
            migrated=migrated,
            created=created,
            normalized=normalized,
        )

    validation = validate_canonical_hydronic_topology_v1(
        candidate,
        known_room_ids=known_room_ids,
    )
    if not validation.ready:
        return _migration_blocked(
            *validation.blockers,
            migrated=migrated,
            created=created,
            normalized=normalized,
            warnings=validation.warnings,
        )

    return CanonicalTopologyMigrationV1(
        ready=True,
        topology=candidate,
        migrated_branch_subleg_ids=tuple(_unique(migrated)),
        created_principal_subleg_ids=tuple(_unique(created)),
        normalized_principal_subleg_ids=tuple(_unique(normalized)),
        warnings=validation.warnings,
        status=(
            "Ready — legacy flat topology converted to a separate validated "
            "Principal → Branch candidate"
        ),
    )


def _flatten_sublegs(
    roots: Iterable[HydronicSublegV1],
) -> list[HydronicSublegV1]:
    out: list[HydronicSublegV1] = []

    def walk(subleg: HydronicSublegV1) -> None:
        out.append(subleg)
        for child in subleg.sublegs:
            walk(child)

    for root in roots:
        walk(root)
    return out


def _validation_blocked(
    reason: str,
    *,
    blockers: Iterable[str] = (),
) -> CanonicalTopologyValidationV1:
    return CanonicalTopologyValidationV1(
        ready=False,
        blockers=tuple(_unique([*blockers, reason])),
        status="Blocked — canonical recursive hydronic topology is invalid",
    )


def _migration_blocked(
    *blockers: str,
    migrated: Iterable[str] = (),
    created: Iterable[str] = (),
    normalized: Iterable[str] = (),
    warnings: Iterable[str] = (),
) -> CanonicalTopologyMigrationV1:
    return CanonicalTopologyMigrationV1(
        ready=False,
        migrated_branch_subleg_ids=tuple(_unique(migrated)),
        created_principal_subleg_ids=tuple(_unique(created)),
        normalized_principal_subleg_ids=tuple(_unique(normalized)),
        blockers=tuple(_unique(blockers)),
        warnings=tuple(_unique(warnings)),
        status="Blocked — legacy topology cannot be migrated unambiguously",
    )


def _unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out
