# ======================================================================
# H-S59-A — Committed Proportioned-system aggregate result package
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

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
from HVAC.hydronics.proportioning.committed_proportioned_system_completion_status_v1 import (
    CommittedProportionedSystemCompletionStatusV1,
    build_committed_proportioned_system_completion_status_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


@dataclass(frozen=True, slots=True)
class CommittedProportionedSystemResultPackageV1:
    """
    One deterministic package of the committed H-S55/H-S56/H-S57/H-S58
    Proportioned-system results.

    The package is derived from one frozen committed snapshot. It is not
    separately persisted and does not promote product, setting, pump,
    resizing or commissioning decisions into committed authority.
    """

    schema: str = "committed_proportioned_system_result_package_v1"
    ready: bool = False
    source_snapshot_schema: str = ""
    accepted_return_arrangement_basis: str = "—"
    route_result: CommittedBasisRouteProportioningResultV1 | None = None
    point_reconciliation: (
        CommittedPointLevelBalancingReconciliationV1 | None
    ) = None
    section_result: CommittedBasisSectionHydraulicResultV1 | None = None
    completion_status: (
        CommittedProportionedSystemCompletionStatusV1 | None
    ) = None
    route_count: int = 0
    balancing_point_count: int = 0
    unique_section_count: int = 0
    route_addressable_section_count: int = 0
    status: str = "Committed Proportioned-system result package not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No live preview evidence used",
        "No ProjectState mutation or additional persistence",
        "No new hydraulic, friction or pressure calculation",
        "No pump selection",
        "No valve product selected",
        "No valve setting selected",
        "No automatic generic-Kvs revision",
        "No pipe resizing",
        "No commissioning or final system balancing",
    )
    note: str = (
        "Aggregate committed Proportioned evidence only; later export, "
        "product selection and commissioning remain separate."
    )


def build_committed_proportioned_system_result_package_v1(
    snapshot: ProportionedBasisSnapshotV1 | None,
) -> CommittedProportionedSystemResultPackageV1:
    """Build and integrity-check one committed Proportioned result package."""
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
    completion = (
        build_committed_proportioned_system_completion_status_v1(snapshot)
    )

    blockers: list[str] = []
    blockers.extend(
        _upstream_blockers_v1("H-S55-A", route_result)
    )
    blockers.extend(
        _upstream_blockers_v1("H-S56-C", point_result)
    )
    blockers.extend(
        _upstream_blockers_v1("H-S57-A", section_result)
    )
    blockers.extend(
        _upstream_blockers_v1("H-S58-A", completion)
    )

    route_rows = tuple(getattr(route_result, "rows", ()) or ())
    point_rows = tuple(getattr(point_result, "point_rows", ()) or ())
    section_rows = tuple(getattr(section_result, "rows", ()) or ())
    route_count = len(route_rows)
    point_count = len(point_rows)
    unique_section_count = int(
        getattr(section_result, "unique_section_count", 0) or 0
    )
    route_addressable_section_count = len(section_rows)

    snapshot_schema = _text_v1(getattr(snapshot, "schema", ""))
    return_basis = _text_v1(
        getattr(snapshot, "return_arrangement_basis", "")
    )
    if not snapshot_schema:
        blockers.append("Committed source snapshot schema required")
    if (
        _text_v1(
            getattr(
                completion,
                "accepted_return_arrangement_basis",
                "",
            )
        )
        != return_basis
    ):
        blockers.append(
            "H-S58-A accepted return basis must match committed snapshot"
        )
    if int(getattr(completion, "route_count", 0) or 0) != route_count:
        blockers.append(
            "H-S58-A route count must match packaged H-S55-A rows"
        )
    if (
        int(getattr(completion, "balancing_point_count", 0) or 0)
        != point_count
    ):
        blockers.append(
            "H-S58-A balancing-point count must match packaged H-S56-C rows"
        )
    if (
        int(getattr(completion, "unique_section_count", 0) or 0)
        != unique_section_count
    ):
        blockers.append(
            "H-S58-A unique-section count must match packaged H-S57-A result"
        )
    if (
        int(
            getattr(
                completion,
                "route_addressable_section_count",
                0,
            )
            or 0
        )
        != route_addressable_section_count
    ):
        blockers.append(
            "H-S58-A route-addressable section count must match packaged "
            "H-S57-A rows"
        )

    clean = _unique_v1(blockers)
    ready = not clean
    return CommittedProportionedSystemResultPackageV1(
        ready=ready,
        source_snapshot_schema=snapshot_schema,
        accepted_return_arrangement_basis=return_basis or "—",
        route_result=route_result,
        point_reconciliation=point_result,
        section_result=section_result,
        completion_status=completion,
        route_count=route_count,
        balancing_point_count=point_count,
        unique_section_count=unique_section_count,
        route_addressable_section_count=(
            route_addressable_section_count
        ),
        status=(
            "Ready — committed Proportioned-system result package available"
            if ready
            else "Blocked — " + "; ".join(clean)
        ),
        blockers=clean,
    )


def _upstream_blockers_v1(stage: str, result: object) -> list[str]:
    if bool(getattr(result, "ready", False)):
        return []
    values = [
        _text_v1(value)
        for value in tuple(getattr(result, "blockers", ()) or ())
        if _text_v1(value)
    ]
    if not values:
        values = [
            _text_v1(getattr(result, "status", ""))
            or f"{stage} committed result is not ready"
        ]
    return [f"{stage}: {value}" for value in values]


def _blocked_v1(
    *blockers: str,
) -> CommittedProportionedSystemResultPackageV1:
    clean = _unique_v1(blockers)
    return CommittedProportionedSystemResultPackageV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in output:
            output.append(text)
    return tuple(output)
