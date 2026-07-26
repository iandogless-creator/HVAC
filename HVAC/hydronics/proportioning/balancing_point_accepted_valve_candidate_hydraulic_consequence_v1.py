# ======================================================================
# H-S52-C — Accepted catalogue valve-candidate hydraulic consequence
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import (
    ACCEPTED_KVS_DP_FORMULA_V1,
    calculate_accepted_kvs_hydraulic_consequence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_candidate_acceptance_intent_v1 import (
    ResolvedPointValveCandidateAcceptanceV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    BalancingPointValveProductSearchDutyEnvelopeV1,
)


NO_ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_REQUIRED = (
    "no_accepted_valve_candidate_consequence_required"
)
ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_PENDING = (
    "accepted_valve_candidate_consequence_pending"
)
ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE = (
    "accepted_valve_candidate_consequence_available"
)
ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_UNAVAILABLE = (
    "accepted_valve_candidate_consequence_unavailable"
)


@dataclass(frozen=True, slots=True)
class BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1:
    balancing_point_id: str = ""
    ready: bool = False
    consequence_state_id: str = ""
    consequence_available: bool = False
    accepted: bool = False
    catalog_id: str = ""
    valve_ref: str = ""
    current_kv_m3_h: float | None = None
    flow_m3_h: float | None = None
    controlled_circuit_dp_pa: float | None = None
    implied_valve_dp_bar: float | None = None
    implied_valve_dp_pa: float | None = None
    implied_authority: float | None = None
    status: str = ""
    blockers: tuple[str, ...] = ()
    formula: str = ACCEPTED_KVS_DP_FORMULA_V1


@dataclass(frozen=True, slots=True)
class BalancingPointAcceptedValveCandidateHydraulicConsequenceV1:
    """Preview the consequence of current catalogue Kv evidence.

    The persisted H-S52-A catalogue ID and valve reference remain the manual
    identity authority. Current Kv is resolved afresh from H-S50-A and is not
    copied into ProjectState. This projection does not commit product
    hydraulics, a valve setting or final balancing.
    """

    schema: str = (
        "balancing_point_accepted_valve_candidate_"
        "hydraulic_consequence_v1"
    )
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[
        BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1,
        ...,
    ] = ()
    exclusions: tuple[str, ...] = (
        "No automatic valve-candidate acceptance",
        "No candidate ranking or recommendation",
        "No committed valve product selection",
        "No valve size, DN, connection or setting selected",
        "No product-derived hydraulic mutation",
        "No design valve pressure drop changed",
        "No design authority changed",
        "No pump selection",
        "No pipe resizing",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Current catalogue Kv consequence is read-only preview evidence and "
        "requires manual engineering review."
    )


def build_balancing_point_accepted_valve_candidate_hydraulic_consequence_v1(
    duty_envelopes: BalancingPointValveProductSearchDutyEnvelopeV1 | None,
    acceptance_resolution: ResolvedPointValveCandidateAcceptanceV1 | None,
) -> BalancingPointAcceptedValveCandidateHydraulicConsequenceV1:
    """Join approved point duty to current accepted catalogue identity."""

    if not isinstance(
        duty_envelopes,
        BalancingPointValveProductSearchDutyEnvelopeV1,
    ):
        return _blocked_projection("H-S49-A duty envelopes required")
    if not isinstance(
        acceptance_resolution,
        ResolvedPointValveCandidateAcceptanceV1,
    ):
        return _blocked_projection(
            "H-S52-A valve-candidate acceptance resolution required"
        )

    envelope_rows = tuple(duty_envelopes.rows or ())
    if not envelope_rows:
        return _blocked_projection("H-S49-A point duty rows required")

    resolved_by_id = _rows_by_id_v1(
        tuple(acceptance_resolution.rows or ()),
        source="H-S52-A",
    )
    if isinstance(resolved_by_id, str):
        return _blocked_projection(resolved_by_id)

    envelope_ids = tuple(
        _stable_id_v1(row.balancing_point_id) for row in envelope_rows
    )
    if any(not point_id for point_id in envelope_ids):
        return _blocked_projection(
            "Every H-S49-A row requires balancing_point_id"
        )
    if len(set(envelope_ids)) != len(envelope_ids):
        return _blocked_projection(
            "Duplicate H-S49-A balancing_point_id values"
        )

    rows = tuple(
        _resolve_row_v1(
            envelope,
            resolved_by_id.get(_stable_id_v1(envelope.balancing_point_id)),
        )
        for envelope in envelope_rows
    )
    upstream = tuple(
        f"H-S49-A: {value}"
        for value in tuple(duty_envelopes.blockers or ())
    ) + tuple(
        f"H-S52-A: {value}"
        for value in tuple(acceptance_resolution.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream, *row_blockers))
    ready = (
        bool(duty_envelopes.ready)
        and bool(acceptance_resolution.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not ready and not blockers:
        blockers = (
            "Upstream duty-envelope or candidate-acceptance evidence "
            "is not ready",
        )

    available_count = sum(1 for row in rows if row.consequence_available)
    pending_count = sum(
        1
        for row in rows
        if row.consequence_state_id
        == ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_PENDING
    )
    return BalancingPointAcceptedValveCandidateHydraulicConsequenceV1(
        ready=ready,
        status=(
            "Ready — accepted catalogue valve-candidate consequence "
            f"available at {available_count} point(s); "
            f"{pending_count} acceptance(s) pending"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(envelope, resolved):
    point_id = _stable_id_v1(envelope.balancing_point_id)
    if not bool(getattr(envelope, "product_search_required", False)):
        return BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1(
            balancing_point_id=point_id,
            ready=bool(getattr(envelope, "ready", False)),
            consequence_state_id=(
                NO_ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_REQUIRED
            ),
            status="No accepted catalogue-candidate consequence required",
        )

    if resolved is None or not bool(getattr(resolved, "accepted", False)):
        blockers = _unique_v1(
            tuple(getattr(resolved, "blockers", ()) or ())
        )
        if blockers:
            return BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1(
                balancing_point_id=point_id,
                ready=False,
                consequence_state_id=(
                    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_UNAVAILABLE
                ),
                catalog_id=str(
                    getattr(resolved, "catalog_id", "") or ""
                ),
                valve_ref=str(
                    getattr(resolved, "valve_ref", "") or ""
                ),
                status=(
                    "Blocked — accepted catalogue-candidate consequence "
                    "unavailable"
                ),
                blockers=blockers,
            )
        return BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1(
            balancing_point_id=point_id,
            ready=bool(getattr(envelope, "ready", False)),
            consequence_state_id=(
                ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_PENDING
            ),
            status=(
                "Manual valve-candidate acceptance pending — "
                "no catalogue consequence yet"
            ),
        )

    current_kv = getattr(resolved, "current_kv_m3_h", None)
    flow_m3_h = getattr(envelope, "flow_m3_h", None)
    controlled_dp = getattr(envelope, "controlled_circuit_dp_pa", None)
    try:
        implied_bar, implied_pa, authority = (
            calculate_accepted_kvs_hydraulic_consequence_v1(
                flow_m3_h=flow_m3_h,
                accepted_kvs=current_kv,
                controlled_circuit_dp_pa=controlled_dp,
            )
        )
    except ValueError as exc:
        return BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1(
            balancing_point_id=point_id,
            ready=False,
            consequence_state_id=(
                ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_UNAVAILABLE
            ),
            accepted=True,
            catalog_id=str(getattr(resolved, "catalog_id", "") or ""),
            valve_ref=str(getattr(resolved, "valve_ref", "") or ""),
            current_kv_m3_h=current_kv,
            flow_m3_h=flow_m3_h,
            controlled_circuit_dp_pa=controlled_dp,
            status=(
                "Blocked — accepted catalogue-candidate consequence "
                "unavailable"
            ),
            blockers=(str(exc),),
        )

    return BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1(
        balancing_point_id=point_id,
        ready=True,
        consequence_state_id=(
            ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE
        ),
        consequence_available=True,
        accepted=True,
        catalog_id=str(getattr(resolved, "catalog_id", "") or ""),
        valve_ref=str(getattr(resolved, "valve_ref", "") or ""),
        current_kv_m3_h=float(current_kv),
        flow_m3_h=float(flow_m3_h),
        controlled_circuit_dp_pa=float(controlled_dp),
        implied_valve_dp_bar=implied_bar,
        implied_valve_dp_pa=implied_pa,
        implied_authority=authority,
        status=(
            "Accepted catalogue valve-candidate hydraulic consequence "
            "available — preview only; manual review required"
        ),
    )


def _rows_by_id_v1(rows: tuple, *, source: str) -> dict | str:
    result = {}
    for row in rows:
        point_id = _stable_id_v1(getattr(row, "balancing_point_id", ""))
        if not point_id:
            return f"Every {source} row requires balancing_point_id"
        if point_id in result:
            return f"Duplicate {source} balancing_point_id: {point_id}"
        result[point_id] = row
    return result


def _stable_id_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(
    *blockers: str,
) -> BalancingPointAcceptedValveCandidateHydraulicConsequenceV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointAcceptedValveCandidateHydraulicConsequenceV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
