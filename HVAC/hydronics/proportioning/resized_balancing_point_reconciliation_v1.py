from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Optional

from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import (
    ProportionedPipeResizingHydraulicProjectionV1,
)


CONSERVATION_TOLERANCE_PA = 0.05


@dataclass(frozen=True, slots=True)
class ResizedBalancingPointReconciliationRowV1:
    """Reconciled duty for one frozen committed balancing-point identity."""

    balancing_point_id: str
    point_scope: str
    point_role: str
    label: str
    parent_balancing_point_id: str
    anchor_section_id: str
    allocation_route_ids: tuple[str, ...]
    projected_route_ids: tuple[str, ...]
    is_shared: bool
    is_route_exclusive: bool
    point_flow_kg_s: float

    previous_allocated_dp_Pa: float
    previous_resistance_Pa_per_kg_s2: float
    reconciled_allocated_dp_Pa: float
    reconciled_resistance_Pa_per_kg_s2: float
    allocation_change_dp_Pa: float
    valve_duty_required: bool
    status: str


@dataclass(frozen=True, slots=True)
class ResizedBalancingRouteReconciliationRowV1:
    """Conservation check for one resized route shortfall."""

    projected_route_id: str
    allocation_route_id: str
    resized_hydraulic_dp_Pa: float
    controlling_target_Pa: float
    required_added_dp_Pa: float
    allocated_path_dp_Pa: float
    residual_Pa: float
    contributing_balancing_point_ids: tuple[str, ...]
    conserved: bool
    status: str


@dataclass(frozen=True, slots=True)
class ResizedBalancingPointReconciliationV1:
    """
    H-S61-D balancing-point reconciliation for resized route shortfalls.

    Point identities, scopes, hierarchy and governed routes come from the
    committed H-S56-A allocation authority.  Former point duty values are
    evidence only: new duties are derived from H-S61-C route shortfalls.
    """

    schema: str = "resized_balancing_point_reconciliation_v1"
    ready: bool = False
    point_rows: tuple[ResizedBalancingPointReconciliationRowV1, ...] = ()
    route_rows: tuple[ResizedBalancingRouteReconciliationRowV1, ...] = ()
    point_count: int = 0
    route_count: int = 0
    valve_duty_point_count: int = 0
    status: str = ""
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No ProjectState mutation",
        "No committed point-allocation replacement",
        "No committed DN replacement",
        "No accepted generic Kvs reuse or selection",
        "No valve product or setting selection",
        "No pump selection",
        "No final balancing",
    )
    note: str = (
        "Read-only reconciliation — committed point topology is retained "
        "while resized route shortfalls receive newly derived point duties."
    )


def _blocked_v1(
        status: str,
        *blockers: str,
) -> ResizedBalancingPointReconciliationV1:
    return ResizedBalancingPointReconciliationV1(
        status=status,
        blockers=tuple(blockers),
    )


def _normalise_pa_v1(value: float) -> float:
    value = float(value)
    return 0.0 if abs(value) < CONSERVATION_TOLERANCE_PA else value


def _text_v1(value: Any) -> str:
    return str(value or "").strip()


def _float_attr_v1(
        row: Any,
        *names: str,
        default: float = 0.0,
) -> float:
    for name in names:
        if hasattr(row, name):
            value = getattr(row, name)
            if value is not None:
                return float(value)
    return float(default)


def _route_token_v1(route_id: Any) -> str:
    value = _text_v1(route_id)
    return value.rsplit(":", 1)[-1]


def _authority_route_ids_v1(authority: Any) -> tuple[str, ...]:
    result: list[str] = []
    for row in tuple(getattr(authority, "route_conservation", ()) or ()):
        route_id = _text_v1(getattr(row, "route_id", ""))
        if route_id and route_id not in result:
            result.append(route_id)
    for point in tuple(getattr(authority, "rows", ()) or ()):
        for raw_route_id in tuple(
                getattr(point, "downstream_route_ids", ()) or ()
        ):
            route_id = _text_v1(raw_route_id)
            if route_id and route_id not in result:
                result.append(route_id)
    return tuple(result)


def _match_routes_v1(
        projection: ProportionedPipeResizingHydraulicProjectionV1,
        allocation_route_ids: tuple[str, ...],
) -> tuple[dict[str, str], dict[str, str]]:
    projected_ids = tuple(row.route_id for row in projection.routes)
    projected_to_allocation: dict[str, str] = {}
    allocation_to_projected: dict[str, str] = {}

    for projected_id in projected_ids:
        exact = [
            route_id
            for route_id in allocation_route_ids
            if route_id == projected_id
        ]
        matches = exact or [
            route_id
            for route_id in allocation_route_ids
            if _route_token_v1(route_id) == _route_token_v1(projected_id)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"{projected_id}: expected one committed allocation-route "
                f"identity match, found {len(matches)}"
            )
        allocation_id = matches[0]
        if allocation_id in allocation_to_projected:
            raise ValueError(
                f"{allocation_id}: allocation route matched more than once"
            )
        projected_to_allocation[projected_id] = allocation_id
        allocation_to_projected[allocation_id] = projected_id

    unmatched = set(allocation_route_ids) - set(allocation_to_projected)
    if unmatched:
        raise ValueError(
            "Committed allocation routes missing from resized projection: "
            + ", ".join(sorted(unmatched))
        )
    return projected_to_allocation, allocation_to_projected


def _point_id_v1(point: Any) -> str:
    return _text_v1(getattr(point, "balancing_point_id", ""))


def _point_depths_v1(points: tuple[Any, ...]) -> dict[str, int]:
    by_id = {_point_id_v1(point): point for point in points}
    if "" in by_id:
        raise ValueError("Committed balancing point requires stable identity")
    if len(by_id) != len(points):
        raise ValueError("Duplicate committed balancing-point identity")

    depths: dict[str, int] = {}

    def depth(point_id: str, trail: tuple[str, ...] = ()) -> int:
        if point_id in depths:
            return depths[point_id]
        if point_id in trail:
            raise ValueError(
                "Committed balancing-point parent hierarchy contains a cycle"
            )
        point = by_id[point_id]
        parent_id = _text_v1(
            getattr(point, "parent_balancing_point_id", "")
        )
        if not parent_id:
            value = 0
        else:
            if parent_id not in by_id:
                raise ValueError(
                    f"{point_id}: unknown parent balancing point {parent_id}"
                )
            value = depth(parent_id, trail + (point_id,)) + 1
        depths[point_id] = value
        return value

    for point_id in by_id:
        depth(point_id)
    return depths


def _ordered_points_v1(points: tuple[Any, ...]) -> tuple[Any, ...]:
    depths = _point_depths_v1(points)
    return tuple(
        sorted(
            points,
            key=lambda point: (
                depths[_point_id_v1(point)],
                -len(tuple(
                    getattr(point, "downstream_route_ids", ()) or ()
                )),
                _point_id_v1(point),
            ),
        )
    )


def build_resized_balancing_point_reconciliation_v1(
        *,
        resized_hydraulics: (
            ProportionedPipeResizingHydraulicProjectionV1 | None
        ),
        committed_point_allocation_authority: Any,
) -> ResizedBalancingPointReconciliationV1:
    """
    Reconcile H-S61-C shortfalls through frozen H-S56-A point topology.

    Deterministic allocation rule:
        walk the committed parent hierarchy from shared upstream points toward
        route-exclusive downstream points.  At each point allocate the minimum
        unresolved shortfall across all routes governed by that point.

    This preserves shared pressure duty where every governed route needs it,
    while preventing a shared point from adding pressure to a controlling
    route whose required shortfall is zero.
    """
    if not isinstance(
            resized_hydraulics,
            ProportionedPipeResizingHydraulicProjectionV1,
    ):
        return _blocked_v1(
            "Blocked — H-S61-C resized hydraulic projection required",
            "H-S61-C resized hydraulic projection required",
        )
    if not resized_hydraulics.ready:
        return _blocked_v1(
            "Blocked — H-S61-C resized hydraulic projection is not ready",
            *(tuple(resized_hydraulics.blockers or ()) or (
                "H-S61-C resized hydraulic projection is not ready",
            )),
        )
    if committed_point_allocation_authority is None:
        return _blocked_v1(
            "Blocked — H-S56-A committed point-allocation authority required",
            "H-S56-A committed point-allocation authority required",
        )
    if not bool(
            getattr(committed_point_allocation_authority, "ready", False)
    ):
        return _blocked_v1(
            "Blocked — H-S56-A committed point-allocation authority "
            "is not ready",
            *(tuple(
                getattr(
                    committed_point_allocation_authority,
                    "blockers",
                    (),
                )
                or ()
            ) or (
                "H-S56-A committed point-allocation authority is not ready",
            )),
        )

    try:
        points = tuple(
            getattr(committed_point_allocation_authority, "rows", ()) or ()
        )
        allocation_route_ids = _authority_route_ids_v1(
            committed_point_allocation_authority
        )
        if not allocation_route_ids:
            raise ValueError(
                "Committed point-allocation route identities required"
            )
        projected_to_allocation, allocation_to_projected = (
            _match_routes_v1(
                resized_hydraulics,
                allocation_route_ids,
            )
        )
        ordered_points = _ordered_points_v1(points)

        projection_by_id = {
            row.route_id: row for row in resized_hydraulics.routes
        }
        residual_by_allocation_id = {
            allocation_id: _normalise_pa_v1(
                projection_by_id[projected_id].required_added_dp_Pa
            )
            for allocation_id, projected_id
            in allocation_to_projected.items()
        }
        allocated_by_point_id: dict[str, float] = {}

        for point in ordered_points:
            point_id = _point_id_v1(point)
            governed = tuple(
                dict.fromkeys(
                    _text_v1(route_id)
                    for route_id in tuple(
                        getattr(point, "downstream_route_ids", ()) or ()
                    )
                    if _text_v1(route_id)
                )
            )
            unknown = set(governed) - set(residual_by_allocation_id)
            if unknown:
                raise ValueError(
                    f"{point_id}: unknown governed allocation routes: "
                    + ", ".join(sorted(unknown))
                )

            if governed:
                allocated = min(
                    residual_by_allocation_id[route_id]
                    for route_id in governed
                )
                allocated = max(0.0, _normalise_pa_v1(allocated))
            else:
                allocated = 0.0

            allocated_by_point_id[point_id] = allocated
            for route_id in governed:
                residual_by_allocation_id[route_id] = _normalise_pa_v1(
                    residual_by_allocation_id[route_id] - allocated
                )

        unresolved = {
            route_id: value
            for route_id, value in residual_by_allocation_id.items()
            if abs(value) >= CONSERVATION_TOLERANCE_PA
        }
        if unresolved:
            raise ValueError(
                "Committed point topology cannot reconcile resized route "
                "shortfalls: "
                + ", ".join(
                    f"{route_id}={value:.3f} Pa"
                    for route_id, value in sorted(unresolved.items())
                )
            )

        point_rows: list[ResizedBalancingPointReconciliationRowV1] = []
        for point in ordered_points:
            point_id = _point_id_v1(point)
            allocation_routes = tuple(
                dict.fromkeys(
                    _text_v1(route_id)
                    for route_id in tuple(
                        getattr(point, "downstream_route_ids", ()) or ()
                    )
                    if _text_v1(route_id)
                )
            )
            projected_routes = tuple(
                allocation_to_projected[route_id]
                for route_id in allocation_routes
            )
            point_flow = _float_attr_v1(
                point,
                "point_flow_kg_s",
                "flow_kg_s",
            )
            previous_dp = _float_attr_v1(
                point,
                "allocated_added_dp_pa",
                "allocated_added_pressure_drop_Pa",
            )
            previous_resistance = _float_attr_v1(
                point,
                "allocated_resistance_pa_per_kg_s2",
                "allocated_resistance_Pa_per_kg_s2",
            )
            reconciled_dp = allocated_by_point_id[point_id]
            if reconciled_dp > 0.0 and point_flow <= 0.0:
                raise ValueError(
                    f"{point_id}: positive reconciled duty requires "
                    "positive committed point flow"
                )
            resistance = (
                reconciled_dp / point_flow**2
                if reconciled_dp > 0.0
                else 0.0
            )
            if not isfinite(resistance):
                raise ValueError(
                    f"{point_id}: invalid reconciled resistance"
                )
            duty_required = reconciled_dp > 0.0
            point_rows.append(
                ResizedBalancingPointReconciliationRowV1(
                    balancing_point_id=point_id,
                    point_scope=_text_v1(
                        getattr(point, "point_scope", "")
                    ),
                    point_role=_text_v1(
                        getattr(point, "point_role", "")
                    ),
                    label=_text_v1(getattr(point, "label", "")),
                    parent_balancing_point_id=_text_v1(
                        getattr(
                            point,
                            "parent_balancing_point_id",
                            "",
                        )
                    ),
                    anchor_section_id=_text_v1(
                        getattr(point, "anchor_section_id", "")
                    ),
                    allocation_route_ids=allocation_routes,
                    projected_route_ids=projected_routes,
                    is_shared=bool(getattr(point, "is_shared", False)),
                    is_route_exclusive=bool(
                        getattr(point, "is_route_exclusive", False)
                    ),
                    point_flow_kg_s=point_flow,
                    previous_allocated_dp_Pa=previous_dp,
                    previous_resistance_Pa_per_kg_s2=previous_resistance,
                    reconciled_allocated_dp_Pa=reconciled_dp,
                    reconciled_resistance_Pa_per_kg_s2=resistance,
                    allocation_change_dp_Pa=_normalise_pa_v1(
                        reconciled_dp - previous_dp
                    ),
                    valve_duty_required=duty_required,
                    status=(
                        "Reconciled preview — positive resized valve duty"
                        if duty_required
                        else "Reconciled preview — no resized valve duty"
                    ),
                )
            )

        route_rows: list[ResizedBalancingRouteReconciliationRowV1] = []
        for projected in sorted(
                resized_hydraulics.routes,
                key=lambda row: row.route_id,
        ):
            allocation_id = projected_to_allocation[projected.route_id]
            contributing = tuple(
                row.balancing_point_id
                for row in point_rows
                if (
                    allocation_id in row.allocation_route_ids
                    and row.reconciled_allocated_dp_Pa > 0.0
                )
            )
            allocated_path = sum(
                row.reconciled_allocated_dp_Pa
                for row in point_rows
                if allocation_id in row.allocation_route_ids
            )
            residual = _normalise_pa_v1(
                float(projected.required_added_dp_Pa) - allocated_path
            )
            conserved = abs(residual) < CONSERVATION_TOLERANCE_PA
            route_rows.append(
                ResizedBalancingRouteReconciliationRowV1(
                    projected_route_id=projected.route_id,
                    allocation_route_id=allocation_id,
                    resized_hydraulic_dp_Pa=float(
                        projected.route_pressure_drop_total_Pa
                    ),
                    controlling_target_Pa=float(
                        projected.controlling_target_Pa
                    ),
                    required_added_dp_Pa=float(
                        projected.required_added_dp_Pa
                    ),
                    allocated_path_dp_Pa=allocated_path,
                    residual_Pa=residual,
                    contributing_balancing_point_ids=contributing,
                    conserved=conserved,
                    status=(
                        "Reconciled — resized route reaches controlling target"
                        if conserved
                        else "Blocked — resized point allocation does not "
                        "conserve route shortfall"
                    ),
                )
            )
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        return _blocked_v1(
            f"Blocked — resized point reconciliation failed: {exc}",
            str(exc),
        )

    ready = bool(route_rows) and all(row.conserved for row in route_rows)
    valve_count = sum(row.valve_duty_required for row in point_rows)
    return ResizedBalancingPointReconciliationV1(
        ready=ready,
        point_rows=tuple(point_rows),
        route_rows=tuple(route_rows),
        point_count=len(point_rows),
        route_count=len(route_rows),
        valve_duty_point_count=valve_count,
        status=(
            f"Ready — {len(route_rows)} resized routes reconcile across "
            f"{len(point_rows)} committed balancing points; "
            f"{valve_count} require valve duty"
            if ready
            else "Blocked — resized route conservation failed"
        ),
    )
