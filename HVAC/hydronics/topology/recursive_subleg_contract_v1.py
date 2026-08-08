from __future__ import annotations

from dataclasses import dataclass

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicSublegV1,
    HydronicTopologyV1,
)


PRINCIPAL_SUBLEG_KIND = "principal"
BRANCH_SUBLEG_KIND = "branch"


@dataclass(frozen=True, slots=True)
class RecursiveSublegPositionV1:
    """One derived position in the canonical recursive subleg tree."""

    leg_id: str
    leg_label: str
    subleg: HydronicSublegV1
    kind: str
    parent_subleg_id: str | None
    depth: int
    ancestor_subleg_ids: tuple[str, ...]
    is_leaf: bool

    @property
    def subleg_id(self) -> str:
        return self.subleg.subleg_id

    @property
    def subleg_label(self) -> str:
        return self.subleg.label


def build_recursive_subleg_positions_v1(
    topology: HydronicTopologyV1,
) -> tuple[RecursiveSublegPositionV1, ...]:
    """
    Traverse the canonical Leg -> Principal -> Branch grammar.

    Position is authoritative for terminology:
    - every top-level subleg beneath a leg is principal;
    - every nested subleg is branch;
    - leaf status is derived from the current child collection.

    This is a read-only contract projection. Full identity, membership and
    origin validation belongs to H-S67-C.
    """

    if not isinstance(topology, HydronicTopologyV1):
        raise TypeError("topology must be HydronicTopologyV1")

    positions: list[RecursiveSublegPositionV1] = []
    active_object_ids: set[int] = set()

    def walk(
        *,
        leg_id: str,
        leg_label: str,
        subleg: HydronicSublegV1,
        parent_subleg_id: str | None,
        ancestors: tuple[str, ...],
    ) -> None:
        object_id = id(subleg)
        if object_id in active_object_ids:
            raise ValueError(
                f"Recursive subleg cycle encountered at {subleg.subleg_id!r}"
            )

        active_object_ids.add(object_id)
        try:
            depth = len(ancestors)
            positions.append(
                RecursiveSublegPositionV1(
                    leg_id=leg_id,
                    leg_label=leg_label,
                    subleg=subleg,
                    kind=(
                        PRINCIPAL_SUBLEG_KIND
                        if parent_subleg_id is None
                        else BRANCH_SUBLEG_KIND
                    ),
                    parent_subleg_id=parent_subleg_id,
                    depth=depth,
                    ancestor_subleg_ids=ancestors,
                    is_leaf=subleg.is_leaf,
                )
            )

            child_ancestors = (*ancestors, subleg.subleg_id)
            for child in subleg.sublegs:
                walk(
                    leg_id=leg_id,
                    leg_label=leg_label,
                    subleg=child,
                    parent_subleg_id=subleg.subleg_id,
                    ancestors=child_ancestors,
                )
        finally:
            active_object_ids.remove(object_id)

    for leg in topology.legs:
        for principal_subleg in leg.sublegs:
            walk(
                leg_id=leg.leg_id,
                leg_label=leg.label,
                subleg=principal_subleg,
                parent_subleg_id=None,
                ancestors=(),
            )

    return tuple(positions)
