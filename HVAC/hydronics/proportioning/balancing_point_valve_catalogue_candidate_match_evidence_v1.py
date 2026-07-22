# ======================================================================
# H-S50-A — Valve catalogue candidate-match evidence
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_valve_product_search_criteria_intent_v1 import (
    PRODUCT_SEARCH_CRITERIA_AVAILABLE,
    ResolvedPointValveProductSearchCriteriaV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)
from HVAC.hydronics_v3.dto.valve_catalog_dto import ValveCatalogDTO


CATALOGUE_MATCH_NOT_APPLICABLE = "catalogue_match_not_applicable"
CATALOGUE_MATCH_CRITERIA_PENDING = "catalogue_match_criteria_pending"
CATALOGUE_MATCH_EVIDENCE_AVAILABLE = "catalogue_match_evidence_available"
CATALOGUE_MATCH_EVIDENCE_UNAVAILABLE = "catalogue_match_evidence_unavailable"


@dataclass(frozen=True, slots=True)
class ValveCatalogueCandidateMatchV1:
    catalog_id: str
    valve_ref: str
    kv_m3_h: float
    kv_deviation_percent: float
    note: str = ""


@dataclass(frozen=True, slots=True)
class BalancingPointValveCatalogueCandidateMatchRowV1:
    balancing_point_id: str = ""
    ready: bool = False
    match_state_id: str = ""
    match_evidence_available: bool = False
    accepted_kvs_basis: float | None = None
    catalog_id: str = ""
    kv_tolerance_percent: float | None = None
    valve_ref_contains: str = ""
    note_contains: str = ""
    candidates: tuple[ValveCatalogueCandidateMatchV1, ...] = ()
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BalancingPointValveCatalogueCandidateMatchEvidenceV1:
    schema: str = "balancing_point_valve_catalogue_candidate_match_evidence_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointValveCatalogueCandidateMatchRowV1, ...] = ()
    catalog_id: str = ""
    exclusions: tuple[str, ...] = (
        "No automatic product-search criteria created",
        "No catalogue source inferred or persisted",
        "No candidate ranking or recommendation",
        "No valve product selected",
        "No valve size, DN, connection or setting selected",
        "No hydraulic mutation",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Matches preserve supplied catalogue order and are evidence only."
    )


def build_balancing_point_valve_catalogue_candidate_match_evidence_v1(
    duty_envelopes: BalancingPointValveProductSearchDutyEnvelopeV1 | None,
    criteria_resolution: ResolvedPointValveProductSearchCriteriaV1 | None,
    valve_catalog: ValveCatalogDTO | None,
) -> BalancingPointValveCatalogueCandidateMatchEvidenceV1:
    if not isinstance(
        duty_envelopes,
        BalancingPointValveProductSearchDutyEnvelopeV1,
    ):
        return _blocked_projection("H-S49-A duty envelopes required")
    if not isinstance(
        criteria_resolution,
        ResolvedPointValveProductSearchCriteriaV1,
    ):
        return _blocked_projection("H-S49-B criteria resolution required")
    if not isinstance(valve_catalog, ValveCatalogDTO):
        return _blocked_projection("Supplied ValveCatalogDTO required")

    catalog_id = _stable_text_v1(valve_catalog.catalog_id)
    if not catalog_id:
        return _blocked_projection("ValveCatalogDTO catalog_id required")
    options = tuple(valve_catalog.kv_options or ())
    catalogue_blockers = _validate_catalogue_v1(options)
    if catalogue_blockers:
        return _blocked_projection(*catalogue_blockers, catalog_id=catalog_id)

    criteria_by_id = _rows_by_id_v1(
        tuple(criteria_resolution.rows or ()),
        source="H-S49-B",
    )
    if isinstance(criteria_by_id, str):
        return _blocked_projection(criteria_by_id, catalog_id=catalog_id)

    rows = tuple(
        _resolve_row_v1(
            envelope,
            criteria_by_id.get(_stable_text_v1(envelope.balancing_point_id)),
            catalog_id,
            options,
        )
        for envelope in tuple(duty_envelopes.rows or ())
    )
    upstream = tuple(
        f"H-S49-A: {value}"
        for value in tuple(duty_envelopes.blockers or ())
    ) + tuple(
        f"H-S49-B: {value}"
        for value in tuple(criteria_resolution.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream, *row_blockers))
    ready = (
        bool(duty_envelopes.ready)
        and bool(criteria_resolution.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    matched_points = sum(1 for row in rows if row.candidates)
    matched_options = sum(len(row.candidates) for row in rows)
    return BalancingPointValveCatalogueCandidateMatchEvidenceV1(
        ready=ready,
        status=(
            f"Ready — {matched_options} candidate match(es) across "
            f"{matched_points} point(s); no ranking or selection"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
        catalog_id=catalog_id,
    )


def _resolve_row_v1(envelope, criteria, catalog_id: str, options: tuple):
    point_id = _stable_text_v1(envelope.balancing_point_id)
    approved = (
        bool(envelope.envelope_available)
        and bool(envelope.approved_for_product_search)
        and envelope.envelope_state_id == PRODUCT_SEARCH_ENVELOPE_AVAILABLE
    )
    if not approved:
        return BalancingPointValveCatalogueCandidateMatchRowV1(
            balancing_point_id=point_id,
            ready=bool(envelope.ready),
            match_state_id=CATALOGUE_MATCH_NOT_APPLICABLE,
            status="Catalogue matching dormant — no approved envelope",
        )
    if criteria is None or not bool(criteria.criteria_available):
        return BalancingPointValveCatalogueCandidateMatchRowV1(
            balancing_point_id=point_id,
            ready=bool(getattr(criteria, "ready", True)),
            match_state_id=CATALOGUE_MATCH_CRITERIA_PENDING,
            accepted_kvs_basis=envelope.accepted_kvs,
            status="Manual product-search criteria pending",
        )
    if criteria.criteria_state_id != PRODUCT_SEARCH_CRITERIA_AVAILABLE:
        return _blocked_row_v1(
            point_id,
            criteria,
            "Current H-S49-B criteria evidence unavailable",
        )
    if _stable_text_v1(criteria.catalog_id) != catalog_id:
        return _blocked_row_v1(
            point_id,
            criteria,
            "Supplied catalogue does not match manual catalog_id",
        )

    accepted_kvs = _positive_finite_v1(criteria.accepted_kvs_basis)
    tolerance = _percentage_v1(criteria.kv_tolerance_percent)
    if accepted_kvs is None or tolerance is None:
        return _blocked_row_v1(
            point_id,
            criteria,
            "Positive accepted Kvs and valid tolerance required",
        )
    ref_filter = _stable_text_v1(criteria.valve_ref_contains).casefold()
    note_filter = _stable_text_v1(criteria.note_contains).casefold()
    matches = []
    for option in options:
        valve_ref = _stable_text_v1(option.valve_ref)
        note = _stable_text_v1(option.note)
        kv = float(option.kv_m3_h)
        deviation = abs(kv - accepted_kvs) / accepted_kvs * 100.0
        if deviation > tolerance + 1e-12:
            continue
        if ref_filter and ref_filter not in valve_ref.casefold():
            continue
        if note_filter and note_filter not in note.casefold():
            continue
        matches.append(ValveCatalogueCandidateMatchV1(
            catalog_id=catalog_id,
            valve_ref=valve_ref,
            kv_m3_h=kv,
            kv_deviation_percent=deviation,
            note=note,
        ))

    candidates = tuple(matches)
    return BalancingPointValveCatalogueCandidateMatchRowV1(
        balancing_point_id=point_id,
        ready=True,
        match_state_id=CATALOGUE_MATCH_EVIDENCE_AVAILABLE,
        match_evidence_available=True,
        accepted_kvs_basis=accepted_kvs,
        catalog_id=catalog_id,
        kv_tolerance_percent=tolerance,
        valve_ref_contains=criteria.valve_ref_contains,
        note_contains=criteria.note_contains,
        candidates=candidates,
        status=(
            f"{len(candidates)} catalogue candidate match(es) — "
            "supplied order retained; no ranking or selection"
            if candidates
            else "No catalogue candidates match the manual criteria"
        ),
    )


def _validate_catalogue_v1(options: tuple) -> tuple[str, ...]:
    blockers = []
    seen = set()
    for option in options:
        ref = _stable_text_v1(getattr(option, "valve_ref", ""))
        kv = _positive_finite_v1(getattr(option, "kv_m3_h", None))
        if not ref:
            blockers.append("Every catalogue option requires valve_ref")
        elif ref in seen:
            blockers.append(f"Duplicate catalogue valve_ref: {ref}")
        else:
            seen.add(ref)
        if kv is None:
            blockers.append(f"Positive finite Kv required for {ref or 'option'}")
    return _unique_v1(tuple(blockers))


def _blocked_row_v1(point_id, criteria, blocker):
    return BalancingPointValveCatalogueCandidateMatchRowV1(
        balancing_point_id=point_id,
        ready=False,
        match_state_id=CATALOGUE_MATCH_EVIDENCE_UNAVAILABLE,
        accepted_kvs_basis=getattr(criteria, "accepted_kvs_basis", None),
        catalog_id=_stable_text_v1(getattr(criteria, "catalog_id", "")),
        kv_tolerance_percent=getattr(criteria, "kv_tolerance_percent", None),
        valve_ref_contains=_stable_text_v1(
            getattr(criteria, "valve_ref_contains", "")
        ),
        note_contains=_stable_text_v1(getattr(criteria, "note_contains", "")),
        status="Blocked — catalogue candidate-match evidence unavailable",
        blockers=(blocker,),
    )


def _rows_by_id_v1(rows: tuple, *, source: str):
    result = {}
    for row in rows:
        point_id = _stable_text_v1(getattr(row, "balancing_point_id", ""))
        if not point_id:
            return f"Every {source} row requires balancing_point_id"
        if point_id in result:
            return f"Duplicate {source} balancing_point_id: {point_id}"
        result[point_id] = row
    return result


def _stable_text_v1(value: object) -> str:
    return str(value or "").strip()


def _positive_finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0.0 else None


def _percentage_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and 0.0 <= number <= 100.0 else None


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result = []
    for value in values:
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(
    *blockers: str,
    catalog_id: str = "",
) -> BalancingPointValveCatalogueCandidateMatchEvidenceV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointValveCatalogueCandidateMatchEvidenceV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        catalog_id=catalog_id,
    )
