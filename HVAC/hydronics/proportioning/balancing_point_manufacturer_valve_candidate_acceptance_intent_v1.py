# ======================================================================
# H-S64-F1 — Exact manufacturer valve-candidate acceptance intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math

from HVAC.hydronics.proportioning.balancing_point_manufacturer_valve_candidate_comparison_v1 import (
    MANUFACTURER_VALVE_COMPARISON_AVAILABLE,
    BalancingPointManufacturerValveCandidateComparisonV1,
)


@dataclass(frozen=True, slots=True)
class PointManufacturerValveCandidateAcceptanceV1:
    """One persisted manual product identity and its reviewed comparison."""

    balancing_point_id: str
    product_catalog_id: str
    product_catalog_revision: str
    valve_ref: str
    comparison_fingerprint: str


@dataclass(slots=True)
class BalancingPointManufacturerValveCandidateAcceptanceIntentV1:
    """Persisted manual acceptance keyed by stable balancing-point identity."""

    schema: str = (
        "balancing_point_manufacturer_valve_candidate_acceptance_intent_v1"
    )
    accepted_by_point_id: dict[
        str,
        PointManufacturerValveCandidateAcceptanceV1,
    ] = field(default_factory=dict)

    def accept_candidate(
        self,
        *,
        balancing_point_id: str,
        product_catalog_id: str,
        product_catalog_revision: str,
        valve_ref: str,
        comparison_fingerprint: str,
    ) -> None:
        point_id = _stable_text_v1(balancing_point_id)
        catalog_id = _stable_text_v1(product_catalog_id)
        revision = _stable_text_v1(product_catalog_revision)
        reference = _stable_text_v1(valve_ref)
        fingerprint = _fingerprint_text_v1(comparison_fingerprint)
        if not point_id:
            raise ValueError("balancing_point_id is required")
        if not catalog_id:
            raise ValueError("product_catalog_id is required")
        if not revision:
            raise ValueError("product_catalog_revision is required")
        if not reference:
            raise ValueError("valve_ref is required")
        if not fingerprint:
            raise ValueError("valid comparison_fingerprint is required")
        self.accepted_by_point_id[point_id] = (
            PointManufacturerValveCandidateAcceptanceV1(
                balancing_point_id=point_id,
                product_catalog_id=catalog_id,
                product_catalog_revision=revision,
                valve_ref=reference,
                comparison_fingerprint=fingerprint,
            )
        )

    def clear_candidate(self, balancing_point_id: str) -> bool:
        point_id = _stable_text_v1(balancing_point_id)
        if not point_id:
            return False
        return self.accepted_by_point_id.pop(point_id, None) is not None

    def to_dict(self) -> dict:
        return (
            balancing_point_manufacturer_valve_candidate_acceptance_intent_to_dict_v1(
                self
            )
        )

    @classmethod
    def from_dict(
        cls,
        data: dict | None,
    ) -> "BalancingPointManufacturerValveCandidateAcceptanceIntentV1":
        return (
            balancing_point_manufacturer_valve_candidate_acceptance_intent_from_dict_v1(
                data
            )
        )


@dataclass(frozen=True, slots=True)
class ResolvedPointManufacturerValveCandidateAcceptanceRowV1:
    balancing_point_id: str = ""
    accepted: bool = False
    product_catalog_id: str = ""
    product_catalog_revision: str = ""
    valve_ref: str = ""
    manufacturer_name: str = ""
    product_family: str = ""
    model_name: str = ""
    valve_type_id: str = ""
    nominal_dn: int | None = None
    connection_type: str = ""
    cost_band_id: str = ""
    product_kvs_m3_h: float | None = None
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedPointManufacturerValveCandidateAcceptanceV1:
    schema: str = (
        "resolved_point_manufacturer_valve_candidate_acceptance_v1"
    )
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[
        ResolvedPointManufacturerValveCandidateAcceptanceRowV1, ...
    ] = ()
    exclusions: tuple[str, ...] = (
        "No automatic candidate acceptance",
        "No premium, standard or budget ranking or recommendation",
        "No cost-band quality inference",
        "No valve preset or setting selected",
        "No product-derived hydraulic mutation",
        "No final balancing",
        "No pump selection or pipe resizing",
    )
    note: str = (
        "Persisted identity is resolved against the exact current H-S64-B "
        "comparison. Product details remain read-only current evidence."
    )


def balancing_point_manufacturer_valve_candidate_acceptance_intent_to_dict_v1(
    intent: BalancingPointManufacturerValveCandidateAcceptanceIntentV1 | None,
) -> dict:
    source = (
        intent
        or BalancingPointManufacturerValveCandidateAcceptanceIntentV1()
    )
    return {
        "schema": source.schema,
        "accepted_by_point_id": {
            point_id: {
                "balancing_point_id": entry.balancing_point_id,
                "product_catalog_id": entry.product_catalog_id,
                "product_catalog_revision": entry.product_catalog_revision,
                "valve_ref": entry.valve_ref,
                "comparison_fingerprint": entry.comparison_fingerprint,
            }
            for point_id, entry in sorted(
                source.accepted_by_point_id.items()
            )
        },
    }


def balancing_point_manufacturer_valve_candidate_acceptance_intent_from_dict_v1(
    data: dict | None,
) -> BalancingPointManufacturerValveCandidateAcceptanceIntentV1:
    intent = BalancingPointManufacturerValveCandidateAcceptanceIntentV1()
    if not isinstance(data, dict):
        return intent
    entries = data.get("accepted_by_point_id", {})
    if not isinstance(entries, dict):
        return intent
    for raw_point_id, raw_entry in entries.items():
        if not isinstance(raw_entry, dict):
            continue
        point_id = _stable_text_v1(
            raw_entry.get("balancing_point_id") or raw_point_id
        )
        catalog_id = _stable_text_v1(
            raw_entry.get("product_catalog_id")
        )
        revision = _stable_text_v1(
            raw_entry.get("product_catalog_revision")
        )
        reference = _stable_text_v1(raw_entry.get("valve_ref"))
        fingerprint = _fingerprint_text_v1(
            raw_entry.get("comparison_fingerprint")
        )
        if not all((point_id, catalog_id, revision, reference, fingerprint)):
            continue
        intent.accepted_by_point_id[point_id] = (
            PointManufacturerValveCandidateAcceptanceV1(
                balancing_point_id=point_id,
                product_catalog_id=catalog_id,
                product_catalog_revision=revision,
                valve_ref=reference,
                comparison_fingerprint=fingerprint,
            )
        )
    return intent


def resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
    intent: BalancingPointManufacturerValveCandidateAcceptanceIntentV1 | None,
    comparison: BalancingPointManufacturerValveCandidateComparisonV1 | None,
) -> ResolvedPointManufacturerValveCandidateAcceptanceV1:
    """Resolve manual identities against exact current H-S64-B evidence."""

    source = (
        intent
        or BalancingPointManufacturerValveCandidateAcceptanceIntentV1()
    )
    if not isinstance(
        comparison,
        BalancingPointManufacturerValveCandidateComparisonV1,
    ):
        return _blocked_v1(
            "H-S64-B manufacturer valve comparison evidence required"
        )

    comparison_rows = tuple(comparison.rows or ())
    evidence_ids = {
        _stable_text_v1(getattr(row, "balancing_point_id", ""))
        for row in comparison_rows
        if _stable_text_v1(getattr(row, "balancing_point_id", ""))
    }
    blockers: list[str] = [
        f"{point_id}: accepted manufacturer candidate has no current point evidence"
        for point_id in sorted(source.accepted_by_point_id)
        if point_id not in evidence_ids
    ]
    rows: list[ResolvedPointManufacturerValveCandidateAcceptanceRowV1] = []

    for comparison_row in comparison_rows:
        point_id = _stable_text_v1(
            getattr(comparison_row, "balancing_point_id", "")
        )
        entry = source.accepted_by_point_id.get(point_id)
        candidates = tuple(getattr(comparison_row, "candidates", ()) or ())
        if entry is None:
            rows.append(
                ResolvedPointManufacturerValveCandidateAcceptanceRowV1(
                    balancing_point_id=point_id,
                    product_catalog_id=_stable_text_v1(
                        getattr(comparison_row, "product_catalog_id", "")
                    ),
                    product_catalog_revision=_stable_text_v1(
                        getattr(
                            comparison_row,
                            "product_catalog_revision",
                            "",
                        )
                    ),
                    status=(
                        "Manual manufacturer valve-candidate acceptance pending"
                        if candidates
                        else "No current compatible manufacturer candidate available"
                    ),
                )
            )
            continue

        identity_blocker = _identity_blocker_v1(entry, comparison_row)
        if identity_blocker:
            blockers.append(f"{point_id}: {identity_blocker}")
            rows.append(_stale_row_v1(entry, identity_blocker))
            continue

        matching = next(
            (
                candidate
                for candidate in candidates
                if _stable_text_v1(getattr(candidate, "valve_ref", ""))
                == entry.valve_ref
            ),
            None,
        )
        if matching is None:
            blocker = (
                "Accepted valve reference is not a current H-S64-B "
                "candidate for this point"
            )
            blockers.append(f"{point_id}: {blocker}")
            rows.append(_stale_row_v1(entry, blocker))
            continue
        if not bool(getattr(matching, "compatible", False)):
            blocker = (
                "Accepted manufacturer valve candidate is no longer "
                "compatible with the approved duty"
            )
            blockers.append(f"{point_id}: {blocker}")
            rows.append(_stale_row_v1(entry, blocker))
            continue

        fingerprint = (
            build_manufacturer_valve_candidate_comparison_fingerprint_v1(
                comparison_row,
                matching,
            )
        )
        if not fingerprint or fingerprint != entry.comparison_fingerprint:
            blocker = (
                "Accepted manufacturer candidate comparison fingerprint "
                "does not match current H-S64-B evidence"
            )
            blockers.append(f"{point_id}: {blocker}")
            rows.append(_stale_row_v1(entry, blocker))
            continue

        rows.append(
            ResolvedPointManufacturerValveCandidateAcceptanceRowV1(
                balancing_point_id=point_id,
                accepted=True,
                product_catalog_id=entry.product_catalog_id,
                product_catalog_revision=entry.product_catalog_revision,
                valve_ref=entry.valve_ref,
                manufacturer_name=_stable_text_v1(
                    getattr(matching, "manufacturer_name", "")
                ),
                product_family=_stable_text_v1(
                    getattr(matching, "product_family", "")
                ),
                model_name=_stable_text_v1(
                    getattr(matching, "model_name", "")
                ),
                valve_type_id=_stable_text_v1(
                    getattr(matching, "valve_type_id", "")
                ),
                nominal_dn=getattr(matching, "nominal_dn", None),
                connection_type=_stable_text_v1(
                    getattr(matching, "connection_type", "")
                ),
                cost_band_id=_stable_text_v1(
                    getattr(matching, "cost_band_id", "")
                ),
                product_kvs_m3_h=getattr(
                    matching,
                    "product_kvs_m3_h",
                    None,
                ),
                status=(
                    "Manual manufacturer valve-candidate identity resolved "
                    "— no preset or hydraulics committed"
                ),
            )
        )

    upstream = tuple(
        f"H-S64-B: {value}"
        for value in tuple(comparison.blockers or ())
    )
    all_blockers = _unique_v1((*upstream, *tuple(blockers)))
    ready = bool(comparison.ready) and not all_blockers
    return ResolvedPointManufacturerValveCandidateAcceptanceV1(
        ready=ready,
        status=(
            "Ready — manual manufacturer valve-candidate intent resolved"
            if ready
            else "Blocked — " + "; ".join(all_blockers)
        ),
        blockers=all_blockers,
        rows=tuple(rows),
    )


def build_manufacturer_valve_candidate_comparison_fingerprint_v1(
    comparison_row: object,
    selected_candidate: object,
) -> str:
    """Fingerprint the exact selected candidate and complete review set."""

    point_id = _stable_text_v1(
        getattr(comparison_row, "balancing_point_id", "")
    )
    catalog_id = _stable_text_v1(
        getattr(comparison_row, "product_catalog_id", "")
    )
    revision = _stable_text_v1(
        getattr(comparison_row, "product_catalog_revision", "")
    )
    selected_ref = _stable_text_v1(
        getattr(selected_candidate, "valve_ref", "")
    )
    candidates = tuple(getattr(comparison_row, "candidates", ()) or ())
    selected_in_row = any(
        candidate == selected_candidate for candidate in candidates
    )
    if (
        not point_id
        or not catalog_id
        or not revision
        or not selected_ref
        or not selected_in_row
        or not bool(getattr(comparison_row, "ready", False))
        or not bool(getattr(comparison_row, "comparison_available", False))
        or _stable_text_v1(
            getattr(comparison_row, "comparison_state_id", "")
        ) != MANUFACTURER_VALVE_COMPARISON_AVAILABLE
        or not bool(getattr(selected_candidate, "compatible", False))
    ):
        return ""

    payload = repr((
        ("fingerprint_basis", "h_s64_f1_exact_h_s64_b_comparison_v1"),
        ("balancing_point_id", point_id),
        (
            "approved_basis_catalog_id",
            _stable_text_v1(
                getattr(comparison_row, "approved_basis_catalog_id", "")
            ),
        ),
        (
            "approved_basis_valve_ref",
            _stable_text_v1(
                getattr(comparison_row, "approved_basis_valve_ref", "")
            ),
        ),
        (
            "approved_current_kv_m3_h",
            _float_token_v1(
                getattr(comparison_row, "approved_current_kv_m3_h", None)
            ),
        ),
        (
            "required_kv",
            _float_token_v1(getattr(comparison_row, "required_kv", None)),
        ),
        ("product_catalog_id", catalog_id),
        ("product_catalog_revision", revision),
        ("selected_valve_ref", selected_ref),
        (
            "candidates_in_catalogue_order",
            tuple(_candidate_token_v1(candidate) for candidate in candidates),
        ),
    )).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _candidate_token_v1(candidate: object) -> tuple:
    return (
        _stable_text_v1(getattr(candidate, "valve_ref", "")),
        _stable_text_v1(getattr(candidate, "manufacturer_name", "")),
        _stable_text_v1(getattr(candidate, "product_family", "")),
        _stable_text_v1(getattr(candidate, "model_name", "")),
        _stable_text_v1(getattr(candidate, "valve_type_id", "")),
        getattr(candidate, "nominal_dn", None),
        _stable_text_v1(getattr(candidate, "connection_type", "")),
        _stable_text_v1(getattr(candidate, "cost_band_id", "")),
        _float_token_v1(
            getattr(candidate, "approved_current_kv_m3_h", None)
        ),
        _float_token_v1(getattr(candidate, "product_kvs_m3_h", None)),
        bool(getattr(candidate, "kvs_basis_matches", False)),
        _float_token_v1(getattr(candidate, "required_kv", None)),
        bool(getattr(candidate, "target_kv_bracketed", False)),
        _float_token_v1(getattr(candidate, "lower_setting_value", None)),
        _float_token_v1(getattr(candidate, "lower_setting_kv_m3_h", None)),
        _float_token_v1(getattr(candidate, "upper_setting_value", None)),
        _float_token_v1(getattr(candidate, "upper_setting_kv_m3_h", None)),
        bool(getattr(candidate, "compatible", False)),
    )


def _identity_blocker_v1(entry, comparison_row: object) -> str:
    if entry.product_catalog_id != _stable_text_v1(
        getattr(comparison_row, "product_catalog_id", "")
    ):
        return "Accepted product catalogue identity does not match current evidence"
    if entry.product_catalog_revision != _stable_text_v1(
        getattr(comparison_row, "product_catalog_revision", "")
    ):
        return "Accepted product catalogue revision does not match current evidence"
    return ""


def _stale_row_v1(
    entry: PointManufacturerValveCandidateAcceptanceV1,
    blocker: str,
) -> ResolvedPointManufacturerValveCandidateAcceptanceRowV1:
    return ResolvedPointManufacturerValveCandidateAcceptanceRowV1(
        balancing_point_id=entry.balancing_point_id,
        product_catalog_id=entry.product_catalog_id,
        product_catalog_revision=entry.product_catalog_revision,
        valve_ref=entry.valve_ref,
        status="Blocked — stale manual manufacturer valve-candidate acceptance",
        blockers=(blocker,),
    )


def _stable_text_v1(value: object) -> str:
    return str(value or "").strip()


def _fingerprint_text_v1(value: object) -> str:
    text = _stable_text_v1(value).casefold()
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        return ""
    return text


def _float_token_v1(value: object) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number.hex() if math.isfinite(number) else None


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_v1(
    *blockers: str,
) -> ResolvedPointManufacturerValveCandidateAcceptanceV1:
    clean = _unique_v1(tuple(blockers))
    return ResolvedPointManufacturerValveCandidateAcceptanceV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
