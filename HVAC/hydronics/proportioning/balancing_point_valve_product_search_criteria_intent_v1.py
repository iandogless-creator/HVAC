# ======================================================================
# H-S49-B — Manual valve product-search criteria intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math

from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)


PRODUCT_SEARCH_CRITERIA_PENDING = "product_search_criteria_pending"
PRODUCT_SEARCH_CRITERIA_AVAILABLE = "product_search_criteria_available"
PRODUCT_SEARCH_CRITERIA_NOT_APPLICABLE = "product_search_criteria_not_applicable"
PRODUCT_SEARCH_CRITERIA_UNAVAILABLE = "product_search_criteria_unavailable"


@dataclass(frozen=True, slots=True)
class PointValveProductSearchCriteriaV1:
    balancing_point_id: str
    accepted_kvs_basis: float
    catalog_id: str
    kv_tolerance_percent: float = 0.0
    valve_ref_contains: str = ""
    note_contains: str = ""
    # H-S62-C — exact approved H-S49-A duty envelope reviewed.
    duty_envelope_fingerprint: str = ""


@dataclass(slots=True)
class BalancingPointValveProductSearchCriteriaIntentV1:
    """Persisted manual search criteria keyed by stable balancing-point ID."""

    schema: str = "balancing_point_valve_product_search_criteria_intent_v1"
    criteria_by_point_id: dict[str, PointValveProductSearchCriteriaV1] = field(
        default_factory=dict
    )

    def set_criteria(
        self,
        *,
        balancing_point_id: str,
        accepted_kvs_basis: float,
        catalog_id: str,
        kv_tolerance_percent: float = 0.0,
        valve_ref_contains: str = "",
        note_contains: str = "",
        duty_envelope_fingerprint: str = "",
    ) -> None:
        point_id = _stable_text_v1(balancing_point_id)
        kvs = _positive_finite_v1(accepted_kvs_basis)
        catalogue = _stable_text_v1(catalog_id)
        tolerance = _percentage_v1(kv_tolerance_percent)
        fingerprint = _stable_text_v1(duty_envelope_fingerprint)
        if not point_id:
            raise ValueError("balancing_point_id is required")
        if kvs is None:
            raise ValueError("accepted_kvs_basis must be positive and finite")
        if not catalogue:
            raise ValueError("catalog_id is required")
        if tolerance is None:
            raise ValueError("kv_tolerance_percent must be between 0 and 100")
        self.criteria_by_point_id[point_id] = PointValveProductSearchCriteriaV1(
            balancing_point_id=point_id,
            accepted_kvs_basis=kvs,
            catalog_id=catalogue,
            kv_tolerance_percent=tolerance,
            valve_ref_contains=_stable_text_v1(valve_ref_contains),
            note_contains=_stable_text_v1(note_contains),
            duty_envelope_fingerprint=fingerprint,
        )

    def clear_criteria(self, balancing_point_id: str) -> bool:
        point_id = _stable_text_v1(balancing_point_id)
        if not point_id:
            return False
        return self.criteria_by_point_id.pop(point_id, None) is not None

    def to_dict(self) -> dict:
        return balancing_point_valve_product_search_criteria_intent_to_dict_v1(
            self
        )

    @classmethod
    def from_dict(
        cls,
        data: dict | None,
    ) -> "BalancingPointValveProductSearchCriteriaIntentV1":
        return balancing_point_valve_product_search_criteria_intent_from_dict_v1(
            data
        )


@dataclass(frozen=True, slots=True)
class ResolvedPointValveProductSearchCriteriaRowV1:
    balancing_point_id: str = ""
    ready: bool = False
    criteria_state_id: str = ""
    criteria_available: bool = False
    accepted_kvs_basis: float | None = None
    catalog_id: str = ""
    kv_tolerance_percent: float | None = None
    valve_ref_contains: str = ""
    note_contains: str = ""
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedPointValveProductSearchCriteriaV1:
    schema: str = "resolved_point_valve_product_search_criteria_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[ResolvedPointValveProductSearchCriteriaRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic criteria created",
        "No product search executed",
        "No catalogue queried",
        "No product ranked or recommended",
        "No valve product selected",
        "No valve size, DN, connection or setting selected",
        "No hydraulic mutation",
        "No final balancing",
    )


def balancing_point_valve_product_search_criteria_intent_to_dict_v1(
    intent: BalancingPointValveProductSearchCriteriaIntentV1 | None,
) -> dict:
    source = intent or BalancingPointValveProductSearchCriteriaIntentV1()
    return {
        "schema": source.schema,
        "criteria_by_point_id": {
            point_id: {
                "balancing_point_id": item.balancing_point_id,
                "accepted_kvs_basis": float(item.accepted_kvs_basis),
                "catalog_id": item.catalog_id,
                "kv_tolerance_percent": float(item.kv_tolerance_percent),
                "valve_ref_contains": item.valve_ref_contains,
                "note_contains": item.note_contains,
                "duty_envelope_fingerprint": (
                    item.duty_envelope_fingerprint
                ),
            }
            for point_id, item in sorted(source.criteria_by_point_id.items())
        },
    }


def balancing_point_valve_product_search_criteria_intent_from_dict_v1(
    data: dict | None,
) -> BalancingPointValveProductSearchCriteriaIntentV1:
    intent = BalancingPointValveProductSearchCriteriaIntentV1()
    if not isinstance(data, dict):
        return intent
    entries = data.get("criteria_by_point_id", {})
    if not isinstance(entries, dict):
        return intent
    for raw_point_id, raw in entries.items():
        if not isinstance(raw, dict):
            continue
        try:
            intent.set_criteria(
                balancing_point_id=(
                    raw.get("balancing_point_id") or raw_point_id
                ),
                accepted_kvs_basis=raw.get("accepted_kvs_basis"),
                catalog_id=raw.get("catalog_id"),
                kv_tolerance_percent=raw.get("kv_tolerance_percent", 0.0),
                valve_ref_contains=raw.get("valve_ref_contains", ""),
                note_contains=raw.get("note_contains", ""),
                duty_envelope_fingerprint=raw.get(
                    "duty_envelope_fingerprint", ""
                ),
            )
        except ValueError:
            continue
    return intent


def resolve_balancing_point_valve_product_search_criteria_v1(
    intent: BalancingPointValveProductSearchCriteriaIntentV1 | None,
    duty_envelopes: BalancingPointValveProductSearchDutyEnvelopeV1 | None,
    *,
    tolerance: float = 1e-9,
    require_duty_envelope_fingerprint: bool = False,
) -> ResolvedPointValveProductSearchCriteriaV1:
    source = intent or BalancingPointValveProductSearchCriteriaIntentV1()
    if not isinstance(
        duty_envelopes,
        BalancingPointValveProductSearchDutyEnvelopeV1,
    ):
        return _blocked_resolution("H-S49-A duty envelopes required")
    if tolerance < 0.0:
        return _blocked_resolution("tolerance must be zero or greater")

    envelope_rows = tuple(duty_envelopes.rows or ())
    envelope_ids = {
        _stable_text_v1(row.balancing_point_id) for row in envelope_rows
    }
    blockers = [
        f"{point_id}: search criteria have no current H-S49-A point envelope"
        for point_id in sorted(source.criteria_by_point_id)
        if point_id not in envelope_ids
    ]
    rows = []
    for envelope in envelope_rows:
        point_id = _stable_text_v1(envelope.balancing_point_id)
        criteria = source.criteria_by_point_id.get(point_id)
        available = (
            bool(envelope.envelope_available)
            and bool(envelope.approved_for_product_search)
            and envelope.envelope_state_id == PRODUCT_SEARCH_ENVELOPE_AVAILABLE
        )
        if not available:
            if criteria is None:
                rows.append(ResolvedPointValveProductSearchCriteriaRowV1(
                    balancing_point_id=point_id,
                    ready=bool(envelope.ready),
                    criteria_state_id=PRODUCT_SEARCH_CRITERIA_NOT_APPLICABLE,
                    status="Product-search criteria dormant — no approved envelope",
                ))
            else:
                blocker = "Search criteria exist without a current approved envelope"
                blockers.append(f"{point_id}: {blocker}")
                rows.append(_blocked_row_v1(point_id, criteria, blocker))
            continue

        if criteria is None:
            rows.append(ResolvedPointValveProductSearchCriteriaRowV1(
                balancing_point_id=point_id,
                ready=True,
                criteria_state_id=PRODUCT_SEARCH_CRITERIA_PENDING,
                accepted_kvs_basis=envelope.accepted_kvs,
                status="Manual product-search criteria pending",
            ))
            continue

        current_kvs = _positive_finite_v1(envelope.accepted_kvs)
        if current_kvs is None or not math.isclose(
            criteria.accepted_kvs_basis,
            current_kvs,
            rel_tol=tolerance,
            abs_tol=tolerance,
        ):
            blocker = "Search criteria are stale for the current accepted Kvs"
            blockers.append(f"{point_id}: {blocker}")
            rows.append(_blocked_row_v1(point_id, criteria, blocker))
            continue

        current_fingerprint = (
            build_product_search_duty_envelope_fingerprint_v1(envelope)
        )
        fingerprint_blocker = ""
        if criteria.duty_envelope_fingerprint:
            if (
                not current_fingerprint
                or criteria.duty_envelope_fingerprint != current_fingerprint
            ):
                fingerprint_blocker = (
                    "Product-search criteria duty-envelope fingerprint does "
                    "not match current H-S49-A evidence"
                )
        elif require_duty_envelope_fingerprint:
            fingerprint_blocker = (
                "Product-search criteria predate exact post-resize duty "
                "envelope; fresh manual review required"
            )
        if fingerprint_blocker:
            blockers.append(f"{point_id}: {fingerprint_blocker}")
            rows.append(_blocked_row_v1(point_id, criteria, fingerprint_blocker))
            continue

        rows.append(ResolvedPointValveProductSearchCriteriaRowV1(
            balancing_point_id=point_id,
            ready=True,
            criteria_state_id=PRODUCT_SEARCH_CRITERIA_AVAILABLE,
            criteria_available=True,
            accepted_kvs_basis=criteria.accepted_kvs_basis,
            catalog_id=criteria.catalog_id,
            kv_tolerance_percent=criteria.kv_tolerance_percent,
            valve_ref_contains=criteria.valve_ref_contains,
            note_contains=criteria.note_contains,
            status="Manual product-search criteria available — search not executed",
        ))

    all_blockers = _unique_v1(
        (*tuple(duty_envelopes.blockers or ()), *tuple(blockers))
    )
    ready = bool(duty_envelopes.ready) and not all_blockers and all(
        row.ready for row in rows
    )
    return ResolvedPointValveProductSearchCriteriaV1(
        ready=ready,
        status=(
            "Ready — manual product-search criteria resolved; search not executed"
            if ready
            else "Blocked — " + "; ".join(all_blockers)
        ),
        blockers=all_blockers,
        rows=tuple(rows),
    )



def build_product_search_duty_envelope_fingerprint_v1(
    envelope: object,
) -> str:
    """Fingerprint the exact approved H-S49-A search-duty envelope.

    H-S62-C binds manual filters to the engineering duty they were applied
    against. Display labels and the filter values themselves are deliberately
    excluded from this upstream evidence identity.
    """

    point_id = _stable_text_v1(
        getattr(envelope, "balancing_point_id", "")
    )
    state_id = _stable_text_v1(
        getattr(envelope, "envelope_state_id", "")
    )
    if (
        not point_id
        or state_id != PRODUCT_SEARCH_ENVELOPE_AVAILABLE
        or not bool(getattr(envelope, "envelope_available", False))
        or not bool(getattr(envelope, "approved_for_product_search", False))
    ):
        return ""

    numeric_fields = (
        "point_flow_kg_s",
        "flow_m3_h",
        "required_kv",
        "accepted_kvs",
        "implied_valve_dp_bar",
        "implied_valve_dp_pa",
        "controlled_circuit_dp_pa",
        "implied_authority",
        "design_valve_dp_pa",
        "design_authority",
    )
    numbers: list[tuple[str, str]] = []
    for field_name in numeric_fields:
        value = _positive_finite_v1(getattr(envelope, field_name, None))
        if value is None:
            return ""
        numbers.append((field_name, float(value).hex()))

    text_fields = (
        "point_scope",
        "point_role",
        "topology",
        "kvs_series_id",
    )
    texts = tuple(
        (field_name, _stable_text_v1(getattr(envelope, field_name, "")))
        for field_name in text_fields
    )
    governed_routes = tuple(
        _stable_text_v1(value)
        for value in tuple(
            getattr(envelope, "governed_route_ids", ()) or ()
        )
    )
    payload = repr((
        ("balancing_point_id", point_id),
        ("envelope_state_id", state_id),
        *texts,
        *tuple(numbers),
        ("governed_route_ids", governed_routes),
    )).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _blocked_row_v1(point_id, criteria, blocker):
    return ResolvedPointValveProductSearchCriteriaRowV1(
        balancing_point_id=point_id,
        ready=False,
        criteria_state_id=PRODUCT_SEARCH_CRITERIA_UNAVAILABLE,
        accepted_kvs_basis=criteria.accepted_kvs_basis,
        catalog_id=criteria.catalog_id,
        kv_tolerance_percent=criteria.kv_tolerance_percent,
        valve_ref_contains=criteria.valve_ref_contains,
        note_contains=criteria.note_contains,
        status="Blocked — stale product-search criteria",
        blockers=(blocker,),
    )


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


def _blocked_resolution(*blockers: str):
    clean = _unique_v1(tuple(blockers))
    return ResolvedPointValveProductSearchCriteriaV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
