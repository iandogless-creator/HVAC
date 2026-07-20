# ======================================================================
# HVAC/hydronics/proportioning/balancing_point_resistance_allocation_v1.py
# H-S44-B — Balancing-point provisional resistance allocation
# ======================================================================

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from HVAC.hydronics.proportioning.balancing_point_topology_authority_v1 import (
    SUBLEG_POINT_SCOPE,
    BalancingPointTopologyProjectionV1,
    BalancingPointTopologyRowV1,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    PreliminaryBalancingResistanceBasisV1,
)


_NUMBER_RE_V1 = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


@dataclass(frozen=True, slots=True)
class BalancingPointResistanceAllocationRowV1:
    """One provisional point allocation; never a selected valve."""

    balancing_point_id: str
    point_scope: str
    point_role: str
    label: str
    parent_balancing_point_id: str
    anchor_section_id: str
    downstream_route_ids: tuple[str, ...]
    is_shared: bool
    is_route_exclusive: bool

    point_flow_kg_s: float | None
    allocated_added_dp_pa: float
    allocated_resistance_pa_per_kg_s2: float | None
    status: str


@dataclass(frozen=True, slots=True)
class BalancingPointRouteConservationRowV1:
    """No-double-counting proof for one canonical H-S43 route burden."""

    route_id: str
    required_added_dp_pa: float
    allocated_path_dp_pa: float
    difference_pa: float
    contributing_balancing_point_ids: tuple[str, ...]
    conserved: bool
    status: str


@dataclass(frozen=True, slots=True)
class BalancingPointResistanceAllocationProjectionV1:
    """
    H-S44-B provisional allocation onto H-S44-A topology points.

    Shared pressure is factored upward once, residual pressure moves downward,
    and every route receives a conservation check. This projection does not
    select a valve, calculate Kv/Kvs, commit balancing, select a pump, resize
    pipework, persist intent, or mutate ProjectState.
    """

    ready: bool
    rows: tuple[BalancingPointResistanceAllocationRowV1, ...]
    route_conservation: tuple[BalancingPointRouteConservationRowV1, ...]
    blockers: tuple[str, ...] = ()
    status: str = "H-S44-B balancing-point allocation not ready"


@dataclass(frozen=True, slots=True)
class _RouteBurdenV1:
    route_id: str
    flow_kg_s: float
    required_added_dp_pa: float


def build_balancing_point_resistance_allocation_v1(
    *,
    topology: BalancingPointTopologyProjectionV1 | None,
    resistance_basis: PreliminaryBalancingResistanceBasisV1 | None,
    dp_tolerance_pa: float = 0.05,
) -> BalancingPointResistanceAllocationProjectionV1:
    """Allocate H-S43 route burdens through the H-S44-A point hierarchy."""

    if topology is None:
        return _blocked_projection("No H-S44-A topology projection is available")
    if not topology.ready:
        return _blocked_projection(
            "H-S44-A topology projection is not ready",
            *tuple(topology.blockers or ()),
        )
    if resistance_basis is None:
        return _blocked_projection("No H-S43 resistance basis is available")
    if not resistance_basis.ready:
        return _blocked_projection(
            "H-S43 resistance basis is not ready",
            *tuple(resistance_basis.blockers or ()),
        )
    if dp_tolerance_pa < 0.0:
        return _blocked_projection("dp_tolerance_pa must be zero or greater")

    points = tuple(topology.points or ())
    point_blockers, ordered_points, children_by_id = _validate_point_tree_v1(
        points
    )
    if point_blockers:
        return _blocked_projection(*point_blockers)

    topology_route_ids = _ordered_union(
        point.downstream_route_ids for point in points
    )
    burdens, burden_blockers = _route_burdens_v1(
        resistance_basis,
        topology_route_ids=topology_route_ids,
        dp_tolerance_pa=dp_tolerance_pa,
    )
    if burden_blockers:
        return _blocked_projection(*burden_blockers)

    point_by_id = {point.balancing_point_id: point for point in points}
    burden_by_route = {burden.route_id: burden for burden in burdens}
    point_flow_by_id: dict[str, float] = {}
    flow_blockers: list[str] = []

    def point_flow(point_id: str) -> float | None:
        if point_id in point_flow_by_id:
            return point_flow_by_id[point_id]
        point = point_by_id[point_id]
        if point.point_scope == SUBLEG_POINT_SCOPE:
            burden = burden_by_route.get(point.subleg_id)
            value = burden.flow_kg_s if burden is not None else None
        else:
            child_values = [point_flow(child_id) for child_id in children_by_id[point_id]]
            value = (
                sum(float(item) for item in child_values if item is not None)
                if child_values and all(item is not None for item in child_values)
                else None
            )
        if value is None or value <= 0.0:
            flow_blockers.append(
                f"{point.balancing_point_id}: positive point flow unavailable"
            )
            return None
        point_flow_by_id[point_id] = float(value)
        return float(value)

    for point in reversed(ordered_points):
        point_flow(point.balancing_point_id)
    if flow_blockers:
        return _blocked_projection(*_deduplicate(flow_blockers))

    residual_by_route = {
        burden.route_id: burden.required_added_dp_pa for burden in burdens
    }
    allocation_by_point: dict[str, float] = {}
    rows: list[BalancingPointResistanceAllocationRowV1] = []

    for point in ordered_points:
        governed = tuple(point.downstream_route_ids or ())
        allocation = min(residual_by_route[route_id] for route_id in governed)
        if allocation <= dp_tolerance_pa:
            allocation = 0.0
        for route_id in governed:
            residual_by_route[route_id] = max(
                0.0,
                residual_by_route[route_id] - allocation,
            )
        allocation_by_point[point.balancing_point_id] = allocation
        flow = point_flow_by_id[point.balancing_point_id]
        resistance = allocation / (flow ** 2)
        rows.append(
            BalancingPointResistanceAllocationRowV1(
                balancing_point_id=point.balancing_point_id,
                point_scope=point.point_scope,
                point_role=point.point_role,
                label=point.label,
                parent_balancing_point_id=point.parent_balancing_point_id,
                anchor_section_id=point.anchor_section_id,
                downstream_route_ids=governed,
                is_shared=point.is_shared,
                is_route_exclusive=point.is_route_exclusive,
                point_flow_kg_s=flow,
                allocated_added_dp_pa=allocation,
                allocated_resistance_pa_per_kg_s2=resistance,
                status=(
                    "Shared provisional burden allocated once"
                    if allocation > 0.0 and point.is_shared
                    else "Route-exclusive residual burden allocated"
                    if allocation > 0.0
                    else "No residual burden allocated at this point"
                ),
            )
        )

    conservation: list[BalancingPointRouteConservationRowV1] = []
    blockers: list[str] = []
    for burden in burdens:
        contributors = tuple(
            point.balancing_point_id
            for point in ordered_points
            if burden.route_id in point.downstream_route_ids
            and allocation_by_point[point.balancing_point_id] > 0.0
        )
        allocated = sum(allocation_by_point[point_id] for point_id in contributors)
        difference = burden.required_added_dp_pa - allocated
        conserved = abs(difference) <= dp_tolerance_pa
        conservation.append(
            BalancingPointRouteConservationRowV1(
                route_id=burden.route_id,
                required_added_dp_pa=burden.required_added_dp_pa,
                allocated_path_dp_pa=allocated,
                difference_pa=difference,
                contributing_balancing_point_ids=contributors,
                conserved=conserved,
                status=(
                    "Conserved — source route burden allocated exactly once"
                    if conserved
                    else "Blocked — topology cannot represent route residual"
                ),
            )
        )
        if not conserved:
            blockers.append(
                f"{burden.route_id}: unallocated residual {difference:.3f} Pa"
            )

    ready = not blockers
    return BalancingPointResistanceAllocationProjectionV1(
        ready=ready,
        rows=tuple(rows),
        route_conservation=tuple(conservation),
        blockers=tuple(blockers),
        status=(
            "H-S44-B balancing-point resistance allocation ready"
            if ready
            else "H-S44-B allocation blocked — route burden not conserved"
        ),
    )


def _route_burdens_v1(
    resistance_basis: PreliminaryBalancingResistanceBasisV1,
    *,
    topology_route_ids: tuple[str, ...],
    dp_tolerance_pa: float,
) -> tuple[tuple[_RouteBurdenV1, ...], tuple[str, ...]]:
    rows = tuple(resistance_basis.rows or ())
    blockers: list[str] = []
    rows_by_id: dict[str, object] = {}
    for row in rows:
        route_id = str(_row_value(row, "route_id", "") or "").strip()
        if not route_id:
            blockers.append("Every H-S43 resistance row requires route_id")
        elif route_id in rows_by_id:
            blockers.append(f"Duplicate H-S43 route_id: {route_id}")
        else:
            rows_by_id[route_id] = row

    missing = tuple(route_id for route_id in topology_route_ids if route_id not in rows_by_id)
    extra = tuple(route_id for route_id in rows_by_id if route_id not in topology_route_ids)
    if missing:
        blockers.append("H-S43 route burdens missing for: " + ", ".join(missing))
    if extra:
        blockers.append("H-S43 route burdens not present in topology: " + ", ".join(extra))

    burdens: list[_RouteBurdenV1] = []
    for route_id in topology_route_ids:
        row = rows_by_id.get(route_id)
        if row is None:
            continue
        flow = _number(_row_value(row, "flow_kg_s", None))
        added_dp = _number(_row_value(row, "required_added_dp", None))
        if flow is None or flow <= 0.0:
            blockers.append(f"{route_id}: positive H-S43 route flow required")
        if added_dp is None:
            blockers.append(f"{route_id}: H-S43 required added Δp unavailable")
        elif added_dp < -dp_tolerance_pa:
            blockers.append(f"{route_id}: required added Δp cannot be negative")
        if flow is not None and flow > 0.0 and added_dp is not None and added_dp >= -dp_tolerance_pa:
            burdens.append(
                _RouteBurdenV1(
                    route_id=route_id,
                    flow_kg_s=flow,
                    required_added_dp_pa=max(0.0, added_dp),
                )
            )
    return tuple(burdens), tuple(blockers)


def _validate_point_tree_v1(
    points: tuple[BalancingPointTopologyRowV1, ...],
) -> tuple[
    tuple[str, ...],
    tuple[BalancingPointTopologyRowV1, ...],
    dict[str, tuple[str, ...]],
]:
    if not points:
        return ("H-S44-A topology has no balancing points",), (), {}
    ids = tuple(point.balancing_point_id for point in points)
    blockers: list[str] = []
    if any(not point_id for point_id in ids):
        blockers.append("Every topology point requires balancing_point_id")
    duplicates = sorted({point_id for point_id in ids if ids.count(point_id) > 1})
    if duplicates:
        blockers.append("Duplicate balancing_point_id values: " + ", ".join(duplicates))
    point_by_id = {point.balancing_point_id: point for point in points}
    children: dict[str, list[str]] = {point_id: [] for point_id in point_by_id}
    for point in points:
        if not point.downstream_route_ids:
            blockers.append(f"{point.balancing_point_id}: no governed routes")
        parent_id = point.parent_balancing_point_id
        if parent_id:
            if parent_id not in point_by_id:
                blockers.append(f"{point.balancing_point_id}: parent point unresolved")
            else:
                children[parent_id].append(point.balancing_point_id)
    if blockers:
        return tuple(blockers), (), {key: tuple(value) for key, value in children.items()}

    depth_by_id: dict[str, int] = {}
    visiting: set[str] = set()
    def depth(point_id: str) -> int:
        if point_id in depth_by_id:
            return depth_by_id[point_id]
        if point_id in visiting:
            raise ValueError(point_id)
        visiting.add(point_id)
        parent_id = point_by_id[point_id].parent_balancing_point_id
        value = 0 if not parent_id else depth(parent_id) + 1
        visiting.remove(point_id)
        depth_by_id[point_id] = value
        return value
    try:
        for point_id in point_by_id:
            depth(point_id)
    except ValueError as exc:
        return (f"Balancing-point parent cycle at {exc.args[0]}",), (), {}
    original_order = {point.balancing_point_id: index for index, point in enumerate(points)}
    ordered = tuple(
        sorted(points, key=lambda point: (depth_by_id[point.balancing_point_id], original_order[point.balancing_point_id]))
    )
    return (), ordered, {key: tuple(value) for key, value in children.items()}


def _row_value(row: object, name: str, default=None):
    if isinstance(row, dict):
        return row.get(name, default)
    return getattr(row, name, default)


def _number(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text or text in {"—", "-", "None", "none", "null"}:
        return None
    match = _NUMBER_RE_V1.search(text)
    if match is None:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _ordered_union(groups: Iterable[Iterable[str]]) -> tuple[str, ...]:
    result: list[str] = []
    for group in groups:
        for raw_value in group:
            value = str(raw_value or "").strip()
            if value and value not in result:
                result.append(value)
    return tuple(result)


def _deduplicate(values: Iterable[str]) -> tuple[str, ...]:
    return _ordered_union((values,))


def _blocked_projection(
    *blockers: str,
) -> BalancingPointResistanceAllocationProjectionV1:
    return BalancingPointResistanceAllocationProjectionV1(
        ready=False,
        rows=(),
        route_conservation=(),
        blockers=tuple(str(blocker) for blocker in blockers if str(blocker)),
        status="H-S44-B balancing-point allocation not ready",
    )
