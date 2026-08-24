# ======================================================================
# H-S70-A — Balancing completion readiness
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
)
from HVAC.hydronics.proportioning.balancing_point_topology_authority_v1 import (
    BalancingPointTopologyProjectionV1,
)
from HVAC.hydronics.proportioning.committed_balancing_point_allocation_authority_v1 import (
    CommittedBalancingPointAllocationAuthorityV1,
)
from HVAC.hydronics.proportioning.committed_point_level_balancing_reconciliation_v1 import (
    build_committed_point_level_balancing_reconciliation_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


_COMMITTED_SNAPSHOT_STATES_V1 = {
    "COMMITTED_BASIS_ONLY",
    "COMMITTED_RESIZED_HYDRAULICS",
}


@dataclass(frozen=True, slots=True)
class BalancingCompletionReadinessV1:
    """Read-only readiness for explicit final-balancing acceptance."""

    schema: str = "balancing_completion_readiness_v1"
    ready: bool = False
    accepted_proportioning_basis_ready: bool = False
    point_coverage_ready: bool = False
    allocation_conservation_ready: bool = False
    point_kvs_basis_ready: bool = False
    expected_point_ids: tuple[str, ...] = ()
    allocated_point_ids: tuple[str, ...] = ()
    valve_duty_point_ids: tuple[str, ...] = ()
    uncovered_point_ids: tuple[str, ...] = ()
    unexpected_allocation_point_ids: tuple[str, ...] = ()
    duplicate_topology_point_ids: tuple[str, ...] = ()
    duplicate_allocation_point_ids: tuple[str, ...] = ()
    unconserved_route_ids: tuple[str, ...] = ()
    missing_kvs_point_ids: tuple[str, ...] = ()
    invalid_kvs_point_ids: tuple[str, ...] = ()
    stale_kvs_point_ids: tuple[str, ...] = ()
    status: str = "Balancing completion readiness not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No ProjectState mutation",
        "No balancing method accepted",
        "No final balancing schedule committed",
        "No valve product or setting selected",
        "No automatic Kvs choice or revision",
        "No pump duty or pump selection",
        "No pipe resizing",
    )
    note: str = (
        "Readiness evidence only — current balancing-point coverage is compared "
        "with the committed allocation authority and H-S56-C supplies frozen "
        "route-conservation and approved generic-Kvs reconciliation."
    )


def build_balancing_completion_readiness_v1(
    *,
    snapshot: ProportionedBasisSnapshotV1 | None,
    topology: BalancingPointTopologyProjectionV1 | None,
) -> BalancingCompletionReadinessV1:
    """Report exact blockers without accepting or committing balancing."""

    blockers: list[str] = []
    accepted_basis_ready = False
    expected_ids: tuple[str, ...] = ()
    allocated_ids: tuple[str, ...] = ()
    valve_duty_ids: tuple[str, ...] = ()
    uncovered: tuple[str, ...] = ()
    unexpected: tuple[str, ...] = ()
    duplicate_topology: tuple[str, ...] = ()
    duplicate_allocation: tuple[str, ...] = ()
    unconserved_routes: tuple[str, ...] = ()
    missing_kvs: tuple[str, ...] = ()
    invalid_kvs: tuple[str, ...] = ()
    stale_kvs: tuple[str, ...] = ()

    if not isinstance(snapshot, ProportionedBasisSnapshotV1):
        blockers.append("Committed accepted proportioning snapshot required")
        reconciliation = None
    else:
        snapshot_state = _text_v1(snapshot.status)
        return_basis = _text_v1(snapshot.return_arrangement_basis)
        hydraulic = snapshot.hydraulic_input_authority
        basis_blockers: list[str] = []
        if snapshot_state not in _COMMITTED_SNAPSHOT_STATES_V1:
            basis_blockers.append(
                "Recognised committed proportioning snapshot state required"
            )
        if not return_basis or return_basis in {"—", "UNDECIDED"}:
            basis_blockers.append(
                "Committed accepted return arrangement basis required"
            )
        if hydraulic is None or not bool(getattr(hydraulic, "ready", False)):
            basis_blockers.append(
                "Ready committed proportioning hydraulic-input authority required"
            )
        blockers.extend(basis_blockers)
        accepted_basis_ready = not basis_blockers
        reconciliation = (
            build_committed_point_level_balancing_reconciliation_v1(snapshot)
        )

    if not isinstance(topology, BalancingPointTopologyProjectionV1):
        blockers.append("H-S44-A balancing-point topology authority required")
    elif not topology.ready:
        upstream = tuple(
            _text_v1(value)
            for value in tuple(topology.blockers or ())
            if _text_v1(value)
        )
        blockers.extend(
            f"H-S44-A: {value}" for value in (
                upstream or ("Balancing-point topology is not ready",)
            )
        )
    else:
        expected_ids, duplicate_topology = _ordered_ids_v1(
            getattr(row, "balancing_point_id", "")
            for row in tuple(topology.points or ())
        )
        if not expected_ids:
            blockers.append("H-S44-A balancing-point identities required")
        if duplicate_topology:
            blockers.append(
                "Duplicate H-S44-A balancing-point identities: "
                + ", ".join(duplicate_topology)
            )

    authority = (
        snapshot.point_allocation_authority
        if isinstance(snapshot, ProportionedBasisSnapshotV1)
        else None
    )
    if not isinstance(authority, CommittedBalancingPointAllocationAuthorityV1):
        blockers.append("Committed balancing-point allocation authority required")
        allocation_rows = ()
    elif not authority.ready:
        upstream = tuple(
            _text_v1(value)
            for value in tuple(authority.blockers or ())
            if _text_v1(value)
        )
        blockers.extend(
            f"H-S56-A: {value}" for value in (
                upstream or ("Committed point allocation is not ready",)
            )
        )
        allocation_rows = tuple(authority.rows or ())
    else:
        allocation_rows = tuple(authority.rows or ())

    allocated_ids, duplicate_allocation = _ordered_ids_v1(
        getattr(row, "balancing_point_id", "") for row in allocation_rows
    )
    if authority is not None and not allocated_ids:
        blockers.append("Committed balancing-point allocation rows required")
    if duplicate_allocation:
        blockers.append(
            "Duplicate committed allocation point identities: "
            + ", ".join(duplicate_allocation)
        )

    if expected_ids and allocated_ids:
        allocated_set = set(allocated_ids)
        expected_set = set(expected_ids)
        uncovered = tuple(
            point_id for point_id in expected_ids if point_id not in allocated_set
        )
        unexpected = tuple(
            point_id for point_id in allocated_ids if point_id not in expected_set
        )
        if uncovered:
            blockers.append(
                "Balancing points missing committed allocation: "
                + ", ".join(uncovered)
            )
        if unexpected:
            blockers.append(
                "Committed allocations outside current balancing-point topology: "
                + ", ".join(unexpected)
            )

    point_coverage_ready = bool(expected_ids) and (
        isinstance(authority, CommittedBalancingPointAllocationAuthorityV1)
        and authority.ready
        and not duplicate_topology
        and not duplicate_allocation
        and not uncovered
        and not unexpected
        and expected_ids == allocated_ids
    )
    if (
        expected_ids
        and allocated_ids
        and not uncovered
        and not unexpected
        and expected_ids != allocated_ids
    ):
        # Membership is authoritative; ordering is presentation-only here.
        point_coverage_ready = (
            isinstance(authority, CommittedBalancingPointAllocationAuthorityV1)
            and authority.ready
            and not duplicate_topology
            and not duplicate_allocation
        )

    if reconciliation is not None:
        route_rows = tuple(reconciliation.route_rows or ())
        unconserved_routes = tuple(
            _text_v1(row.committed_route_id)
            for row in route_rows
            if not bool(row.ready) or not bool(row.reconciled)
        )
        if unconserved_routes:
            blockers.append(
                "Committed routes without conserved point allocation: "
                + ", ".join(unconserved_routes)
            )
        allocation_conservation_ready = (
            bool(route_rows)
            and not unconserved_routes
            and all(
                bool(row.ready) and bool(row.reconciled)
                for row in route_rows
            )
        )
    else:
        route_rows = ()
        allocation_conservation_ready = False

    valve_duty_ids = tuple(
        _text_v1(getattr(row, "balancing_point_id", ""))
        for row in allocation_rows
        if (_finite_v1(
            getattr(row, "allocated_added_pressure_drop_Pa", None)
        ) or 0.0) > 0.0
    )
    bases = (
        tuple(snapshot.committed_point_valve_bases or ())
        if isinstance(snapshot, ProportionedBasisSnapshotV1)
        else ()
    )
    basis_ids, duplicate_bases = _ordered_ids_v1(
        getattr(row, "balancing_point_id", "") for row in bases
    )
    basis_by_id = {
        _text_v1(getattr(row, "balancing_point_id", "")): row
        for row in bases
        if _text_v1(getattr(row, "balancing_point_id", ""))
    }
    missing_kvs = tuple(
        point_id for point_id in valve_duty_ids if point_id not in basis_by_id
    )
    stale_kvs = tuple(
        point_id for point_id in basis_ids if point_id not in set(valve_duty_ids)
    )
    invalid_kvs = tuple(
        point_id
        for point_id, basis in basis_by_id.items()
        if (
            _positive_finite_v1(getattr(basis, "accepted_kvs_basis", None))
            is None
            or _text_v1(getattr(basis, "disposition", ""))
            != APPROVED_FOR_PRODUCT_SEARCH
        )
    )
    if duplicate_bases:
        blockers.append(
            "Duplicate committed generic-Kvs point identities: "
            + ", ".join(duplicate_bases)
        )
    if missing_kvs:
        blockers.append(
            "Valve-duty points missing approved generic-Kvs basis: "
            + ", ".join(missing_kvs)
        )
    if invalid_kvs:
        blockers.append(
            "Valve-duty points with invalid generic-Kvs basis: "
            + ", ".join(invalid_kvs)
        )
    if stale_kvs:
        blockers.append(
            "Approved generic-Kvs bases without current valve duty: "
            + ", ".join(stale_kvs)
        )
    point_kvs_ready = (
        bool(allocation_rows)
        and not duplicate_bases
        and not missing_kvs
        and not invalid_kvs
        and not stale_kvs
    )

    if reconciliation is not None and not reconciliation.ready:
        for value in tuple(reconciliation.blockers or ()):
            text = _text_v1(value)
            if text:
                blockers.append(f"H-S56-C: {text}")

    clean = _unique_v1(tuple(blockers))
    ready = (
        accepted_basis_ready
        and point_coverage_ready
        and allocation_conservation_ready
        and point_kvs_ready
        and reconciliation is not None
        and reconciliation.ready
        and not clean
    )
    return BalancingCompletionReadinessV1(
        ready=ready,
        accepted_proportioning_basis_ready=accepted_basis_ready,
        point_coverage_ready=point_coverage_ready,
        allocation_conservation_ready=allocation_conservation_ready,
        point_kvs_basis_ready=point_kvs_ready,
        expected_point_ids=expected_ids,
        allocated_point_ids=allocated_ids,
        valve_duty_point_ids=valve_duty_ids,
        uncovered_point_ids=uncovered,
        unexpected_allocation_point_ids=unexpected,
        duplicate_topology_point_ids=duplicate_topology,
        duplicate_allocation_point_ids=duplicate_allocation,
        unconserved_route_ids=unconserved_routes,
        missing_kvs_point_ids=missing_kvs,
        invalid_kvs_point_ids=invalid_kvs,
        stale_kvs_point_ids=stale_kvs,
        status=(
            "Ready — balancing completion inputs reconcile; explicit method "
            "acceptance and schedule commit remain separate"
            if ready
            else "Blocked — " + "; ".join(clean)
        ),
        blockers=clean,
    )


def _ordered_ids_v1(values) -> tuple[tuple[str, ...], tuple[str, ...]]:
    result: list[str] = []
    duplicates: list[str] = []
    seen: set[str] = set()
    for value in values:
        stable = _text_v1(value)
        if not stable:
            continue
        if stable in seen:
            if stable not in duplicates:
                duplicates.append(stable)
            continue
        seen.add(stable)
        result.append(stable)
    return tuple(result), tuple(duplicates)


def _finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _positive_finite_v1(value: object) -> float | None:
    number = _finite_v1(value)
    return number if number is not None and number > 0.0 else None


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text_v1(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return tuple(result)
