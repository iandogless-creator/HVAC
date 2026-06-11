# ======================================================================
# HVAC/hydronics/proportioning/proportioning_readiness_gate_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field

from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    ProportioningInputSnapshotV1,
)


_TRUE_TEXT = {"yes", "true", "1", "y"}


@dataclass(slots=True)
class ProportioningReadinessCheckV1:
    code: str
    label: str
    passed: bool
    detail: str = ""


@dataclass(slots=True)
class ProportioningReadinessGateV1:
    """
    Readiness gate for future proportioning authority.

    This is not a balancing engine.
    """

    ready: bool = False
    status: str = "Not ready for proportioning"
    checks: list[ProportioningReadinessCheckV1] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


def _has_text(value: object) -> bool:
    return str(value or "").strip() not in ("", "—", "None")


def _is_true_text(value: object) -> bool:
    return str(value or "").strip().lower() in _TRUE_TEXT


def _add_check(
    checks: list[ProportioningReadinessCheckV1],
    *,
    code: str,
    label: str,
    passed: bool,
    detail: str = "",
) -> None:
    checks.append(
        ProportioningReadinessCheckV1(
            code=code,
            label=label,
            passed=passed,
            detail=detail,
        )
    )


def evaluate_proportioning_readiness_v1(
    snapshot: ProportioningInputSnapshotV1 | None,
) -> ProportioningReadinessGateV1:
    """
    Evaluate whether the current proportioning input snapshot is ready
    for the next proportioning stage.

    Authority boundary:
    • no ProjectState mutation
    • no balancing
    • no pump selection
    • no pipe resizing
    • no committed return arrangement
    """
    checks: list[ProportioningReadinessCheckV1] = []

    if snapshot is None:
        _add_check(
            checks,
            code="SNAPSHOT_EXISTS",
            label="Snapshot exists",
            passed=False,
            detail="No proportioning input snapshot is available",
        )
        return ProportioningReadinessGateV1(
            ready=False,
            status="Not ready for proportioning",
            checks=checks,
            blockers=["No proportioning input snapshot is available"],
        )

    sections = snapshot.sections
    routes = snapshot.routes
    returns = snapshot.return_comparisons

    _add_check(
        checks,
        code="SECTIONS_AVAILABLE",
        label="Section pressure basis rows available",
        passed=bool(sections),
        detail=f"{len(sections)} section rows",
    )

    _add_check(
        checks,
        code="ROUTES_AVAILABLE",
        label="Route pressure rows available",
        passed=bool(routes),
        detail=f"{len(routes)} route rows",
    )

    _add_check(
        checks,
        code="RETURN_COMPARISONS_AVAILABLE",
        label="F+R / F+RR comparison rows available",
        passed=bool(returns),
        detail=f"{len(returns)} return comparison rows",
    )

    section_pressure_ready = bool(sections) and all(
        _has_text(section.flow_kg_s)
        and _has_text(section.pipe)
        and _has_text(section.dp_per_m)
        and _has_text(section.section_dp)
        for section in sections
    )

    _add_check(
        checks,
        code="SECTION_PRESSURE_BASIS",
        label="Section pressure basis complete",
        passed=section_pressure_ready,
        detail="Requires flow, pipe, Δp/m and section Δp for every section",
    )

    route_pressure_ready = bool(routes) and all(
        _has_text(route.route_dp_sum)
        for route in routes
    )

    _add_check(
        checks,
        code="ROUTE_PRESSURE_BASIS",
        label="Route Δp basis complete",
        passed=route_pressure_ready,
        detail="Requires route total Δp for every route",
    )

    route_shortfall_ready = bool(routes) and all(
        _has_text(route.shortfall_pa)
        for route in routes
    )

    _add_check(
        checks,
        code="ROUTE_SHORTFALL_BASIS",
        label="Route shortfall basis complete",
        passed=route_shortfall_ready,
        detail="Requires shortfall against controlling route for every route",
    )

    controlling_routes = [
        route
        for route in routes
        if _is_true_text(route.controlling)
    ]

    controlling_ready = len(controlling_routes) == 1

    _add_check(
        checks,
        code="CONTROLLING_ROUTE",
        label="Single controlling route identified",
        passed=controlling_ready,
        detail=f"{len(controlling_routes)} controlling routes found",
    )

    return_basis_ready = bool(returns) and all(
        _has_text(row.direct_total_dp)
        and _has_text(row.reverse_total_dp)
        and _has_text(row.rr_suitability)
        for row in returns
    )

    _add_check(
        checks,
        code="RETURN_COMPARISON_BASIS",
        label="F+R / F+RR comparison basis complete",
        passed=return_basis_ready,
        detail="Requires direct Δp, reverse Δp and RR suitability for every comparison row",
    )

    blockers = [
        check.label
        for check in checks
        if not check.passed
    ]

    ready = not blockers

    return ProportioningReadinessGateV1(
        ready=ready,
        status=(
            "Ready for preliminary proportioning"
            if ready
            else "Not ready for proportioning"
        ),
        checks=checks,
        blockers=blockers,
    )