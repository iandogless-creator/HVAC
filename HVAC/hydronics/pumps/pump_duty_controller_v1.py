"""H-S73-B: committed-basis route ledger and explicit final pump-duty commit.

Chosen pipework totals include Local K. Old allocated balancing resistance is
comparison evidence only; it is REPLACED by the explicit operating-Kv loss,
never added again. Shared valves enter each governed route once, at point flow.
No live design inputs, manufacturer choice, valve setting or upstream mutation.
"""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math

from HVAC.hydronics.pumps.pump_duty_basis_v1 import (
    PumpDutyAcceptanceV1, PumpDutyBasisV1, PumpPointKvV1, PumpRouteEquipmentV1,
)
from HVAC.hydronics.pumps.pump_duty_runner_v1 import valve_loss_Pa_v1
from HVAC.hydronics.pumps.pump_preview_controller_v1 import preview_pump_v1
from HVAC.hydronics.pumps.pump_preview_runner_v1 import PumpPreviewNumbersV1, run_pump_preview_v1
from HVAC.hydronics.proportioning.committed_point_level_balancing_reconciliation_v1 import (
    build_committed_point_level_balancing_reconciliation_v1,
)

TOLERANCE_PA = 0.05


@dataclass(frozen=True, slots=True)
class PumpDutyPointV1:
    point_id: str
    label: str
    route_ids: tuple[str, ...]
    mass_flow_kg_s: float
    kvs: float
    allocated_Pa: float
    operating_kv: float | None = None
    rated_loss_Pa: float | None = None
    operating_loss_Pa: float | None = None


@dataclass(frozen=True, slots=True)
class PumpDutyRouteV1:
    route_id: str
    label: str
    pipework_Pa: float
    equipment_Pa: float | None = None
    valve_Pa: float | None = None
    total_Pa: float | None = None
    residual_Pa: float | None = None
    controlling: bool = False


@dataclass(frozen=True, slots=True)
class PumpDutyResultV1:
    ready: bool = False
    acceptance_ready: bool = False
    accepted: bool = False
    blockers: tuple[str, ...] = ()
    acceptance_blockers: tuple[str, ...] = ()
    preview_basis_fingerprint: str = ""
    basis_fingerprint: str = ""
    routes: tuple[PumpDutyRouteV1, ...] = ()
    points: tuple[PumpDutyPointV1, ...] = ()
    numbers: PumpPreviewNumbersV1 | None = None
    controlling_route_ids: tuple[str, ...] = ()


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def _finite(value, *, positive=False) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and (value > 0 if positive else value >= 0))


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 2000


def _context(project) -> PumpDutyResultV1:
    base = preview_pump_v1(project)
    routes = tuple(PumpDutyRouteV1(key, label, float(dp))
                   for key, label, dp in base.route_pressures)
    if not base.ready:
        return PumpDutyResultV1(routes=routes, blockers=base.blockers)
    snapshot = project.hydronic_proportioned_basis_snapshot
    reconciliation = build_committed_point_level_balancing_reconciliation_v1(snapshot)
    if not reconciliation.ready:
        return PumpDutyResultV1(routes=routes, blockers=tuple(
            f"Committed balancing basis: {b}" for b in reconciliation.blockers))
    bridge = {row.allocation_route_id: row.committed_route_id for row in reconciliation.route_rows}
    if len(bridge) != len(routes) or set(bridge.values()) != {r.route_id for r in routes}:
        return PumpDutyResultV1(routes=routes, blockers=("Exact committed route/point identity coverage required.",))
    points = []
    for row in reconciliation.point_rows:
        mapped = tuple(sorted(bridge.get(key, key) for key in row.downstream_route_ids))
        if (not mapped or len(set(mapped)) != len(mapped)
                or not set(mapped) <= set(bridge.values())):
            return PumpDutyResultV1(routes=routes, blockers=(f"{row.balancing_point_id}: ambiguous governed routes.",))
        if row.valve_duty_required:
            points.append(PumpDutyPointV1(
                row.balancing_point_id, row.label, mapped, float(row.point_flow_kg_s),
                float(row.accepted_kvs_basis), float(row.allocated_added_pressure_drop_Pa),
            ))
    # Recheck membership and sums rather than trusting a stored 'conserved' flag.
    for row in reconciliation.route_rows:
        governed = {p.point_id for p in points if row.committed_route_id in p.route_ids}
        contributors = row.contributing_balancing_point_ids
        total = sum(p.allocated_Pa for p in points if p.point_id in governed)
        if (len(set(contributors)) != len(contributors) or governed != set(contributors)
                or not math.isclose(total, row.required_added_pressure_drop_Pa,
                                    rel_tol=0, abs_tol=TOLERANCE_PA)):
            return PumpDutyResultV1(routes=routes, blockers=(f"{row.committed_route_id}: inconsistent point membership/allocation.",))
    basis = project.hydronic_pump_preview_basis
    fingerprint = _digest({
        "snapshot": base.fingerprint,
        "density": float(basis.density_kg_m3),
        "common_loss": float(basis.additional_common_loss_Pa),
        "margin": float(basis.head_margin_percent),
        "source_note": basis.source_note,
    })
    return PumpDutyResultV1(routes=routes, points=tuple(sorted(points, key=lambda p: p.point_id)),
                            preview_basis_fingerprint=fingerprint)


def _evaluate(project, basis, context) -> PumpDutyResultV1:
    if context.blockers:
        return context
    if not isinstance(basis, PumpDutyBasisV1):
        return replace(context, blockers=("Enter every route loss (0 if none), review generic Kv and apply the duty basis.",))
    blockers = []
    if basis.preview_basis_fingerprint != context.preview_basis_fingerprint:
        blockers.append("Committed snapshot or fluid/common-loss/margin basis changed; review and reapply.")
    route_ids = [r.route_id for r in basis.routes]
    point_ids = [p.point_id for p in basis.points]
    if not all(_text(key) for key in route_ids + point_ids):
        return replace(context, blockers=("Route and valve point identities must be non-empty strings.",))
    if (len(set(route_ids)) != len(route_ids)
            or set(route_ids) != {r.route_id for r in context.routes}):
        blockers.append("Exactly one equipment-loss input is required for each committed route.")
    if (len(set(point_ids)) != len(point_ids)
            or set(point_ids) != {p.point_id for p in context.points}):
        blockers.append("Exactly one Kv review is required for each committed valve point.")
    for row in basis.routes:
        if not _finite(row.pressure_Pa) or not _text(row.source_note):
            blockers.append(f"{row.route_id}: finite additional loss ≥ 0 Pa and source note required.")
    for row in basis.points:
        if row.operating_kv is not None and not _finite(row.operating_kv, positive=True):
            blockers.append(f"{row.point_id}: positive finite operating Kv required, or leave blank for Kvs-only preview.")
    if not _text(basis.review_note) or type(basis.reviewed) is not bool:
        blockers.append("A review note and Boolean review status are required.")
    if blockers:
        return replace(context, blockers=tuple(blockers))
    inputs = {p.point_id: p.operating_kv for p in basis.points}
    acceptance_blockers = []
    points = []
    density = float(project.hydronic_pump_preview_basis.density_kg_m3)
    try:
        for point in context.points:
            kv = inputs[point.point_id]
            if kv is not None and kv > point.kvs:
                blockers.append(f"{point.point_id}: operating Kv exceeds committed Kvs {point.kvs:g}.")
                continue
            rated = valve_loss_Pa_v1(mass_flow_kg_s=point.mass_flow_kg_s, density_kg_m3=density, kv=point.kvs)
            loss = valve_loss_Pa_v1(mass_flow_kg_s=point.mass_flow_kg_s, density_kg_m3=density,
                                   kv=point.kvs if kv is None else kv)
            points.append(replace(point, operating_kv=kv, rated_loss_Pa=rated, operating_loss_Pa=loss))
            if kv is None:
                acceptance_blockers.append(f"{point.point_id}: explicitly enter operating Kv; Kvs alone is preview evidence.")
        if blockers:
            return replace(context, blockers=tuple(blockers))
        equipment = {r.route_id: r.pressure_Pa for r in basis.routes}
        routes = []
        for route in context.routes:
            valve = sum(p.operating_loss_Pa for p in points if route.route_id in p.route_ids)
            total = route.pipework_Pa + equipment[route.route_id] + valve
            if not _finite(total):
                raise ValueError("Route total exceeds the numerical range")
            routes.append(replace(route, equipment_Pa=equipment[route.route_id], valve_Pa=valve, total_Pa=total))
        target = max(r.total_Pa for r in routes)
        routes = tuple(replace(r, residual_Pa=target-r.total_Pa,
                               controlling=target-r.total_Pa <= TOLERANCE_PA) for r in routes)
        for route in routes:
            if route.residual_Pa > TOLERANCE_PA:
                acceptance_blockers.append(f"{route.route_id}: {route.residual_Pa:.6g} Pa remains to reconcile; review equipment/operating Kv.")
        base = project.hydronic_pump_preview_basis
        initial = preview_pump_v1(project)
        numbers = run_pump_preview_v1(mass_flow_kg_s=initial.mass_flow_kg_s, density_kg_m3=density,
                                      pipework_pressure_Pa=target,
                                      additional_common_loss_Pa=base.additional_common_loss_Pa,
                                      head_margin_percent=base.head_margin_percent)
        if not all(_finite(v, positive=True) for v in asdict(numbers).values()):
            raise ValueError("Pump duty must be positive and finite")
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        return replace(context, blockers=(str(exc),))
    if not basis.reviewed:
        acceptance_blockers.append("Confirm the fluid, equipment coverage and control basis review.")
    fingerprint = _digest({"version": "pump_duty_v1", "basis": basis.to_dict(),
                           "numbers": asdict(numbers), "routes": [asdict(r) for r in routes],
                           "points": [asdict(p) for p in points]})
    acceptance_ready = not acceptance_blockers
    saved = getattr(project, "hydronic_pump_duty_acceptance", None)
    accepted = bool(acceptance_ready and isinstance(saved, PumpDutyAcceptanceV1)
                    and saved.basis_fingerprint == fingerprint and saved.review_note == basis.review_note
                    and all(_finite(getattr(saved, key), positive=True)
                            and getattr(saved, key) == value for key, value in asdict(numbers).items()))
    return PumpDutyResultV1(
        ready=True, acceptance_ready=acceptance_ready, accepted=accepted,
        acceptance_blockers=tuple(acceptance_blockers), numbers=numbers,
        preview_basis_fingerprint=context.preview_basis_fingerprint, basis_fingerprint=fingerprint,
        routes=routes, points=tuple(points),
        controlling_route_ids=tuple(r.route_id for r in routes if r.controlling),
    )


def preview_pump_duty_v1(project) -> PumpDutyResultV1:
    """Read-only; saved acceptance is authoritative only while this resolves it."""
    return _evaluate(project, getattr(project, "hydronic_pump_duty_basis", None), _context(project))


def _input_number(value, *, optional=False):
    if optional and (value is None or value == ""):
        return None
    if isinstance(value, bool):
        raise ValueError("Numeric inputs must not be Boolean")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Enter numeric losses and Kv values") from None
    if not math.isfinite(number):
        raise ValueError("Numeric inputs must be finite")
    return number


def apply_pump_duty_basis_v1(project, payload: dict) -> tuple[str, ...]:
    context = _context(project)
    if context.blockers:
        return context.blockers
    try:
        basis = PumpDutyBasisV1(
            preview_basis_fingerprint=context.preview_basis_fingerprint,
            routes=tuple(PumpRouteEquipmentV1(r["route_id"], _input_number(r["pressure_Pa"]),
                                              r["source_note"]) for r in payload["routes"]),
            points=tuple(PumpPointKvV1(p["point_id"], _input_number(p["operating_kv"], optional=True))
                         for p in payload["points"]),
            review_note=payload["review_note"], reviewed=payload["reviewed"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        return (f"Invalid duty basis: {exc}",)
    result = _evaluate(project, basis, context)
    if not result.ready:
        return result.blockers
    project.hydronic_pump_duty_basis = basis
    project.hydronic_pump_duty_acceptance = None
    return ()


def accept_pump_duty_v1(project, expected_fingerprint: str) -> tuple[str, ...]:
    """Explicit, atomic commit of the exact duty last displayed for review."""
    result = preview_pump_duty_v1(project)
    if not result.ready or not result.acceptance_ready:
        return result.blockers + result.acceptance_blockers
    if not expected_fingerprint or expected_fingerprint != result.basis_fingerprint:
        return ("Displayed pump duty changed; refresh and review before accepting.",)
    project.hydronic_pump_duty_acceptance = PumpDutyAcceptanceV1(
        basis_fingerprint=result.basis_fingerprint, **asdict(result.numbers),
        review_note=project.hydronic_pump_duty_basis.review_note,
    )
    return ()


def clear_pump_duty_acceptance_v1(project) -> None:
    project.hydronic_pump_duty_acceptance = None


def clear_pump_duty_basis_v1(project) -> None:
    project.hydronic_pump_duty_basis = None
    project.hydronic_pump_duty_acceptance = None
