# ======================================================================
# H-S58-A — Committed Proportioned-system completion status
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.committed_basis_route_proportioning_result_v1 import (
    CommittedBasisRouteProportioningResultV1,
    build_committed_basis_route_proportioning_result_v1,
)
from HVAC.hydronics.proportioning.committed_basis_section_hydraulic_result_v1 import (
    CommittedBasisSectionHydraulicResultV1,
    build_committed_basis_section_hydraulic_result_v1,
)
from HVAC.hydronics.proportioning.committed_point_level_balancing_reconciliation_v1 import (
    CommittedPointLevelBalancingReconciliationV1,
    build_committed_point_level_balancing_reconciliation_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


@dataclass(frozen=True, slots=True)
class CommittedProportionedSystemCompletionStatusV1:
    """
    System-level completion status composed only from frozen committed results.

    This is committed proportioning evidence, not a declaration that pump,
    valve-product, setting, commissioning or installed-system design is final.
    """

    schema: str = (
        "committed_proportioned_system_completion_status_v1"
    )
    ready: bool = False
    accepted_return_arrangement_basis: str = "—"
    controlling_target_pressure_drop_Pa: float | None = None
    route_count: int = 0
    routes_at_target_count: int = 0
    balancing_point_count: int = 0
    reconciled_balancing_point_count: int = 0
    valve_duty_point_count: int = 0
    unique_section_count: int = 0
    route_addressable_section_count: int = 0
    status: str = (
        "Committed Proportioned-system completion status not ready"
    )
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No live preview evidence used",
        "No new friction or pressure calculation",
        "No ProjectState mutation",
        "No pump selection",
        "No valve product selected",
        "No valve setting selected",
        "No pipe resizing",
        "No commissioning or final system balancing",
    )
    note: str = (
        "Committed route, balancing-point and section results reconcile; "
        "later product and commissioning decisions remain separate."
    )


def build_committed_proportioned_system_completion_status_v1(
    snapshot: ProportionedBasisSnapshotV1 | None,
) -> CommittedProportionedSystemCompletionStatusV1:
    """Compose H-S55/H-S56/H-S57 results from one frozen snapshot."""
    if not isinstance(snapshot, ProportionedBasisSnapshotV1):
        return _blocked_v1(
            "H-S26-G committed proportioning snapshot required"
        )

    route_result = build_committed_basis_route_proportioning_result_v1(
        snapshot.hydraulic_input_authority
    )
    point_result = (
        build_committed_point_level_balancing_reconciliation_v1(snapshot)
    )
    section_result = build_committed_basis_section_hydraulic_result_v1(
        snapshot
    )
    return _compose_committed_completion_status_v1(
        snapshot=snapshot,
        route_result=route_result,
        point_result=point_result,
        section_result=section_result,
    )


def _compose_committed_completion_status_v1(
    *,
    snapshot: ProportionedBasisSnapshotV1,
    route_result: CommittedBasisRouteProportioningResultV1,
    point_result: CommittedPointLevelBalancingReconciliationV1,
    section_result: CommittedBasisSectionHydraulicResultV1,
) -> CommittedProportionedSystemCompletionStatusV1:
    blockers: list[str] = []

    return_basis = _text_v1(snapshot.return_arrangement_basis)
    if not return_basis or return_basis in {"—", "UNDECIDED"}:
        blockers.append("Committed accepted return arrangement basis required")

    blockers.extend(
        _upstream_blockers_v1(
            "H-S55-A",
            route_result.ready,
            route_result.blockers,
            route_result.status,
        )
    )
    blockers.extend(
        _upstream_blockers_v1(
            "H-S56-C",
            point_result.ready,
            point_result.blockers,
            point_result.status,
        )
    )
    blockers.extend(
        _upstream_blockers_v1(
            "H-S57-A",
            section_result.ready,
            section_result.blockers,
            section_result.status,
        )
    )

    target = _finite_v1(
        route_result.controlling_target_pressure_drop_Pa
    )
    if target is None or target < 0.0:
        blockers.append(
            "H-S55-A finite non-negative controlling target required"
        )

    route_rows = tuple(route_result.rows or ())
    point_rows = tuple(point_result.point_rows or ())
    point_route_rows = tuple(point_result.route_rows or ())
    section_rows = tuple(section_result.rows or ())

    route_ids = _unique_ids_v1(
        (getattr(row, "route_id", "") for row in route_rows),
        label="H-S55-A route",
        blockers=blockers,
    )
    point_route_ids = _unique_ids_v1(
        (
            getattr(row, "committed_route_id", "")
            for row in point_route_rows
        ),
        label="H-S56-C committed route",
        blockers=blockers,
    )
    section_route_ids = {
        _text_v1(getattr(row, "committed_route_id", ""))
        for row in section_rows
        if _text_v1(getattr(row, "committed_route_id", ""))
    }

    if not route_ids:
        blockers.append("H-S55-A committed route rows required")
    if set(point_route_ids) != set(route_ids):
        blockers.append(
            "H-S56-C committed route identities must match H-S55-A"
        )
    if section_route_ids != set(route_ids):
        blockers.append(
            "H-S57-A committed route identities must match H-S55-A"
        )

    routes_at_target = sum(
        bool(getattr(row, "ready", False))
        and bool(getattr(row, "within_tolerance", False))
        for row in route_rows
    )
    if routes_at_target != len(route_rows):
        blockers.append("Every H-S55-A route must be ready and at target")

    reconciled_route_count = sum(
        bool(getattr(row, "ready", False))
        and bool(getattr(row, "reconciled", False))
        for row in point_route_rows
    )
    if reconciled_route_count != len(point_route_rows):
        blockers.append("Every H-S56-C route must reconcile")

    reconciled_point_count = sum(
        bool(getattr(row, "ready", False))
        and bool(getattr(row, "reconciled", False))
        for row in point_rows
    )
    if reconciled_point_count != len(point_rows):
        blockers.append("Every H-S56-C balancing point must reconcile")

    unique_section_count = int(
        getattr(section_result, "unique_section_count", 0) or 0
    )
    route_count = len(route_rows)
    section_route_count = int(
        getattr(section_result, "route_count", 0) or 0
    )
    if unique_section_count <= 0 or not section_rows:
        blockers.append("H-S57-A committed section rows required")
    if section_route_count != route_count:
        blockers.append(
            "H-S57-A route count must match H-S55-A route count"
        )

    clean = _unique_text_v1(blockers)
    ready = not clean
    return CommittedProportionedSystemCompletionStatusV1(
        ready=ready,
        accepted_return_arrangement_basis=return_basis or "—",
        controlling_target_pressure_drop_Pa=target,
        route_count=route_count,
        routes_at_target_count=routes_at_target,
        balancing_point_count=len(point_rows),
        reconciled_balancing_point_count=reconciled_point_count,
        valve_duty_point_count=sum(
            bool(getattr(row, "valve_duty_required", False))
            for row in point_rows
        ),
        unique_section_count=unique_section_count,
        route_addressable_section_count=len(section_rows),
        status=(
            "Ready — committed Proportioned-system completion "
            "status available"
            if ready
            else "Blocked — " + "; ".join(clean)
        ),
        blockers=clean,
    )


def _upstream_blockers_v1(
    stage: str,
    ready: bool,
    blockers,
    status: object,
) -> list[str]:
    if ready:
        return []
    values = [
        _text_v1(value)
        for value in tuple(blockers or ())
        if _text_v1(value)
    ]
    if not values:
        values = [
            _text_v1(status)
            or f"{stage} committed result is not ready"
        ]
    return [f"{stage}: {value}" for value in values]


def _unique_ids_v1(values, *, label: str, blockers: list[str]) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        identifier = _text_v1(value)
        if not identifier:
            blockers.append(f"Every {label} requires stable identity")
            continue
        if identifier in output:
            blockers.append(f"Duplicate {label} identity: {identifier}")
            continue
        output.append(identifier)
    return tuple(output)


def _finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_text_v1(values) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in output:
            output.append(text)
    return tuple(output)


def _blocked_v1(
    *blockers: str,
) -> CommittedProportionedSystemCompletionStatusV1:
    clean = _unique_text_v1(blockers)
    return CommittedProportionedSystemCompletionStatusV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
