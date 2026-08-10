from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.topology.canonical_topology_validation_migration_v1 import (
    migrate_legacy_flat_sublegs_to_canonical_v1,
    validate_canonical_hydronic_topology_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import HydronicTopologyV1
from HVAC.hydronics.topology.recursive_subleg_contract_v1 import (
    build_recursive_subleg_positions_v1,
)


FIXED_HEAT_SOURCE_DISPOSITION = "fixed_heat_source"
ASSIGNED_TOPOLOGY_DISPOSITION = "assigned_topology"
UNASSIGNED_STAGING_DISPOSITION = "unassigned_staging"


@dataclass(frozen=True, slots=True)
class TopologyRoomInventoryRowV1:
    """One exact room disposition in the Topology Arranger inventory."""

    room_id: str
    room_label: str
    disposition: str
    leg_id: str = ""
    leg_label: str = ""
    subleg_id: str = ""
    subleg_label: str = ""
    subleg_kind: str = ""
    route_order: int = 0
    is_index: bool = False
    is_terminal: bool = False


@dataclass(frozen=True, slots=True)
class TopologyUnassignedRoomInventoryV1:
    """Complete derived room inventory; it owns no persisted state."""

    ready: bool
    rows: tuple[TopologyRoomInventoryRowV1, ...] = ()
    migration_projection_used: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Topology room inventory not resolved"

    @property
    def fixed_heat_source(self) -> TopologyRoomInventoryRowV1 | None:
        return next(
            (
                row
                for row in self.rows
                if row.disposition == FIXED_HEAT_SOURCE_DISPOSITION
            ),
            None,
        )

    @property
    def assigned_rooms(self) -> tuple[TopologyRoomInventoryRowV1, ...]:
        return tuple(
            row
            for row in self.rows
            if row.disposition == ASSIGNED_TOPOLOGY_DISPOSITION
        )

    @property
    def staging_rooms(self) -> tuple[TopologyRoomInventoryRowV1, ...]:
        return tuple(
            row
            for row in self.rows
            if row.disposition == UNASSIGNED_STAGING_DISPOSITION
        )

    @property
    def staging_room_ids(self) -> tuple[str, ...]:
        return tuple(row.room_id for row in self.staging_rooms)

    def require_room(self, room_id: str) -> TopologyRoomInventoryRowV1:
        stable_room_id = str(room_id or "")
        row = next(
            (item for item in self.rows if item.room_id == stable_room_id),
            None,
        )
        if row is None:
            raise KeyError(f"Unknown topology room inventory identity: {room_id}")
        return row


def build_topology_unassigned_room_inventory_v1(
    project_state: Any,
) -> TopologyUnassignedRoomInventoryV1:
    """
    Classify every ProjectState room without mutating ProjectState.

    A room resolves to exactly one disposition:
    - fixed heat source;
    - assigned to one exact recursive subleg and route order;
    - unassigned and therefore available in the future staging tray.
    """

    rooms = getattr(project_state, "rooms", None)
    topology = getattr(project_state, "hydronic_topology", None)
    if not isinstance(rooms, dict):
        return _blocked("ProjectState rooms mapping is required")
    if not isinstance(topology, HydronicTopologyV1):
        return _blocked("Canonical HydronicTopologyV1 is required")

    known_room_ids = tuple(str(room_id) for room_id in rooms)
    validation = validate_canonical_hydronic_topology_v1(
        topology,
        known_room_ids=known_room_ids,
    )
    migration_projection_used = False
    warnings = list(validation.warnings)
    effective_topology = topology
    if not validation.ready:
        migration = migrate_legacy_flat_sublegs_to_canonical_v1(
            topology,
            known_room_ids=known_room_ids,
        )
        if not migration.ready or migration.topology is None:
            return _blocked(
                "Existing topology is neither canonical nor safely migratable",
                *validation.blockers,
                *migration.blockers,
            )
        effective_topology = migration.topology
        migration_projection_used = True
        warnings.extend(migration.warnings)
        warnings.append(
            "Accepted legacy topology was projected through its unambiguous "
            "Principal/Branch migration without mutating ProjectState"
        )

    heat_source_room_id = str(effective_topology.heat_source_room_id or "")
    assignment_by_room_id: dict[str, TopologyRoomInventoryRowV1] = {}
    for position in build_recursive_subleg_positions_v1(effective_topology):
        route_room_ids = tuple(
            str(room_id) for room_id in position.subleg.route_room_ids
        )
        terminal_room_id = route_room_ids[-1] if route_room_ids else ""
        for route_order, room_id in enumerate(route_room_ids, start=1):
            room = rooms.get(room_id)
            assignment_by_room_id[room_id] = TopologyRoomInventoryRowV1(
                room_id=room_id,
                room_label=str(getattr(room, "name", None) or room_id),
                disposition=ASSIGNED_TOPOLOGY_DISPOSITION,
                leg_id=position.leg_id,
                leg_label=position.leg_label,
                subleg_id=position.subleg_id,
                subleg_label=position.subleg_label,
                subleg_kind=position.kind,
                route_order=route_order,
                is_index=(room_id == str(position.subleg.index_room_id or "")),
                is_terminal=(room_id == terminal_room_id),
            )

    inventory_rows: list[TopologyRoomInventoryRowV1] = []
    for room_id, room in rooms.items():
        stable_room_id = str(room_id)
        room_label = str(getattr(room, "name", None) or stable_room_id)
        if stable_room_id == heat_source_room_id:
            inventory_rows.append(
                TopologyRoomInventoryRowV1(
                    room_id=stable_room_id,
                    room_label=room_label,
                    disposition=FIXED_HEAT_SOURCE_DISPOSITION,
                )
            )
        elif stable_room_id in assignment_by_room_id:
            inventory_rows.append(assignment_by_room_id[stable_room_id])
        else:
            inventory_rows.append(
                TopologyRoomInventoryRowV1(
                    room_id=stable_room_id,
                    room_label=room_label,
                    disposition=UNASSIGNED_STAGING_DISPOSITION,
                )
            )

    return TopologyUnassignedRoomInventoryV1(
        ready=True,
        rows=tuple(inventory_rows),
        migration_projection_used=migration_projection_used,
        warnings=_unique(warnings),
        status=(
            "Ready — every room has one exact fixed, assigned or staging "
            "disposition"
        ),
    )


def _blocked(*blockers: str) -> TopologyUnassignedRoomInventoryV1:
    return TopologyUnassignedRoomInventoryV1(
        ready=False,
        blockers=_unique(blockers) or ("Topology room inventory is blocked",),
        status="Blocked — topology room inventory is not trustworthy",
    )


def _unique(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value).strip()))
