# ======================================================================
# H-S57-A — Committed-basis section hydraulic result
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


@dataclass(frozen=True, slots=True)
class CommittedBasisSectionHydraulicRowV1:
    """One route-addressable copy of frozen committed section evidence."""

    committed_route_id: str
    committed_route_label: str
    basis: str
    section_id: str
    section_scope: str
    route_ids: tuple[str, ...]
    shared_across_routes: bool
    order: int
    from_label: str
    to_label: str
    carried_flow_kg_s: float
    pipe_size_label: str
    dn: int
    length_m: float
    k_total: float
    velocity_m_s: float
    reynolds_number: float
    friction_factor: float
    friction_method: str
    colebrook_iteration_count: int
    colebrook_converged: bool
    pressure_gradient_Pa_per_m: float
    straight_pressure_drop_Pa: float
    local_pressure_drop_Pa: float
    section_total_pressure_drop_Pa: float
    status: str = "Ready — frozen committed section evidence"


@dataclass(frozen=True, slots=True)
class CommittedBasisSectionHydraulicResultV1:
    """
    Route-addressable section result copied only from committed H-S54 authority.

    Shared sections appear once for each committed route membership so the
    Proportioned route focus can select them without consulting live previews.
    """

    schema: str = "committed_basis_section_hydraulic_result_v1"
    ready: bool = False
    rows: tuple[CommittedBasisSectionHydraulicRowV1, ...] = ()
    unique_section_count: int = 0
    route_count: int = 0
    status: str = "Committed-basis section hydraulic result not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No live hydraulic or Basic PS preview used",
        "No friction or pressure-drop recalculation",
        "No route total recomputed",
        "No pipe resizing",
        "No pump selected",
        "No valve product or setting selected",
        "No final commissioning or balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Frozen committed section evidence projected by route membership only."
    )


def build_committed_basis_section_hydraulic_result_v1(
    snapshot: ProportionedBasisSnapshotV1 | None,
) -> CommittedBasisSectionHydraulicResultV1:
    """Build a deterministic display/result projection from frozen evidence."""
    if not isinstance(snapshot, ProportionedBasisSnapshotV1):
        return _blocked("H-S26-G committed proportioning snapshot required")

    authority = snapshot.hydraulic_input_authority
    if not isinstance(
        authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ):
        return _blocked("H-S54-A committed hydraulic-input authority required")
    if not authority.ready:
        return _blocked(
            "H-S54-A committed hydraulic-input authority is not ready",
            *tuple(authority.blockers or ()),
        )

    routes = tuple(authority.routes or ())
    sections = tuple(authority.sections or ())
    blockers: list[str] = []
    route_by_id: dict[str, object] = {}
    route_order: dict[str, int] = {}

    for index, route in enumerate(routes):
        route_id = _text(getattr(route, "route_id", ""))
        if not route_id:
            blockers.append("Every committed route requires stable route_id")
            continue
        if route_id in route_by_id:
            blockers.append(f"Duplicate committed route: {route_id}")
            continue
        route_by_id[route_id] = route
        route_order[route_id] = index

    seen_sections: set[str] = set()
    memberships_by_route: dict[str, list[object]] = {
        route_id: [] for route_id in route_by_id
    }
    for section in sections:
        section_id = _text(getattr(section, "section_id", ""))
        if not section_id:
            blockers.append("Every committed section requires stable section_id")
            continue
        if section_id in seen_sections:
            blockers.append(f"Duplicate committed section: {section_id}")
            continue
        seen_sections.add(section_id)

        raw_membership_ids = tuple(
            _text(value)
            for value in tuple(getattr(section, "route_ids", ()) or ())
            if _text(value)
        )
        if not raw_membership_ids:
            blockers.append(f"{section_id}: committed route membership required")
            continue

        membership_ids: list[str] = []
        for raw_membership_id in raw_membership_ids:
            route_id = _resolve_committed_route_membership_v1(
                raw_membership_id,
                route_by_id,
            )
            if not route_id:
                blockers.append(
                    f"{section_id}: unknown committed route membership "
                    f"{raw_membership_id}"
                )
                continue
            membership_ids.append(route_id)

        if len(set(membership_ids)) != len(membership_ids):
            blockers.append(f"{section_id}: duplicate route membership")
            continue

        for route_id in membership_ids:
            memberships_by_route[route_id].append(section)

        blockers.extend(_section_blockers(section_id, section))

    for route_id in route_by_id:
        if not memberships_by_route.get(route_id):
            blockers.append(
                f"{route_id}: at least one committed section required"
            )

    clean = _unique(blockers)
    if clean:
        return _blocked(*clean)

    output: list[CommittedBasisSectionHydraulicRowV1] = []
    for route_id, route in route_by_id.items():
        route_sections = sorted(
            memberships_by_route[route_id],
            key=lambda row: (
                int(getattr(row, "order", 0)),
                _text(getattr(row, "section_id", "")),
            ),
        )
        for section in route_sections:
            membership_ids = tuple(section.route_ids or ())
            output.append(
                CommittedBasisSectionHydraulicRowV1(
                    committed_route_id=route_id,
                    committed_route_label=(
                        _text(getattr(route, "route_label", ""))
                        or route_id
                    ),
                    basis=_text(getattr(route, "basis", "")),
                    section_id=section.section_id,
                    section_scope=section.section_scope,
                    route_ids=membership_ids,
                    shared_across_routes=len(membership_ids) > 1,
                    order=section.order,
                    from_label=section.from_label,
                    to_label=section.to_label,
                    carried_flow_kg_s=section.carried_flow_kg_s,
                    pipe_size_label=section.pipe_size_label,
                    dn=section.dn,
                    length_m=section.length_m,
                    k_total=section.k_total,
                    velocity_m_s=section.velocity_m_s,
                    reynolds_number=section.reynolds_number,
                    friction_factor=section.friction_factor,
                    friction_method=section.friction_method,
                    colebrook_iteration_count=(
                        section.colebrook_iteration_count
                    ),
                    colebrook_converged=section.colebrook_converged,
                    pressure_gradient_Pa_per_m=(
                        section.pressure_gradient_Pa_per_m
                    ),
                    straight_pressure_drop_Pa=(
                        section.straight_pressure_drop_Pa
                    ),
                    local_pressure_drop_Pa=section.local_pressure_drop_Pa,
                    section_total_pressure_drop_Pa=(
                        section.section_total_pressure_drop_Pa
                    ),
                )
            )

    output.sort(
        key=lambda row: (
            route_order[row.committed_route_id],
            row.order,
            row.section_id,
        )
    )
    return CommittedBasisSectionHydraulicResultV1(
        ready=True,
        rows=tuple(output),
        unique_section_count=len(seen_sections),
        route_count=len(route_by_id),
        status=(
            f"Ready — {len(seen_sections)} committed section(s) projected "
            f"across {len(route_by_id)} route(s)"
        ),
    )


def _resolve_committed_route_membership_v1(
    value: object,
    route_by_id: dict[str, object],
) -> str:
    """
    Resolve the frozen H-S54 scoped membership form ``leg-id:route-id``.

    Exact committed route IDs remain valid. A scoped value is accepted only
    when its suffix is a committed route and its prefix is that route's own
    leg scope. No topology inference or hydraulic recalculation occurs here.
    """
    membership_id = _text(value)
    if membership_id in route_by_id:
        return membership_id
    if ":" not in membership_id:
        return ""

    scope_id, route_id = membership_id.split(":", 1)
    scope_id = _text(scope_id)
    route_id = _text(route_id)
    if not scope_id or route_id not in route_by_id:
        return ""
    if route_id != scope_id and not route_id.startswith(scope_id + "-"):
        return ""
    return route_id


def _section_blockers(section_id: str, row: object) -> list[str]:
    blockers: list[str] = []
    if int(getattr(row, "order", -1)) < 0:
        blockers.append(f"{section_id}: non-negative order required")
    if int(getattr(row, "dn", 0)) <= 0:
        blockers.append(f"{section_id}: positive DN required")
    if int(getattr(row, "colebrook_iteration_count", -1)) < 0:
        blockers.append(
            f"{section_id}: non-negative Colebrook iteration count required"
        )

    positive = (
        "carried_flow_kg_s",
        "length_m",
        "velocity_m_s",
        "reynolds_number",
        "friction_factor",
        "pressure_gradient_Pa_per_m",
        "straight_pressure_drop_Pa",
        "section_total_pressure_drop_Pa",
    )
    non_negative = (
        "k_total",
        "local_pressure_drop_Pa",
    )
    for name in positive:
        value = _finite(getattr(row, name, None))
        if value is None or value <= 0.0:
            blockers.append(f"{section_id}: positive {name} required")
    for name in non_negative:
        value = _finite(getattr(row, name, None))
        if value is None or value < 0.0:
            blockers.append(f"{section_id}: non-negative {name} required")

    for name in (
        "section_scope",
        "pipe_size_label",
        "friction_method",
    ):
        if not _text(getattr(row, name, "")):
            blockers.append(f"{section_id}: {name} required")
    if not bool(getattr(row, "colebrook_converged", False)):
        blockers.append(f"{section_id}: converged Colebrook evidence required")
    return blockers


def _blocked(*blockers: str) -> CommittedBasisSectionHydraulicResultV1:
    clean = _unique(blockers)
    return CommittedBasisSectionHydraulicResultV1(
        ready=False,
        blockers=clean,
        status="Blocked — " + "; ".join(clean),
    )


def _finite(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _text(value: object) -> str:
    return str(value or "").strip()


def _unique(values) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        clean = _text(value)
        if clean and clean not in output:
            output.append(clean)
    return tuple(output)
