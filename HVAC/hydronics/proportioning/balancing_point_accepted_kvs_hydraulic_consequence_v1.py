# ======================================================================
# H-S48-C — Accepted generic Kvs hydraulic-consequence evidence
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_acceptance_intent_v1 import (
    ResolvedPointKvsCandidateAcceptanceV1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_utilisation_evidence_v1 import (
    BalancingPointKvsCandidateUtilisationEvidenceV1,
)
from HVAC.hydronics.proportioning.valve_authority_preview_v1 import (
    calculate_valve_authority_v1,
)


NO_ACCEPTED_KVS_CONSEQUENCE_REQUIRED = (
    "no_accepted_kvs_consequence_required"
)
ACCEPTED_KVS_CONSEQUENCE_PENDING = "accepted_kvs_consequence_pending"
ACCEPTED_KVS_CONSEQUENCE_AVAILABLE = "accepted_kvs_consequence_available"
ACCEPTED_KVS_CONSEQUENCE_UNAVAILABLE = "accepted_kvs_consequence_unavailable"
ACCEPTED_KVS_DP_FORMULA_V1 = (
    "implied_valve_dp_bar = (flow_m3_h / accepted_kvs)^2"
)


@dataclass(frozen=True, slots=True)
class BalancingPointAcceptedKvsHydraulicConsequenceRowV1:
    balancing_point_id: str = ""
    ready: bool = False
    consequence_state_id: str = ""
    consequence_available: bool = False
    accepted: bool = False
    accepted_kvs: float | None = None
    flow_m3_h: float | None = None
    controlled_circuit_dp_pa: float | None = None
    implied_valve_dp_bar: float | None = None
    implied_valve_dp_pa: float | None = None
    implied_authority: float | None = None
    status: str = ""
    blockers: tuple[str, ...] = ()
    formula: str = ACCEPTED_KVS_DP_FORMULA_V1


@dataclass(frozen=True, slots=True)
class BalancingPointAcceptedKvsHydraulicConsequenceV1:
    """Preview consequences of explicit H-S48-A generic-Kvs acceptance.

    This projection does not replace design valve pressure drop or authority,
    alter the hydraulic model, choose a valve product/size/setting, or grant
    final engineering approval.
    """

    schema: str = "balancing_point_accepted_kvs_hydraulic_consequence_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointAcceptedKvsHydraulicConsequenceRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic Kvs acceptance",
        "No design valve pressure drop changed",
        "No design authority changed",
        "No hydraulic calculation input mutated",
        "No valve product selected",
        "No valve size or setting selected",
        "No manufacturer catalogue used",
        "No pump selected",
        "No pipe resizing",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Accepted generic Kvs consequence evidence is preview-only and "
        "requires manual engineering review."
    )


def calculate_accepted_kvs_hydraulic_consequence_v1(
    *,
    flow_m3_h: float,
    accepted_kvs: float,
    controlled_circuit_dp_pa: float,
) -> tuple[float, float, float]:
    """Return implied valve Δp bar, Δp Pa and point authority."""

    flow = _positive_finite_v1(flow_m3_h)
    kvs = _positive_finite_v1(accepted_kvs)
    controlled_dp = _positive_finite_v1(controlled_circuit_dp_pa)
    if flow is None:
        raise ValueError("flow_m3_h must be positive and finite")
    if kvs is None:
        raise ValueError("accepted_kvs must be positive and finite")
    if controlled_dp is None:
        raise ValueError(
            "controlled_circuit_dp_pa must be positive and finite"
        )

    implied_dp_bar = (flow / kvs) ** 2
    implied_dp_pa = implied_dp_bar * 100_000.0
    authority = calculate_valve_authority_v1(
        design_valve_dp_pa=implied_dp_pa,
        controlled_circuit_dp_pa=controlled_dp,
    )
    return implied_dp_bar, implied_dp_pa, authority


def build_balancing_point_accepted_kvs_hydraulic_consequence_v1(
    utilisation_evidence: BalancingPointKvsCandidateUtilisationEvidenceV1 | None,
    acceptance_resolution: ResolvedPointKvsCandidateAcceptanceV1 | None,
) -> BalancingPointAcceptedKvsHydraulicConsequenceV1:
    """Build point-scoped evidence without changing upstream calculations."""

    if utilisation_evidence is None:
        return _blocked_projection("H-S47-C utilisation evidence required")
    if not isinstance(
        utilisation_evidence,
        BalancingPointKvsCandidateUtilisationEvidenceV1,
    ):
        return _blocked_projection(
            "utilisation_evidence is not "
            "BalancingPointKvsCandidateUtilisationEvidenceV1"
        )
    if acceptance_resolution is None:
        return _blocked_projection("H-S48-A acceptance resolution required")
    if not isinstance(
        acceptance_resolution,
        ResolvedPointKvsCandidateAcceptanceV1,
    ):
        return _blocked_projection(
            "acceptance_resolution is not "
            "ResolvedPointKvsCandidateAcceptanceV1"
        )

    evidence_rows = tuple(utilisation_evidence.rows or ())
    if not evidence_rows:
        return _blocked_projection("H-S47-C point evidence rows required")

    resolved_by_id = {
        _stable_id_v1(row.balancing_point_id): row
        for row in tuple(acceptance_resolution.rows or ())
    }
    evidence_ids = tuple(
        _stable_id_v1(row.balancing_point_id) for row in evidence_rows
    )
    if any(not point_id for point_id in evidence_ids):
        return _blocked_projection(
            "Every H-S47-C row requires balancing_point_id"
        )
    if len(set(evidence_ids)) != len(evidence_ids):
        return _blocked_projection(
            "Duplicate H-S47-C balancing_point_id values"
        )

    rows = tuple(
        _resolve_row_v1(
            evidence_row,
            resolved_by_id.get(_stable_id_v1(evidence_row.balancing_point_id)),
        )
        for evidence_row in evidence_rows
    )
    upstream_blockers = tuple(
        f"H-S47-C: {value}"
        for value in tuple(utilisation_evidence.blockers or ())
    ) + tuple(
        f"H-S48-A: {value}"
        for value in tuple(acceptance_resolution.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = (
        bool(utilisation_evidence.ready)
        and bool(acceptance_resolution.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not ready and not blockers:
        blockers = ("Upstream Kvs evidence or acceptance is not ready",)

    available_count = sum(1 for row in rows if row.consequence_available)
    pending_count = sum(
        1
        for row in rows
        if row.consequence_state_id == ACCEPTED_KVS_CONSEQUENCE_PENDING
    )
    return BalancingPointAcceptedKvsHydraulicConsequenceV1(
        ready=ready,
        status=(
            f"Ready — accepted Kvs consequence available at "
            f"{available_count} point(s); {pending_count} acceptance(s) pending"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(evidence_row, resolved_row):
    point_id = _stable_id_v1(evidence_row.balancing_point_id)
    candidates = tuple(getattr(evidence_row, "kvs_candidates", ()) or ())

    if not candidates:
        return BalancingPointAcceptedKvsHydraulicConsequenceRowV1(
            balancing_point_id=point_id,
            ready=bool(getattr(evidence_row, "ready", False)),
            consequence_state_id=NO_ACCEPTED_KVS_CONSEQUENCE_REQUIRED,
            status="No accepted-Kvs consequence required — no valve duty",
        )

    if resolved_row is None or not bool(getattr(resolved_row, "accepted", False)):
        blockers = _unique_v1(
            tuple(getattr(resolved_row, "blockers", ()) or ())
        )
        if blockers:
            return BalancingPointAcceptedKvsHydraulicConsequenceRowV1(
                balancing_point_id=point_id,
                ready=False,
                consequence_state_id=ACCEPTED_KVS_CONSEQUENCE_UNAVAILABLE,
                accepted_kvs=getattr(resolved_row, "accepted_kvs", None),
                status="Blocked — accepted Kvs consequence unavailable",
                blockers=blockers,
            )
        return BalancingPointAcceptedKvsHydraulicConsequenceRowV1(
            balancing_point_id=point_id,
            ready=bool(getattr(evidence_row, "ready", False)),
            consequence_state_id=ACCEPTED_KVS_CONSEQUENCE_PENDING,
            status="Manual generic Kvs acceptance pending — no consequence yet",
        )

    accepted_kvs = getattr(resolved_row, "accepted_kvs", None)
    flow_m3_h = getattr(evidence_row, "flow_m3_h", None)
    controlled_dp = getattr(evidence_row, "controlled_circuit_dp_pa", None)
    try:
        implied_bar, implied_pa, authority = (
            calculate_accepted_kvs_hydraulic_consequence_v1(
                flow_m3_h=flow_m3_h,
                accepted_kvs=accepted_kvs,
                controlled_circuit_dp_pa=controlled_dp,
            )
        )
    except ValueError as exc:
        blocker = str(exc)
        return BalancingPointAcceptedKvsHydraulicConsequenceRowV1(
            balancing_point_id=point_id,
            ready=False,
            consequence_state_id=ACCEPTED_KVS_CONSEQUENCE_UNAVAILABLE,
            accepted=True,
            accepted_kvs=accepted_kvs,
            flow_m3_h=flow_m3_h,
            controlled_circuit_dp_pa=controlled_dp,
            status="Blocked — accepted Kvs consequence unavailable",
            blockers=(blocker,),
        )

    return BalancingPointAcceptedKvsHydraulicConsequenceRowV1(
        balancing_point_id=point_id,
        ready=True,
        consequence_state_id=ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
        consequence_available=True,
        accepted=True,
        accepted_kvs=float(accepted_kvs),
        flow_m3_h=float(flow_m3_h),
        controlled_circuit_dp_pa=float(controlled_dp),
        implied_valve_dp_bar=implied_bar,
        implied_valve_dp_pa=implied_pa,
        implied_authority=authority,
        status=(
            "Accepted generic Kvs hydraulic consequence available — "
            "manual review required"
        ),
    )


def _stable_id_v1(value: object) -> str:
    return str(value or "").strip()


def _positive_finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0.0:
        return None
    return number


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(
    *blockers: str,
) -> BalancingPointAcceptedKvsHydraulicConsequenceV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointAcceptedKvsHydraulicConsequenceV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
