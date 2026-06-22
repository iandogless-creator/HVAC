# ======================================================================
# HVAC/hydronics/proportioning/branch_takeoff_room_allocation_basis_v1.py
# H-S24-B — Branch take-off / room allocation basis
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)


@dataclass(frozen=True, slots=True)
class BranchTakeoffRoomAllocationBasisRowV1:
    """
    Read-only topology/setup basis row.

    This describes how the user/topology has allocated rooms to sublegs
    and where branch sublegs currently originate/take off.

    It does not calculate pipe pressure or balancing.
    """

    leg_id: str
    leg_label: str

    subleg_id: str
    subleg_label: str
    subleg_kind: str

    parent_leg_id: str
    parent_subleg_id: str

    takeoff_room_id: str
    takeoff_basis: str

    ordered_room_ids: tuple[str, ...]
    room_count: int
    terminal_room_id: str

    rollup_basis: str
    status: str


@dataclass(frozen=True, slots=True)
class BranchTakeoffRoomAllocationBasisV1:
    """
    Preview-only branch take-off / room allocation basis.

    Authority boundary:
    • reads HydronicTopologyV1 only
    • no ProjectState mutation
    • no pipe graph generation
    • no pressure calculation
    • no balancing commit
    • no valve selection
    • no pump sizing
    • no pipe resizing
    """

    ready: bool = False
    status: str = "Branch take-off / room allocation basis not ready"
    rows: tuple[BranchTakeoffRoomAllocationBasisRowV1, ...] = ()
    blockers: tuple[str, ...] = ()


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _subleg_kind(
    *,
    leg_id: str,
    subleg: HydronicSublegV1,
    parent_subleg_id: str,
) -> str:
    if subleg.subleg_id == primary_subleg_id_for_leg(leg_id):
        return "primary/common subleg"

    if parent_subleg_id:
        return "branch subleg"

    return "subleg"


def _takeoff_basis(
    *,
    subleg_kind: str,
    takeoff_room_id: str,
) -> str:
    if subleg_kind == "primary/common subleg":
        return "common main / leg entry"

    if takeoff_room_id:
        return "origin_room_id / branch take-off basis"

    return "TBD"


def _rollup_basis(
    *,
    subleg_kind: str,
    parent_subleg_id: str,
    takeoff_room_id: str,
) -> str:
    if subleg_kind == "primary/common subleg":
        return "Primary route carries its downstream allocation"

    if parent_subleg_id and takeoff_room_id:
        return (
            "Branch rolls up to parent subleg at take-off; "
            "parent carries branch flow only up to that point"
        )

    if parent_subleg_id:
        return (
            "Branch rolls up to parent subleg; take-off point TBD, "
            "parent section flow provisional"
        )

    return "Roll-up basis unresolved"


def _status(
    *,
    subleg_kind: str,
    parent_subleg_id: str,
    takeoff_room_id: str,
    ordered_room_ids: tuple[str, ...],
) -> str:
    if not ordered_room_ids:
        return "No rooms allocated to subleg"

    if subleg_kind == "primary/common subleg":
        return "Primary subleg room allocation ready"

    if parent_subleg_id and takeoff_room_id:
        return "Branch take-off basis ready"

    if parent_subleg_id:
        return "Branch parent known — take-off TBD"

    return "Subleg parent/take-off basis unresolved"


def _row_for_subleg(
    *,
    leg: HydronicLegV1,
    subleg: HydronicSublegV1,
    parent_subleg_id: str,
) -> BranchTakeoffRoomAllocationBasisRowV1:
    ordered_room_ids = tuple(str(room_id) for room_id in subleg.route_room_ids)
    terminal_room_id = ordered_room_ids[-1] if ordered_room_ids else ""

    kind = _subleg_kind(
        leg_id=leg.leg_id,
        subleg=subleg,
        parent_subleg_id=parent_subleg_id,
    )

    takeoff_room_id = _clean_text(subleg.origin_room_id)

    return BranchTakeoffRoomAllocationBasisRowV1(
        leg_id=leg.leg_id,
        leg_label=leg.label,
        subleg_id=subleg.subleg_id,
        subleg_label=subleg.label,
        subleg_kind=kind,
        parent_leg_id=leg.leg_id,
        parent_subleg_id=parent_subleg_id,
        takeoff_room_id=takeoff_room_id,
        takeoff_basis=_takeoff_basis(
            subleg_kind=kind,
            takeoff_room_id=takeoff_room_id,
        ),
        ordered_room_ids=ordered_room_ids,
        room_count=len(ordered_room_ids),
        terminal_room_id=terminal_room_id,
        rollup_basis=_rollup_basis(
            subleg_kind=kind,
            parent_subleg_id=parent_subleg_id,
            takeoff_room_id=takeoff_room_id,
        ),
        status=_status(
            subleg_kind=kind,
            parent_subleg_id=parent_subleg_id,
            takeoff_room_id=takeoff_room_id,
            ordered_room_ids=ordered_room_ids,
        ),
    )


def _walk_sublegs(
    *,
    leg: HydronicLegV1,
    subleg: HydronicSublegV1,
    parent_subleg_id: str,
    rows: list[BranchTakeoffRoomAllocationBasisRowV1],
) -> None:
    rows.append(
        _row_for_subleg(
            leg=leg,
            subleg=subleg,
            parent_subleg_id=parent_subleg_id,
        )
    )

    for child in subleg.sublegs:
        _walk_sublegs(
            leg=leg,
            subleg=child,
            parent_subleg_id=subleg.subleg_id,
            rows=rows,
        )


def build_branch_takeoff_room_allocation_basis_v1(
    project_state: Any,
) -> BranchTakeoffRoomAllocationBasisV1:
    """
    Build H-S24-B branch take-off / room allocation basis.

    This is the setup truth layer before accurate branch section-flow
    roll-up can be used for balancing duty.
    """

    if project_state is None:
        return BranchTakeoffRoomAllocationBasisV1(
            ready=False,
            blockers=("No project_state is available",),
        )

    topology = getattr(project_state, "hydronic_topology", None)

    if topology is None:
        return BranchTakeoffRoomAllocationBasisV1(
            ready=False,
            blockers=("No hydronic topology is available",),
        )

    if not isinstance(topology, HydronicTopologyV1):
        return BranchTakeoffRoomAllocationBasisV1(
            ready=False,
            blockers=("project_state.hydronic_topology is not HydronicTopologyV1",),
        )

    rows: list[BranchTakeoffRoomAllocationBasisRowV1] = []

    for leg in topology.legs:
        for subleg in leg.sublegs:
            _walk_sublegs(
                leg=leg,
                subleg=subleg,
                parent_subleg_id="",
                rows=rows,
            )

    blockers: list[str] = []

    if not rows:
        blockers.append("No sublegs are defined")

    for row in rows:
        if row.status in {
            "No rooms allocated to subleg",
            "Subleg parent/take-off basis unresolved",
        }:
            blockers.append(f"{row.subleg_label}: {row.status}")

    ready = not blockers

    return BranchTakeoffRoomAllocationBasisV1(
        ready=ready,
        status=(
            "Branch take-off / room allocation basis ready"
            if ready
            else "Branch take-off / room allocation basis incomplete"
        ),
        rows=tuple(rows),
        blockers=tuple(blockers),
    )
