"""H-S73-A readiness and explicit preview-intent ownership boundary.

Only frozen committed hydraulic evidence is consumed. A ready preview is
not final pump duty, balancing acceptance, or permission to select a product.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math

from HVAC.hydronics.pumps.pump_preview_basis_v1 import PumpPreviewBasisV1
from HVAC.hydronics.pumps.pump_preview_runner_v1 import (
    PumpPreviewNumbersV1, run_pump_preview_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
    proportioned_basis_snapshot_from_dict_v1,
    proportioned_basis_snapshot_to_dict_v1,
)


@dataclass(frozen=True, slots=True)
class PumpPreviewResultV1:
    ready: bool = False
    blockers: tuple[str, ...] = ()
    mass_flow_kg_s: float | None = None
    flow_section_id: str = ""
    pipework_pressure_Pa: float | None = None
    controlling_route_ids: tuple[str, ...] = ()
    route_pressures: tuple[tuple[str, str, float], ...] = ()
    numbers: PumpPreviewNumbersV1 | None = None
    fingerprint: str = ""


def _number(value: object, *, positive=False) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and (value > 0 if positive else value >= 0))


def _basis_blockers(basis) -> list[str]:
    if not isinstance(basis, PumpPreviewBasisV1):
        return ["Enter and apply an explicit preview basis; no density or allowances are assumed."]
    reasons = []
    for field, label, positive in (
        ("density_kg_m3", "Positive finite fluid density", True),
        ("additional_common_loss_Pa", "Finite common-loss allowance ≥ 0 Pa", False),
        ("head_margin_percent", "Finite head margin ≥ 0%", False),
    ):
        if not _number(getattr(basis, field), positive=positive):
            reasons.append(label + " required.")
    if not isinstance(basis.source_note, str) or not basis.source_note.strip():
        reasons.append("Record the density source, operating temperature and allowance basis.")
    return reasons


def _snapshot_evidence(snapshot):
    if not isinstance(snapshot, ProportionedBasisSnapshotV1):
        return None, "", ["Commit a proportioning hydraulic basis first."]
    if snapshot.status not in {"COMMITTED_BASIS_ONLY", "COMMITTED_RESIZED_HYDRAULICS"}:
        return None, "", ["A supported committed hydraulic snapshot is required."]
    authority = snapshot.hydraulic_input_authority
    if authority is None or not authority.ready or authority.blockers:
        return None, "", ["Complete committed hydraulic-input authority is required."]
    if snapshot.return_arrangement_basis in (None, "", "UNDECIDED"):
        return None, "", ["A committed return-arrangement basis is required."]
    try:
        # Reject non-finite raw evidence before the existing loader can omit it.
        json.dumps(asdict(snapshot), allow_nan=False)
        # Use the existing persistence contract: it normalises legacy pipe
        # material defaults and numeric types on load. No ProjectState mutation.
        canonical = proportioned_basis_snapshot_from_dict_v1(
            proportioned_basis_snapshot_to_dict_v1(snapshot)
        )
        encoded = json.dumps(proportioned_basis_snapshot_to_dict_v1(canonical),
                             sort_keys=True, allow_nan=False,
                             separators=(",", ":")).encode()
    except (TypeError, ValueError):
        return None, "", ["Committed snapshot contains unsupported or non-finite evidence."]
    return authority, hashlib.sha256(encoded).hexdigest(), []


def preview_pump_v1(project) -> PumpPreviewResultV1:
    authority, fingerprint, blockers = _snapshot_evidence(
        getattr(project, "hydronic_proportioned_basis_snapshot", None)
    )
    if authority is None:
        return PumpPreviewResultV1(blockers=tuple(blockers))
    routes = tuple(authority.routes)
    route_ids = {r.route_id for r in routes}
    if (not routes or "" in route_ids or len(route_ids) != len(routes)
            or any(not _number(r.chosen_pressure_drop_Pa) for r in routes)):
        return PumpPreviewResultV1(
            blockers=("Unique committed routes with finite non-negative pressure are required.",),
            fingerprint=fingerprint,
        )
    # The first common-main section carries all legs. Never add section or
    # route flows: both repeat downstream loads. Require full route coverage.
    candidates = [s for s in authority.sections
                  if s.section_scope == "common_main" and s.order == 1
                  and set(s.route_ids) == route_ids]
    source = candidates[0] if len(candidates) == 1 else None
    mass = None
    if source is None or not _number(source.carried_flow_kg_s, positive=True):
        blockers.append("One committed first common-main section covering every route with positive flow is required.")
    else:
        mass = source.carried_flow_kg_s
    base = max(r.chosen_pressure_drop_Pa for r in routes)
    controlling = tuple(sorted(r.route_id for r in routes
                              if abs(r.chosen_pressure_drop_Pa - base) <= 0.05))
    basis = getattr(project, "hydronic_pump_preview_basis", None)
    blockers.extend(_basis_blockers(basis))
    if isinstance(basis, PumpPreviewBasisV1) and basis.snapshot_fingerprint != fingerprint:
        blockers.append("The committed snapshot changed; review and reapply the preview basis.")
    numbers = None
    if not blockers:
        numbers = run_pump_preview_v1(
            mass_flow_kg_s=mass, density_kg_m3=basis.density_kg_m3,
            pipework_pressure_Pa=base,
            additional_common_loss_Pa=basis.additional_common_loss_Pa,
            head_margin_percent=basis.head_margin_percent,
        )
        if not all(math.isfinite(x) for x in asdict(numbers).values()):
            blockers.append("The supplied basis exceeds the numerical range; review the inputs.")
            numbers = None
    return PumpPreviewResultV1(
        ready=not blockers, blockers=tuple(blockers), mass_flow_kg_s=mass,
        flow_section_id=source.section_id if source else "",
        pipework_pressure_Pa=base, controlling_route_ids=controlling,
        route_pressures=tuple((r.route_id, r.route_label, r.chosen_pressure_drop_Pa)
                              for r in sorted(routes, key=lambda r: r.route_id)),
        numbers=numbers, fingerprint=fingerprint,
    )


def apply_pump_preview_basis_v1(project, payload: dict) -> tuple[str, ...]:
    """Explicit user action; save intent only, never calculated pump output."""
    current = preview_pump_v1(project)
    if not current.fingerprint or current.mass_flow_kg_s is None:
        return current.blockers
    values = {}
    for key in ("density_kg_m3", "additional_common_loss_Pa", "head_margin_percent"):
        raw = payload.get(key)
        try:
            values[key] = float(raw) if not isinstance(raw, bool) else None
        except (TypeError, ValueError, OverflowError):
            values[key] = None
    basis = PumpPreviewBasisV1(**values, source_note=payload.get("source_note", ""),
                              snapshot_fingerprint=current.fingerprint)
    blockers = _basis_blockers(basis)
    if blockers:
        return tuple(blockers)
    # Validate range before mutating ProjectState.
    numbers = run_pump_preview_v1(
        mass_flow_kg_s=current.mass_flow_kg_s,
        density_kg_m3=basis.density_kg_m3,
        pipework_pressure_Pa=current.pipework_pressure_Pa,
        additional_common_loss_Pa=basis.additional_common_loss_Pa,
        head_margin_percent=basis.head_margin_percent,
    )
    if not all(math.isfinite(x) for x in asdict(numbers).values()):
        return ("The supplied basis exceeds the numerical range; review the inputs.",)
    project.hydronic_pump_preview_basis = basis
    return ()


def clear_pump_preview_basis_v1(project) -> None:
    project.hydronic_pump_preview_basis = None
