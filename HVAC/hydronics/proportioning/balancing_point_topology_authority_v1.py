# ======================================================================
# HVAC/hydronics/proportioning/balancing_point_topology_authority_v1.py
# H-S44-A — Main / leg / subleg balancing-point topology authority
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from HVAC.hydronics.proportioning.common_main_leg_entry_sections_v1 import (
    common_main_section_id_for_leg_v1,
    leg_entry_section_id_for_leg_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)


MAIN_POINT_SCOPE = "main"
LEG_POINT_SCOPE = "leg"
SUBLEG_POINT_SCOPE = "subleg"

COMMON_SUBLEG_ROLE = "common"
BRANCH_SUBLEG_ROLE = "branch"
COMMON_ROUTE_DOWNSTREAM_ROLE = "common_route_downstream"


@dataclass(frozen=True, slots=True)
class BalancingPointTopologyRowV1:
    """One stable read-only balancing-point topology anchor."""

    balancing_point_id: str
    point_scope: str
    point_role: str
    label: str

    leg_id: str
    subleg_id: str
    parent_balancing_point_id: str
    anchor_section_id: str
    origin_room_id: str

    downstream_route_ids: tuple[str, ...]
    is_shared: bool
    is_route_exclusive: bool
    status: str


@dataclass(frozen=True, slots=True)
class BalancingPointTopologyProjectionV1:
    """
    H-S44-A balancing-point topology authority.

    The persisted leg order and nested subleg tree are authoritative. This
    projection identifies where later provisional resistance may be scoped;
    it does not allocate resistance, select valves, calculate Kv/Kvs, resize
    pipe, select a pump, commit balancing, or mutate ProjectState.
    """

    ready: bool
    points: tuple[BalancingPointTopologyRowV1, ...]
    main_points: tuple[BalancingPointTopologyRowV1, ...]
    leg_points: tuple[BalancingPointTopologyRowV1, ...]
    subleg_points: tuple[BalancingPointTopologyRowV1, ...]
    # H-S44-A2: additional conceptual route-exclusive children. Existing
    # subleg_points remain the unchanged physical entry-point authority.
    route_exclusive_points: tuple[BalancingPointTopologyRowV1, ...] = ()
    blockers: tuple[str, ...] = ()
    status: str = "H-S44-A balancing-point topology not ready"


@dataclass(frozen=True, slots=True)
class _SublegInfoV1:
    leg: HydronicLegV1
    subleg: HydronicSublegV1
    parent_subleg_id: str
    is_primary: bool


def main_balancing_point_id_v1(leg_id: str) -> str:
    return f"balancing-point:main:{str(leg_id or '').strip()}"


def leg_balancing_point_id_v1(leg_id: str) -> str:
    return f"balancing-point:leg:{str(leg_id or '').strip()}"


def subleg_balancing_point_id_v1(subleg_id: str) -> str:
    return f"balancing-point:subleg:{str(subleg_id or '').strip()}"


def common_subleg_downstream_balancing_point_id_v1(subleg_id: str) -> str:
    """Stable identity for a common route's exclusive residual point."""
    stable_id = str(subleg_id or '').strip()
    return f"balancing-point:subleg:{stable_id}:downstream-exclusive"


def build_balancing_point_topology_authority_v1(
    project_state: Any,
) -> BalancingPointTopologyProjectionV1:
    """Build stable main, leg and subleg balancing-point identities."""

    if project_state is None:
        return _blocked_projection("No project_state is available")

    topology = getattr(project_state, "hydronic_topology", None)
    if not isinstance(topology, HydronicTopologyV1):
        return _blocked_projection(
            "project_state.hydronic_topology is not HydronicTopologyV1"
        )

    legs = tuple(topology.legs or ())
    if not legs:
        return _blocked_projection("Hydronic topology has no persisted legs")

    blockers = _validate_topology_v1(legs)
    if blockers:
        return _blocked_projection(*blockers)

    infos_by_leg: dict[str, tuple[_SublegInfoV1, ...]] = {
        leg.leg_id: tuple(_flatten_leg_sublegs_v1(leg)) for leg in legs
    }
    route_ids_by_leg: dict[str, tuple[str, ...]] = {
        leg_id: tuple(info.subleg.subleg_id for info in infos)
        for leg_id, infos in infos_by_leg.items()
    }

    main_points: list[BalancingPointTopologyRowV1] = []
    leg_points: list[BalancingPointTopologyRowV1] = []
    subleg_points: list[BalancingPointTopologyRowV1] = []
    route_exclusive_points: list[BalancingPointTopologyRowV1] = []

    previous_main_point_id = ""
    for index, leg in enumerate(legs):
        downstream_leg_ids = tuple(item.leg_id for item in legs[index:])
        downstream_route_ids = _ordered_union(
            route_ids_by_leg[leg_id] for leg_id in downstream_leg_ids
        )
        main_point_id = main_balancing_point_id_v1(leg.leg_id)
        main_points.append(
            _point_v1(
                balancing_point_id=main_point_id,
                point_scope=MAIN_POINT_SCOPE,
                point_role="common_main_takeoff",
                label=f"Common main to {leg.label} take-off",
                leg_id=leg.leg_id,
                subleg_id="",
                parent_balancing_point_id=previous_main_point_id,
                anchor_section_id=common_main_section_id_for_leg_v1(leg.leg_id),
                origin_room_id="",
                downstream_route_ids=downstream_route_ids,
                status=(
                    "Persisted leg-order main point; governs this and all "
                    "downstream leg routes"
                ),
            )
        )
        previous_main_point_id = main_point_id

        leg_route_ids = route_ids_by_leg[leg.leg_id]
        leg_point_id = leg_balancing_point_id_v1(leg.leg_id)
        leg_points.append(
            _point_v1(
                balancing_point_id=leg_point_id,
                point_scope=LEG_POINT_SCOPE,
                point_role="leg_entry",
                label=f"{leg.label} entry",
                leg_id=leg.leg_id,
                subleg_id="",
                parent_balancing_point_id=main_point_id,
                anchor_section_id=leg_entry_section_id_for_leg_v1(leg.leg_id),
                origin_room_id="",
                downstream_route_ids=leg_route_ids,
                status="Whole-leg balancing point at stable leg entry",
            )
        )

        descendants_by_subleg = _descendant_route_ids_v1(
            infos_by_leg[leg.leg_id]
        )
        for info in infos_by_leg[leg.leg_id]:
            subleg = info.subleg
            parent_point_id = (
                subleg_balancing_point_id_v1(info.parent_subleg_id)
                if info.parent_subleg_id
                else leg_point_id
            )
            entry_point_id = subleg_balancing_point_id_v1(subleg.subleg_id)
            governed_route_ids = descendants_by_subleg[subleg.subleg_id]
            subleg_points.append(
                _point_v1(
                    balancing_point_id=entry_point_id,
                    point_scope=SUBLEG_POINT_SCOPE,
                    point_role=(
                        COMMON_SUBLEG_ROLE if info.is_primary else BRANCH_SUBLEG_ROLE
                    ),
                    label=f"{leg.label} / {subleg.label} entry",
                    leg_id=leg.leg_id,
                    subleg_id=subleg.subleg_id,
                    parent_balancing_point_id=parent_point_id,
                    anchor_section_id=f"{subleg.subleg_id}-section-001",
                    origin_room_id=str(subleg.origin_room_id or ""),
                    downstream_route_ids=governed_route_ids,
                    status=(
                        "Primary/common subleg entry point"
                        if info.is_primary
                        else "Branch subleg entry point at persisted take-off"
                    ),
                )
            )

            # H-S44-A2: a common entry that also feeds child routes is shared.
            # Add a distinct child for the common route's residual burden. The
            # point is deliberately not tied to a pipe section: branch take-off
            # geometry remains TBA, so physical valve placement is not inferred.
            if info.is_primary and len(governed_route_ids) > 1:
                route_exclusive_points.append(
                    _point_v1(
                        balancing_point_id=(
                            common_subleg_downstream_balancing_point_id_v1(
                                subleg.subleg_id
                            )
                        ),
                        point_scope=SUBLEG_POINT_SCOPE,
                        point_role=COMMON_ROUTE_DOWNSTREAM_ROLE,
                        label=f"{leg.label} / {subleg.label} downstream route",
                        leg_id=leg.leg_id,
                        subleg_id=subleg.subleg_id,
                        parent_balancing_point_id=entry_point_id,
                        anchor_section_id="",
                        origin_room_id="",
                        downstream_route_ids=(subleg.subleg_id,),
                        status=(
                            "Route-exclusive common-subleg residual point; "
                            "physical placement TBA"
                        ),
                    )
                )

    points = tuple(
        main_points + leg_points + subleg_points + route_exclusive_points
    )
    return BalancingPointTopologyProjectionV1(
        ready=True,
        points=points,
        main_points=tuple(main_points),
        leg_points=tuple(leg_points),
        subleg_points=tuple(subleg_points),
        route_exclusive_points=tuple(route_exclusive_points),
        blockers=(),
        status="H-S44-A main / leg / subleg balancing-point topology ready",
    )


def _point_v1(
    *,
    balancing_point_id: str,
    point_scope: str,
    point_role: str,
    label: str,
    leg_id: str,
    subleg_id: str,
    parent_balancing_point_id: str,
    anchor_section_id: str,
    origin_room_id: str,
    downstream_route_ids: tuple[str, ...],
    status: str,
) -> BalancingPointTopologyRowV1:
    route_count = len(downstream_route_ids)
    return BalancingPointTopologyRowV1(
        balancing_point_id=balancing_point_id,
        point_scope=point_scope,
        point_role=point_role,
        label=label,
        leg_id=leg_id,
        subleg_id=subleg_id,
        parent_balancing_point_id=parent_balancing_point_id,
        anchor_section_id=anchor_section_id,
        origin_room_id=origin_room_id,
        downstream_route_ids=downstream_route_ids,
        is_shared=route_count > 1,
        is_route_exclusive=route_count == 1,
        status=status,
    )


def _flatten_leg_sublegs_v1(leg: HydronicLegV1) -> list[_SublegInfoV1]:
    primary_id = primary_subleg_id_for_leg(leg.leg_id)
    has_primary = any(subleg.subleg_id == primary_id for subleg in leg.sublegs)
    result: list[_SublegInfoV1] = []

    def walk(subleg: HydronicSublegV1, parent_subleg_id: str) -> None:
        result.append(
            _SublegInfoV1(
                leg=leg,
                subleg=subleg,
                parent_subleg_id=parent_subleg_id,
                is_primary=subleg.subleg_id == primary_id,
            )
        )
        for child in subleg.sublegs:
            walk(child, subleg.subleg_id)

    for subleg in leg.sublegs:
        parent_id = ""
        if subleg.subleg_id != primary_id and has_primary:
            parent_id = primary_id
        walk(subleg, parent_id)

    return result


def _descendant_route_ids_v1(
    infos: tuple[_SublegInfoV1, ...],
) -> dict[str, tuple[str, ...]]:
    children: dict[str, list[str]] = {
        info.subleg.subleg_id: [] for info in infos
    }
    for info in infos:
        if info.parent_subleg_id:
            children[info.parent_subleg_id].append(info.subleg.subleg_id)

    def descendants(subleg_id: str) -> tuple[str, ...]:
        return (subleg_id,) + _ordered_union(
            descendants(child_id) for child_id in children[subleg_id]
        )

    return {
        subleg_id: descendants(subleg_id) for subleg_id in children
    }


def _validate_topology_v1(
    legs: tuple[HydronicLegV1, ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    leg_ids = tuple(str(leg.leg_id or "").strip() for leg in legs)
    if any(not leg_id for leg_id in leg_ids):
        blockers.append("Every persisted leg requires a stable leg_id")
    duplicate_leg_ids = sorted(
        {leg_id for leg_id in leg_ids if leg_id and leg_ids.count(leg_id) > 1}
    )
    if duplicate_leg_ids:
        blockers.append(
            "Persisted leg_id values must be unique: "
            + ", ".join(duplicate_leg_ids)
        )

    all_subleg_ids: list[str] = []
    for leg in legs:
        infos = _flatten_leg_sublegs_v1(leg)
        if not infos:
            blockers.append(f"{leg.leg_id}: no persisted subleg routes")
            continue
        for info in infos:
            subleg_id = str(info.subleg.subleg_id or "").strip()
            if not subleg_id:
                blockers.append(f"{leg.leg_id}: every subleg requires a stable subleg_id")
            else:
                all_subleg_ids.append(subleg_id)

            if info.parent_subleg_id:
                parent = next(
                    (
                        item.subleg
                        for item in infos
                        if item.subleg.subleg_id == info.parent_subleg_id
                    ),
                    None,
                )
                origin = str(info.subleg.origin_room_id or "").strip()
                if parent is None:
                    blockers.append(
                        f"{subleg_id}: parent subleg {info.parent_subleg_id} unresolved"
                    )
                elif not origin or origin not in tuple(parent.route_room_ids or ()):
                    blockers.append(
                        f"{subleg_id}: origin_room_id is not on parent subleg route"
                    )

    duplicate_subleg_ids = sorted(
        {
            subleg_id
            for subleg_id in all_subleg_ids
            if all_subleg_ids.count(subleg_id) > 1
        }
    )
    if duplicate_subleg_ids:
        blockers.append(
            "Persisted subleg_id values must be globally unique: "
            + ", ".join(duplicate_subleg_ids)
        )
    return tuple(blockers)


def _ordered_union(groups: Iterable[Iterable[str]]) -> tuple[str, ...]:
    result: list[str] = []
    for group in groups:
        for raw_value in group:
            value = str(raw_value or "").strip()
            if value and value not in result:
                result.append(value)
    return tuple(result)


def _blocked_projection(
    *blockers: str,
) -> BalancingPointTopologyProjectionV1:
    return BalancingPointTopologyProjectionV1(
        ready=False,
        points=(),
        main_points=(),
        leg_points=(),
        subleg_points=(),
        route_exclusive_points=(),
        blockers=tuple(blockers),
        status="H-S44-A balancing-point topology not ready",
    )
