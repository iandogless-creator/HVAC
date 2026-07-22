# ======================================================================
# H-S49-A — Approved point valve product-search duty envelope
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    ResolvedPointAcceptedKvsConsequenceDispositionV1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import (
    ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
    BalancingPointAcceptedKvsHydraulicConsequenceV1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_utilisation_evidence_v1 import (
    BalancingPointKvsCandidateUtilisationEvidenceV1,
)


NO_PRODUCT_SEARCH_ENVELOPE_REQUIRED = "no_product_search_envelope_required"
PRODUCT_SEARCH_ENVELOPE_PENDING = "product_search_envelope_pending"
PRODUCT_SEARCH_ENVELOPE_REVISION_REQUIRED = (
    "product_search_envelope_revision_required"
)
PRODUCT_SEARCH_ENVELOPE_AVAILABLE = "product_search_envelope_available"
PRODUCT_SEARCH_ENVELOPE_UNAVAILABLE = "product_search_envelope_unavailable"


@dataclass(frozen=True, slots=True)
class BalancingPointValveProductSearchDutyEnvelopeRowV1:
    balancing_point_id: str = ""
    point_scope: str = ""
    point_role: str = ""
    label: str = ""
    topology: str = ""
    governed_route_ids: tuple[str, ...] = ()
    ready: bool = False
    envelope_state_id: str = ""
    product_search_required: bool = False
    envelope_available: bool = False
    approved_for_product_search: bool = False
    kvs_revision_required: bool = False
    point_flow_kg_s: float | None = None
    flow_m3_h: float | None = None
    required_kv: float | None = None
    accepted_kvs: float | None = None
    kvs_series_id: str = ""
    implied_valve_dp_bar: float | None = None
    implied_valve_dp_pa: float | None = None
    controlled_circuit_dp_pa: float | None = None
    implied_authority: float | None = None
    design_valve_dp_pa: float | None = None
    design_authority: float | None = None
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BalancingPointValveProductSearchDutyEnvelopeV1:
    """Approved point duties released for a later, separate product search."""

    schema: str = "balancing_point_valve_product_search_duty_envelope_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointValveProductSearchDutyEnvelopeRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic envelope approval",
        "No product search started",
        "No manufacturer catalogue used",
        "No valve product selected",
        "No valve size, DN, connection or setting selected",
        "No accepted Kvs changed",
        "No hydraulic calculation input mutated",
        "No pump selected",
        "No pipe resizing",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "An available envelope is a manually approved search input only; "
        "it is not a valve selection or product-search result."
    )


def build_balancing_point_valve_product_search_duty_envelope_v1(
    utilisation_evidence: BalancingPointKvsCandidateUtilisationEvidenceV1 | None,
    consequence_evidence: BalancingPointAcceptedKvsHydraulicConsequenceV1 | None,
    disposition_resolution: (
        ResolvedPointAcceptedKvsConsequenceDispositionV1 | None
    ),
) -> BalancingPointValveProductSearchDutyEnvelopeV1:
    if not isinstance(
        utilisation_evidence,
        BalancingPointKvsCandidateUtilisationEvidenceV1,
    ):
        return _blocked_projection("H-S47-C utilisation evidence required")
    if not isinstance(
        consequence_evidence,
        BalancingPointAcceptedKvsHydraulicConsequenceV1,
    ):
        return _blocked_projection("H-S48-C consequence evidence required")
    if not isinstance(
        disposition_resolution,
        ResolvedPointAcceptedKvsConsequenceDispositionV1,
    ):
        return _blocked_projection("H-S48-D disposition resolution required")

    source_rows = tuple(utilisation_evidence.rows or ())
    if not source_rows:
        return _blocked_projection("H-S47-C point rows required")

    consequence_by_id = _rows_by_id_v1(
        tuple(consequence_evidence.rows or ()),
        source="H-S48-C",
    )
    disposition_by_id = _rows_by_id_v1(
        tuple(disposition_resolution.rows or ()),
        source="H-S48-D",
    )
    if isinstance(consequence_by_id, str):
        return _blocked_projection(consequence_by_id)
    if isinstance(disposition_by_id, str):
        return _blocked_projection(disposition_by_id)

    rows = tuple(
        _resolve_row_v1(
            row,
            consequence_by_id.get(_stable_id_v1(row.balancing_point_id)),
            disposition_by_id.get(_stable_id_v1(row.balancing_point_id)),
        )
        for row in source_rows
    )
    upstream = tuple(
        f"H-S47-C: {value}"
        for value in tuple(utilisation_evidence.blockers or ())
    ) + tuple(
        f"H-S48-C: {value}"
        for value in tuple(consequence_evidence.blockers or ())
    ) + tuple(
        f"H-S48-D: {value}"
        for value in tuple(disposition_resolution.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream, *row_blockers))
    ready = (
        bool(utilisation_evidence.ready)
        and bool(consequence_evidence.ready)
        and bool(disposition_resolution.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not ready and not blockers:
        blockers = ("Upstream point-valve evidence is not ready",)

    available = sum(1 for row in rows if row.envelope_available)
    pending = sum(
        1
        for row in rows
        if row.envelope_state_id == PRODUCT_SEARCH_ENVELOPE_PENDING
    )
    revision = sum(1 for row in rows if row.kvs_revision_required)
    return BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=ready,
        status=(
            f"Ready — {available} approved product-search envelope(s); "
            f"{pending} pending; {revision} requiring Kvs revision"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(source_row, consequence_row, disposition_row):
    point_id = _stable_id_v1(source_row.balancing_point_id)
    common = dict(
        balancing_point_id=point_id,
        point_scope=_stable_id_v1(getattr(source_row, "point_scope", "")),
        point_role=_stable_id_v1(getattr(source_row, "point_role", "")),
        label=_stable_id_v1(getattr(source_row, "label", "")),
        topology=(
            "Shared"
            if bool(getattr(source_row, "is_shared", False))
            else "Route-exclusive"
            if bool(getattr(source_row, "is_route_exclusive", False))
            else ""
        ),
        governed_route_ids=tuple(
            _stable_id_v1(value)
            for value in tuple(
                getattr(source_row, "downstream_route_ids", ()) or ()
            )
            if _stable_id_v1(value)
        ),
        point_flow_kg_s=_finite_v1(
            getattr(source_row, "point_flow_kg_s", None)
        ),
        required_kv=_finite_v1(getattr(source_row, "required_kv", None)),
        kvs_series_id=_stable_id_v1(
            getattr(source_row, "kvs_series_id", "")
        ),
        design_valve_dp_pa=_finite_v1(
            getattr(source_row, "design_valve_dp_pa", None)
        ),
        design_authority=_finite_v1(getattr(source_row, "authority", None)),
    )
    candidates = tuple(getattr(source_row, "kvs_candidates", ()) or ())
    if not candidates:
        return BalancingPointValveProductSearchDutyEnvelopeRowV1(
            **common,
            ready=bool(getattr(source_row, "ready", False)),
            envelope_state_id=NO_PRODUCT_SEARCH_ENVELOPE_REQUIRED,
            product_search_required=False,
            status="No product-search envelope required — no valve duty",
        )

    if consequence_row is None or disposition_row is None:
        return _unavailable_row_v1(
            common,
            "Current H-S48-C consequence and H-S48-D disposition rows required",
        )

    consequence_available = bool(
        getattr(consequence_row, "consequence_available", False)
    ) and (
        getattr(consequence_row, "consequence_state_id", "")
        == ACCEPTED_KVS_CONSEQUENCE_AVAILABLE
    )
    approved = bool(
        getattr(disposition_row, "approved_for_product_search", False)
    )
    revision = bool(getattr(disposition_row, "kvs_revision_required", False))

    if revision:
        return BalancingPointValveProductSearchDutyEnvelopeRowV1(
            **common,
            ready=bool(getattr(disposition_row, "ready", False)),
            envelope_state_id=PRODUCT_SEARCH_ENVELOPE_REVISION_REQUIRED,
            product_search_required=True,
            kvs_revision_required=True,
            accepted_kvs=_finite_v1(
                getattr(consequence_row, "accepted_kvs", None)
            ),
            status="Kvs revision required — product-search envelope withheld",
        )

    if not approved:
        return BalancingPointValveProductSearchDutyEnvelopeRowV1(
            **common,
            ready=(
                bool(getattr(consequence_row, "ready", False))
                and bool(getattr(disposition_row, "ready", False))
            ),
            envelope_state_id=PRODUCT_SEARCH_ENVELOPE_PENDING,
            product_search_required=True,
            accepted_kvs=_finite_v1(
                getattr(consequence_row, "accepted_kvs", None)
            ),
            status=(
                "Manual product-search approval pending"
                if consequence_available
                else "Accepted Kvs consequence pending"
            ),
        )

    evidence = dict(
        flow_m3_h=_positive_finite_v1(
            getattr(consequence_row, "flow_m3_h", None)
        ),
        accepted_kvs=_positive_finite_v1(
            getattr(consequence_row, "accepted_kvs", None)
        ),
        implied_valve_dp_bar=_positive_finite_v1(
            getattr(consequence_row, "implied_valve_dp_bar", None)
        ),
        implied_valve_dp_pa=_positive_finite_v1(
            getattr(consequence_row, "implied_valve_dp_pa", None)
        ),
        controlled_circuit_dp_pa=_positive_finite_v1(
            getattr(consequence_row, "controlled_circuit_dp_pa", None)
        ),
        implied_authority=_positive_finite_v1(
            getattr(consequence_row, "implied_authority", None)
        ),
    )
    missing = [name for name, value in evidence.items() if value is None]
    if not consequence_available:
        missing.append("accepted Kvs consequence availability")
    if not common["kvs_series_id"]:
        missing.append("generic Kvs series identity")
    if common["point_flow_kg_s"] is None:
        missing.append("point flow")
    if common["required_kv"] is None:
        missing.append("required Kv")
    if common["design_valve_dp_pa"] is None:
        missing.append("design valve pressure drop")
    if common["design_authority"] is None:
        missing.append("design authority")
    if missing:
        return _unavailable_row_v1(
            common,
            "Approved envelope evidence unavailable: " + ", ".join(missing),
        )

    return BalancingPointValveProductSearchDutyEnvelopeRowV1(
        **common,
        **evidence,
        ready=True,
        envelope_state_id=PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
        product_search_required=True,
        envelope_available=True,
        approved_for_product_search=True,
        status="Approved product-search duty envelope available — search not started",
    )


def _unavailable_row_v1(common: dict, blocker: str):
    return BalancingPointValveProductSearchDutyEnvelopeRowV1(
        **common,
        ready=False,
        envelope_state_id=PRODUCT_SEARCH_ENVELOPE_UNAVAILABLE,
        product_search_required=True,
        status="Blocked — product-search duty envelope unavailable",
        blockers=(blocker,),
    )


def _rows_by_id_v1(rows: tuple, *, source: str):
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


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result = []
    for value in values:
        text = _stable_id_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(*blockers: str):
    clean = _unique_v1(tuple(blockers))
    return BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
