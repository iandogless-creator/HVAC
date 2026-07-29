# ======================================================================
# H-S56-C — Committed point-level balancing reconciliation result
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
)
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    CommittedBalancingPointAllocationAuthorityV1,
)
from HVAC.hydronics.proportioning.committed_basis_route_proportioning_result_v1 import (
    build_committed_basis_route_proportioning_result_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    CommittedPointValveBasisV1,
    ProportionedBasisSnapshotV1,
)


DEFAULT_POINT_RECONCILIATION_TOLERANCE_PA = 0.05


@dataclass(frozen=True, slots=True)
class CommittedPointBalancingReconciliationRowV1:
    balancing_point_id: str = ""
    point_scope: str = ""
    point_role: str = ""
    label: str = ""
    parent_balancing_point_id: str = ""
    downstream_route_ids: tuple[str, ...] = ()
    is_shared: bool = False
    is_route_exclusive: bool = False
    point_flow_kg_s: float | None = None
    allocated_added_pressure_drop_Pa: float | None = None
    allocated_resistance_Pa_per_kg_s2: float | None = None
    valve_duty_required: bool = False
    accepted_kvs_basis: float | None = None
    disposition: str = ""
    reconciled: bool = False
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CommittedRoutePointReconciliationRowV1:
    committed_route_id: str = ""
    allocation_route_id: str = ""
    route_label: str = ""
    basis: str = ""
    controlling: bool = False
    required_added_pressure_drop_Pa: float | None = None
    allocated_path_pressure_drop_Pa: float | None = None
    residual_Pa: float | None = None
    contributing_balancing_point_ids: tuple[str, ...] = ()
    reconciled: bool = False
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CommittedPointLevelBalancingReconciliationV1:
    """
    Deterministic reconciliation derived only from one committed snapshot.

    It proves route/point allocation conservation and joins positive point
    allocations to the frozen manually approved generic-Kvs bases. It does
    not calculate a valve setting or select a valve product.
    """

    schema: str = "committed_point_level_balancing_reconciliation_v1"
    ready: bool = False
    tolerance_Pa: float = DEFAULT_POINT_RECONCILIATION_TOLERANCE_PA
    point_rows: tuple[CommittedPointBalancingReconciliationRowV1, ...] = ()
    route_rows: tuple[CommittedRoutePointReconciliationRowV1, ...] = ()
    status: str = "Committed point-level balancing reconciliation not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No live hydraulic or point preview used",
        "No ProjectState mutation",
        "No valve product selected",
        "No valve setting selected",
        "No automatic Kvs choice or revision",
        "No pump selection",
        "No pipe resizing",
        "No commissioning or final balancing",
    )
    note: str = (
        "Reconciliation evidence only — committed route additions, point "
        "allocations and approved generic-Kvs bases are checked for identity "
        "and conservation."
    )


def build_committed_point_level_balancing_reconciliation_v1(
    snapshot: ProportionedBasisSnapshotV1 | None,
    *,
    tolerance_Pa: float = DEFAULT_POINT_RECONCILIATION_TOLERANCE_PA,
) -> CommittedPointLevelBalancingReconciliationV1:
    """Reconcile frozen route additions, point allocations and point bases."""

    tolerance = _finite_number_v1(tolerance_Pa)
    if tolerance is None or tolerance < 0.0:
        return _blocked_result_v1(
            "tolerance_Pa must be finite and zero or greater"
        )
    if not isinstance(snapshot, ProportionedBasisSnapshotV1):
        return _blocked_result_v1(
            "Committed Proportioned basis snapshot required",
            tolerance_Pa=tolerance,
        )

    route_result = build_committed_basis_route_proportioning_result_v1(
        snapshot.hydraulic_input_authority,
        tolerance_Pa=tolerance,
    )
    if not route_result.ready:
        upstream = tuple(
            f"H-S55-A: {value}"
            for value in tuple(route_result.blockers or ())
            if _text_v1(value)
        )
        return _blocked_result_v1(
            *(upstream or ("H-S55-A committed route result is not ready",)),
            tolerance_Pa=tolerance,
        )

    authority = snapshot.point_allocation_authority
    if not isinstance(
        authority,
        CommittedBalancingPointAllocationAuthorityV1,
    ):
        return _blocked_result_v1(
            "H-S56-A committed balancing-point allocation authority required",
            tolerance_Pa=tolerance,
        )
    if not authority.ready:
        upstream = tuple(
            f"H-S56-A: {value}"
            for value in tuple(authority.blockers or ())
            if _text_v1(value)
        )
        return _blocked_result_v1(
            *(upstream or ("H-S56-A point allocation is not ready",)),
            tolerance_Pa=tolerance,
        )

    blockers: list[str] = []
    allocation_rows = tuple(authority.rows or ())
    conservation_rows = tuple(authority.route_conservation or ())
    if not allocation_rows:
        blockers.append("Committed point-allocation rows required")
    if not conservation_rows:
        blockers.append("Committed route-conservation rows required")

    point_by_id: dict[str, object] = {}
    for row in allocation_rows:
        point_id = _text_v1(row.balancing_point_id)
        if not point_id:
            blockers.append("Every committed point allocation requires stable ID")
        elif point_id in point_by_id:
            blockers.append(f"Duplicate committed balancing_point_id: {point_id}")
        else:
            point_by_id[point_id] = row

    basis_by_id: dict[str, CommittedPointValveBasisV1] = {}
    for basis in tuple(snapshot.committed_point_valve_bases or ()):
        if not isinstance(basis, CommittedPointValveBasisV1):
            blockers.append("Committed point-valve basis type required")
            continue
        point_id = _text_v1(basis.balancing_point_id)
        kvs = _positive_finite_v1(basis.accepted_kvs_basis)
        if not point_id:
            blockers.append("Every committed point-valve basis requires stable ID")
            continue
        if point_id in basis_by_id:
            blockers.append(f"Duplicate committed point-valve basis: {point_id}")
            continue
        if kvs is None:
            blockers.append(f"{point_id}: positive committed generic Kvs required")
        if _text_v1(basis.disposition) != APPROVED_FOR_PRODUCT_SEARCH:
            blockers.append(
                f"{point_id}: approved product-search disposition required"
            )
        basis_by_id[point_id] = basis

    positive_point_ids = tuple(
        _text_v1(row.balancing_point_id)
        for row in allocation_rows
        if (
            _finite_number_v1(row.allocated_added_pressure_drop_Pa) is not None
            and float(row.allocated_added_pressure_drop_Pa) > 0.0
        )
    )
    missing_bases = tuple(
        point_id for point_id in positive_point_ids if point_id not in basis_by_id
    )
    extra_bases = tuple(
        point_id for point_id in basis_by_id if point_id not in positive_point_ids
    )
    if missing_bases:
        blockers.append(
            "Positive committed point allocations missing generic-Kvs bases: "
            + ", ".join(missing_bases)
        )
    if extra_bases:
        blockers.append(
            "Committed generic-Kvs bases have no positive point allocation: "
            + ", ".join(extra_bases)
        )

    point_rows: list[CommittedPointBalancingReconciliationRowV1] = []
    for source in allocation_rows:
        point_id = _text_v1(source.balancing_point_id)
        allocated = _finite_number_v1(
            source.allocated_added_pressure_drop_Pa
        )
        flow = _positive_finite_v1(source.point_flow_kg_s)
        resistance = _finite_number_v1(
            source.allocated_resistance_Pa_per_kg_s2
        )
        row_blockers: list[str] = []
        if allocated is None or allocated < 0.0:
            row_blockers.append("Non-negative committed point allocation required")
        if flow is None:
            row_blockers.append("Positive committed point flow required")
        if resistance is None or resistance < 0.0:
            row_blockers.append("Non-negative committed point resistance required")

        valve_duty = allocated is not None and allocated > 0.0
        basis = basis_by_id.get(point_id)
        if valve_duty and basis is None:
            row_blockers.append(
                "Positive point allocation requires committed generic-Kvs basis"
            )
        if not valve_duty and basis is not None:
            row_blockers.append(
                "Generic-Kvs basis is stale for zero point allocation"
            )

        clean_row_blockers = _unique_v1(tuple(row_blockers))
        ready = not clean_row_blockers
        if clean_row_blockers:
            blockers.extend(
                f"{point_id or 'unknown point'}: {value}"
                for value in clean_row_blockers
            )
        point_rows.append(
            CommittedPointBalancingReconciliationRowV1(
                balancing_point_id=point_id,
                point_scope=_text_v1(source.point_scope),
                point_role=_text_v1(source.point_role),
                label=_text_v1(source.label) or point_id,
                parent_balancing_point_id=_text_v1(
                    source.parent_balancing_point_id
                ),
                downstream_route_ids=tuple(source.downstream_route_ids or ()),
                is_shared=bool(source.is_shared),
                is_route_exclusive=bool(source.is_route_exclusive),
                point_flow_kg_s=flow,
                allocated_added_pressure_drop_Pa=allocated,
                allocated_resistance_Pa_per_kg_s2=resistance,
                valve_duty_required=valve_duty,
                accepted_kvs_basis=(
                    float(basis.accepted_kvs_basis)
                    if basis is not None
                    else None
                ),
                disposition=(
                    _text_v1(basis.disposition)
                    if basis is not None
                    else ""
                ),
                reconciled=ready,
                ready=ready,
                status=(
                    "Reconciled — positive committed allocation has approved "
                    "generic-Kvs basis"
                    if ready and valve_duty
                    else "Reconciled — no valve duty at zero allocation"
                    if ready
                    else "Blocked — " + "; ".join(clean_row_blockers)
                ),
                blockers=clean_row_blockers,
            )
        )

    conservation_by_id: dict[str, object] = {}
    for row in conservation_rows:
        route_id = _text_v1(row.route_id)
        if not route_id:
            blockers.append(
                "Every committed route-conservation row requires stable route_id"
            )
        elif route_id in conservation_by_id:
            blockers.append(
                f"Duplicate committed conservation route_id: {route_id}"
            )
        else:
            conservation_by_id[route_id] = row

    route_rows: list[CommittedRoutePointReconciliationRowV1] = []
    used_allocation_ids: set[str] = set()
    for source in tuple(route_result.rows or ()):
        committed_id = _text_v1(source.route_id)
        allocation_id = _bridge_route_id_v1(
            committed_id,
            allocation_route_ids=tuple(conservation_by_id),
        )
        row_blockers: list[str] = []
        if not allocation_id:
            row_blockers.append(
                "Committed route has no stable point-allocation route match"
            )
            conservation = None
        elif allocation_id in used_allocation_ids:
            row_blockers.append(
                "Duplicate committed route identity after canonical bridge"
            )
            conservation = conservation_by_id.get(allocation_id)
        else:
            used_allocation_ids.add(allocation_id)
            conservation = conservation_by_id.get(allocation_id)

        route_added = _finite_number_v1(
            source.required_added_pressure_drop_Pa
        )
        allocation_required = (
            _finite_number_v1(
                conservation.required_added_pressure_drop_Pa
            )
            if conservation is not None
            else None
        )
        allocated_path = (
            _finite_number_v1(
                conservation.allocated_path_pressure_drop_Pa
            )
            if conservation is not None
            else None
        )
        if route_added is None or route_added < 0.0:
            row_blockers.append(
                "Non-negative committed route added pressure drop required"
            )
        if allocation_required is None or allocation_required < 0.0:
            row_blockers.append(
                "Non-negative point-allocation route requirement required"
            )
        if allocated_path is None or allocated_path < 0.0:
            row_blockers.append(
                "Non-negative allocated path pressure drop required"
            )

        if route_added is not None and allocation_required is not None:
            if abs(route_added - allocation_required) > tolerance:
                row_blockers.append(
                    "Committed route addition differs from point-allocation "
                    "route requirement"
                )
        residual = (
            route_added - allocated_path
            if route_added is not None and allocated_path is not None
            else None
        )
        if residual is not None and abs(residual) > tolerance:
            row_blockers.append(
                "Committed point allocations do not reconcile to route addition"
            )
        if not bool(source.ready) or not bool(source.within_tolerance):
            row_blockers.append("H-S55-A committed route result is not ready")
        if conservation is not None and not bool(conservation.conserved):
            row_blockers.append(
                "Committed point-allocation route conservation is not ready"
            )

        contributors = (
            tuple(conservation.contributing_balancing_point_ids or ())
            if conservation is not None
            else ()
        )
        for point_id in contributors:
            point = point_by_id.get(point_id)
            if point is None:
                row_blockers.append(
                    f"Contributing balancing point unresolved: {point_id}"
                )
            elif (
                _finite_number_v1(
                    point.allocated_added_pressure_drop_Pa
                )
                or 0.0
            ) <= 0.0:
                row_blockers.append(
                    f"Contributing balancing point has no positive allocation: "
                    f"{point_id}"
                )

        clean_row_blockers = _unique_v1(tuple(row_blockers))
        ready = not clean_row_blockers
        if clean_row_blockers:
            blockers.extend(
                f"{committed_id or 'unknown route'}: {value}"
                for value in clean_row_blockers
            )
        route_rows.append(
            CommittedRoutePointReconciliationRowV1(
                committed_route_id=committed_id,
                allocation_route_id=allocation_id,
                route_label=_text_v1(source.route_label) or committed_id,
                basis=_text_v1(source.basis),
                controlling=bool(source.controlling),
                required_added_pressure_drop_Pa=route_added,
                allocated_path_pressure_drop_Pa=allocated_path,
                residual_Pa=(
                    0.0
                    if residual is not None and abs(residual) <= tolerance
                    else residual
                ),
                contributing_balancing_point_ids=contributors,
                reconciled=ready,
                ready=ready,
                status=(
                    "Reconciled — committed point allocations equal route "
                    "addition"
                    if ready
                    else "Blocked — " + "; ".join(clean_row_blockers)
                ),
                blockers=clean_row_blockers,
            )
        )

    unused = tuple(
        route_id
        for route_id in conservation_by_id
        if route_id not in used_allocation_ids
    )
    if unused:
        blockers.append(
            "Committed point-allocation routes missing from H-S55-A result: "
            + ", ".join(unused)
        )

    clean = _unique_v1(tuple(blockers))
    ready = (
        bool(point_rows)
        and bool(route_rows)
        and not clean
        and all(row.ready for row in point_rows)
        and all(row.ready for row in route_rows)
    )
    return CommittedPointLevelBalancingReconciliationV1(
        ready=ready,
        tolerance_Pa=tolerance,
        point_rows=tuple(point_rows),
        route_rows=tuple(route_rows),
        status=(
            "Ready — committed point-level balancing reconciliation complete"
            if ready
            else "Blocked — " + "; ".join(clean)
        ),
        blockers=clean,
    )


def _bridge_route_id_v1(
    route_id: object,
    *,
    allocation_route_ids: tuple[str, ...],
) -> str:
    """Bridge ``leg_id:subleg_id`` only by stable physical route suffix."""

    value = _text_v1(route_id)
    if value in allocation_route_ids:
        return value
    suffix = value.rsplit(":", 1)[-1] if ":" in value else ""
    return suffix if suffix in allocation_route_ids else ""


def _finite_number_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _positive_finite_v1(value: object) -> float | None:
    number = _finite_number_v1(value)
    return number if number is not None and number > 0.0 else None


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_result_v1(
    *blockers: str,
    tolerance_Pa: float = DEFAULT_POINT_RECONCILIATION_TOLERANCE_PA,
) -> CommittedPointLevelBalancingReconciliationV1:
    clean = _unique_v1(tuple(blockers))
    return CommittedPointLevelBalancingReconciliationV1(
        ready=False,
        tolerance_Pa=tolerance_Pa,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
