# ======================================================================
# H-S53-A — Approved catalogue valve-candidate design duty envelope
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_consequence_disposition_intent_v1 import (
    ResolvedPointAcceptedValveCandidateConsequenceDispositionV1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_hydraulic_consequence_v1 import (
    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE,
    NO_ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_REQUIRED,
    BalancingPointAcceptedValveCandidateHydraulicConsequenceV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    BalancingPointValveProductSearchDutyEnvelopeV1,
)


NO_DETAILED_VALVE_DESIGN_DUTY_REQUIRED = (
    "no_detailed_valve_design_duty_required"
)
DETAILED_VALVE_DESIGN_DUTY_PENDING = (
    "detailed_valve_design_duty_pending"
)
DETAILED_VALVE_DESIGN_DUTY_REVISION_REQUIRED = (
    "detailed_valve_design_duty_revision_required"
)
DETAILED_VALVE_DESIGN_DUTY_AVAILABLE = (
    "detailed_valve_design_duty_available"
)
DETAILED_VALVE_DESIGN_DUTY_UNAVAILABLE = (
    "detailed_valve_design_duty_unavailable"
)


@dataclass(frozen=True, slots=True)
class BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1:
    balancing_point_id: str = ""
    point_scope: str = ""
    point_role: str = ""
    label: str = ""
    topology: str = ""
    governed_route_ids: tuple[str, ...] = ()
    ready: bool = False
    envelope_state_id: str = ""
    detailed_valve_design_required: bool = False
    envelope_available: bool = False
    approved_for_later_valve_design: bool = False
    valve_candidate_revision_required: bool = False
    catalog_id: str = ""
    valve_ref: str = ""
    current_kv_m3_h: float | None = None
    point_flow_kg_s: float | None = None
    flow_m3_h: float | None = None
    required_kv: float | None = None
    controlled_circuit_dp_pa: float | None = None
    implied_valve_dp_bar: float | None = None
    implied_valve_dp_pa: float | None = None
    implied_authority: float | None = None
    design_valve_dp_pa: float | None = None
    design_authority: float | None = None
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1:
    """Read-only duty released for a later detailed valve-design stage."""

    schema: str = (
        "balancing_point_approved_valve_candidate_"
        "design_duty_envelope_v1"
    )
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[
        BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1,
        ...,
    ] = ()
    exclusions: tuple[str, ...] = (
        "No automatic detailed valve-design approval",
        "No catalogue identity or valve reference mutation",
        "No committed valve product selection",
        "No valve size, DN, connection or setting selected",
        "No product-derived hydraulic mutation",
        "No design valve pressure drop or authority changed",
        "No pump selection",
        "No pipe resizing",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "An available envelope is approved input for a later separate "
        "detailed valve-design stage; it is not a selected valve size, "
        "connection or setting."
    )


def build_balancing_point_approved_valve_candidate_design_duty_envelope_v1(
    product_search_duties: (
        BalancingPointValveProductSearchDutyEnvelopeV1 | None
    ),
    consequence_evidence: (
        BalancingPointAcceptedValveCandidateHydraulicConsequenceV1 | None
    ),
    disposition_resolution: (
        ResolvedPointAcceptedValveCandidateConsequenceDispositionV1 | None
    ),
) -> BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1:
    if not isinstance(
        product_search_duties,
        BalancingPointValveProductSearchDutyEnvelopeV1,
    ):
        return _blocked_projection(
            "H-S49-A product-search duty envelopes required"
        )
    if not isinstance(
        consequence_evidence,
        BalancingPointAcceptedValveCandidateHydraulicConsequenceV1,
    ):
        return _blocked_projection(
            "H-S52-C accepted valve-candidate consequence evidence required"
        )
    if not isinstance(
        disposition_resolution,
        ResolvedPointAcceptedValveCandidateConsequenceDispositionV1,
    ):
        return _blocked_projection(
            "H-S52-D valve-candidate disposition resolution required"
        )

    source_rows = tuple(product_search_duties.rows or ())
    if not source_rows:
        return _blocked_projection("H-S49-A point duty rows required")

    consequence_by_id = _rows_by_id_v1(
        tuple(consequence_evidence.rows or ()),
        source="H-S52-C",
    )
    disposition_by_id = _rows_by_id_v1(
        tuple(disposition_resolution.rows or ()),
        source="H-S52-D",
    )
    if isinstance(consequence_by_id, str):
        return _blocked_projection(consequence_by_id)
    if isinstance(disposition_by_id, str):
        return _blocked_projection(disposition_by_id)

    rows = tuple(
        _resolve_row_v1(
            source_row,
            consequence_by_id.get(
                _stable_text_v1(source_row.balancing_point_id)
            ),
            disposition_by_id.get(
                _stable_text_v1(source_row.balancing_point_id)
            ),
        )
        for source_row in source_rows
    )
    upstream = tuple(
        f"H-S49-A: {value}"
        for value in tuple(product_search_duties.blockers or ())
    ) + tuple(
        f"H-S52-C: {value}"
        for value in tuple(consequence_evidence.blockers or ())
    ) + tuple(
        f"H-S52-D: {value}"
        for value in tuple(disposition_resolution.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream, *row_blockers))
    ready = (
        bool(product_search_duties.ready)
        and bool(consequence_evidence.ready)
        and bool(disposition_resolution.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not ready and not blockers:
        blockers = (
            "Upstream product-search or catalogue-candidate evidence "
            "is not ready",
        )

    available = sum(1 for row in rows if row.envelope_available)
    pending = sum(
        1
        for row in rows
        if row.envelope_state_id == DETAILED_VALVE_DESIGN_DUTY_PENDING
    )
    revision = sum(
        1 for row in rows if row.valve_candidate_revision_required
    )
    return BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1(
        ready=ready,
        status=(
            f"Ready — {available} approved detailed valve-design "
            f"envelope(s); {pending} pending; "
            f"{revision} requiring catalogue-candidate revision"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(source_row, consequence_row, disposition_row):
    point_id = _stable_text_v1(source_row.balancing_point_id)
    common = dict(
        balancing_point_id=point_id,
        point_scope=_stable_text_v1(
            getattr(source_row, "point_scope", "")
        ),
        point_role=_stable_text_v1(
            getattr(source_row, "point_role", "")
        ),
        label=_stable_text_v1(getattr(source_row, "label", "")),
        topology=_stable_text_v1(
            getattr(source_row, "topology", "")
        ),
        governed_route_ids=tuple(
            _stable_text_v1(value)
            for value in tuple(
                getattr(source_row, "governed_route_ids", ()) or ()
            )
            if _stable_text_v1(value)
        ),
        point_flow_kg_s=_finite_v1(
            getattr(source_row, "point_flow_kg_s", None)
        ),
        required_kv=_finite_v1(
            getattr(source_row, "required_kv", None)
        ),
        design_valve_dp_pa=_finite_v1(
            getattr(source_row, "design_valve_dp_pa", None)
        ),
        design_authority=_finite_v1(
            getattr(source_row, "design_authority", None)
        ),
    )

    if not bool(
        getattr(source_row, "product_search_required", False)
    ):
        return (
            BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
                **common,
                ready=bool(getattr(source_row, "ready", False)),
                envelope_state_id=(
                    NO_DETAILED_VALVE_DESIGN_DUTY_REQUIRED
                ),
                status=(
                    "No detailed valve-design duty required — "
                    "no valve duty"
                ),
            )
        )

    if consequence_row is None or disposition_row is None:
        return _unavailable_row_v1(
            common,
            "Current H-S52-C consequence and H-S52-D disposition "
            "rows required",
        )

    revision = bool(
        getattr(
            disposition_row,
            "valve_candidate_revision_required",
            False,
        )
    )
    approved = bool(
        getattr(
            disposition_row,
            "approved_for_later_valve_design",
            False,
        )
    )
    current_kv = _finite_v1(
        getattr(consequence_row, "current_kv_m3_h", None)
    )
    identity = dict(
        catalog_id=_stable_text_v1(
            getattr(consequence_row, "catalog_id", "")
        ),
        valve_ref=_stable_text_v1(
            getattr(consequence_row, "valve_ref", "")
        ),
        current_kv_m3_h=current_kv,
    )

    if revision:
        return (
            BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
                **common,
                **identity,
                ready=bool(getattr(disposition_row, "ready", False)),
                envelope_state_id=(
                    DETAILED_VALVE_DESIGN_DUTY_REVISION_REQUIRED
                ),
                detailed_valve_design_required=True,
                valve_candidate_revision_required=True,
                status=(
                    "Catalogue valve-candidate revision required — "
                    "detailed valve-design envelope withheld"
                ),
            )
        )

    consequence_available = bool(
        getattr(consequence_row, "consequence_available", False)
    ) and (
        getattr(consequence_row, "consequence_state_id", "")
        == ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE
    )
    if not approved:
        return (
            BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
                **common,
                **identity,
                ready=(
                    bool(getattr(consequence_row, "ready", False))
                    and bool(getattr(disposition_row, "ready", False))
                ),
                envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_PENDING,
                detailed_valve_design_required=True,
                status=(
                    "Manual detailed valve-design approval pending"
                    if consequence_available
                    else "Accepted catalogue-candidate consequence pending"
                ),
            )
        )

    evidence = dict(
        current_kv_m3_h=_positive_finite_v1(
            getattr(consequence_row, "current_kv_m3_h", None)
        ),
        flow_m3_h=_positive_finite_v1(
            getattr(consequence_row, "flow_m3_h", None)
        ),
        controlled_circuit_dp_pa=_positive_finite_v1(
            getattr(consequence_row, "controlled_circuit_dp_pa", None)
        ),
        implied_valve_dp_bar=_positive_finite_v1(
            getattr(consequence_row, "implied_valve_dp_bar", None)
        ),
        implied_valve_dp_pa=_positive_finite_v1(
            getattr(consequence_row, "implied_valve_dp_pa", None)
        ),
        implied_authority=_positive_finite_v1(
            getattr(consequence_row, "implied_authority", None)
        ),
    )
    catalogue = identity["catalog_id"]
    reference = identity["valve_ref"]
    missing = [name for name, value in evidence.items() if value is None]
    if not consequence_available:
        missing.append("accepted catalogue-candidate consequence")
    if not catalogue:
        missing.append("catalogue identity")
    if not reference:
        missing.append("valve reference")
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
            "Approved detailed valve-design evidence unavailable: "
            + ", ".join(missing),
            **identity,
        )

    return BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
        **common,
        catalog_id=catalogue,
        valve_ref=reference,
        **evidence,
        ready=True,
        envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
        detailed_valve_design_required=True,
        envelope_available=True,
        approved_for_later_valve_design=True,
        status=(
            "Approved catalogue valve-candidate design duty envelope "
            "available — detailed valve design not started"
        ),
    )


def _unavailable_row_v1(common: dict, blocker: str, **identity):
    return BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
        **common,
        **identity,
        ready=False,
        envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_UNAVAILABLE,
        detailed_valve_design_required=True,
        status="Blocked — detailed valve-design duty unavailable",
        blockers=(blocker,),
    )


def _rows_by_id_v1(rows: tuple, *, source: str):
    result = {}
    for row in rows:
        point_id = _stable_text_v1(
            getattr(row, "balancing_point_id", "")
        )
        if not point_id:
            return f"Every {source} row requires balancing_point_id"
        if point_id in result:
            return f"Duplicate {source} balancing_point_id: {point_id}"
        result[point_id] = row
    return result


def _stable_text_v1(value: object) -> str:
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
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(
    *blockers: str,
) -> BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
