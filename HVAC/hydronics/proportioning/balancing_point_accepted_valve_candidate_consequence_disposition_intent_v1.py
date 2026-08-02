# ======================================================================
# H-S52-D — Manual accepted valve-candidate consequence disposition
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math

from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_hydraulic_consequence_v1 import (
    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE,
    NO_ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_REQUIRED,
    BalancingPointAcceptedValveCandidateHydraulicConsequenceV1,
)


APPROVED_FOR_LATER_VALVE_DESIGN = "approved_for_later_valve_design"
VALVE_CANDIDATE_REVISION_REQUIRED = (
    "valve_candidate_revision_required"
)
VALID_DISPOSITIONS = frozenset({
    APPROVED_FOR_LATER_VALVE_DESIGN,
    VALVE_CANDIDATE_REVISION_REQUIRED,
})


@dataclass(frozen=True, slots=True)
class PointAcceptedValveCandidateConsequenceDispositionV1:
    """One manual decision bound to current catalogue consequence basis."""

    balancing_point_id: str
    disposition: str
    catalog_id_basis: str
    valve_ref_basis: str
    current_kv_m3_h_basis: float
    # H-S62-E — exact H-S52-C hydraulic consequence reviewed manually.
    consequence_fingerprint: str = ""


@dataclass(slots=True)
class BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1:
    """Persist point decisions without persisting calculated hydraulics."""

    schema: str = (
        "balancing_point_accepted_valve_candidate_"
        "consequence_disposition_intent_v1"
    )
    disposition_by_point_id: dict[
        str,
        PointAcceptedValveCandidateConsequenceDispositionV1,
    ] = field(default_factory=dict)

    def set_disposition(
        self,
        *,
        balancing_point_id: str,
        disposition: str,
        catalog_id_basis: str,
        valve_ref_basis: str,
        current_kv_m3_h_basis: float,
        consequence_fingerprint: str = "",
    ) -> None:
        point_id = _stable_text_v1(balancing_point_id)
        decision = _stable_text_v1(disposition)
        catalogue = _stable_text_v1(catalog_id_basis)
        reference = _stable_text_v1(valve_ref_basis)
        kv = _positive_finite_v1(current_kv_m3_h_basis)
        fingerprint = _stable_text_v1(consequence_fingerprint)
        if not point_id:
            raise ValueError("balancing_point_id is required")
        if decision not in VALID_DISPOSITIONS:
            raise ValueError(
                "Unknown accepted valve-candidate consequence disposition"
            )
        if not catalogue:
            raise ValueError("catalog_id_basis is required")
        if not reference:
            raise ValueError("valve_ref_basis is required")
        if kv is None:
            raise ValueError(
                "current_kv_m3_h_basis must be positive and finite"
            )
        self.disposition_by_point_id[point_id] = (
            PointAcceptedValveCandidateConsequenceDispositionV1(
                balancing_point_id=point_id,
                disposition=decision,
                catalog_id_basis=catalogue,
                valve_ref_basis=reference,
                current_kv_m3_h_basis=kv,
                consequence_fingerprint=fingerprint,
            )
        )

    def clear_disposition(self, balancing_point_id: str) -> bool:
        point_id = _stable_text_v1(balancing_point_id)
        if not point_id:
            return False
        return self.disposition_by_point_id.pop(point_id, None) is not None

    def to_dict(self) -> dict:
        return balancing_point_accepted_valve_candidate_consequence_disposition_intent_to_dict_v1(
            self
        )

    @classmethod
    def from_dict(
        cls,
        data: dict | None,
    ) -> (
        "BalancingPointAcceptedValveCandidate"
        "ConsequenceDispositionIntentV1"
    ):
        return balancing_point_accepted_valve_candidate_consequence_disposition_intent_from_dict_v1(
            data
        )


@dataclass(frozen=True, slots=True)
class ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1:
    balancing_point_id: str = ""
    ready: bool = False
    disposition: str = ""
    catalog_id_basis: str = ""
    valve_ref_basis: str = ""
    current_kv_m3_h_basis: float | None = None
    approved_for_later_valve_design: bool = False
    valve_candidate_revision_required: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedPointAcceptedValveCandidateConsequenceDispositionV1:
    schema: str = (
        "resolved_point_accepted_valve_candidate_"
        "consequence_disposition_v1"
    )
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[
        ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1,
        ...,
    ] = ()
    exclusions: tuple[str, ...] = (
        "No automatic consequence approval",
        "No automatic valve-candidate acceptance",
        "No catalogue identity or valve reference mutation",
        "No product-derived hydraulic mutation",
        "No design valve pressure drop or authority changed",
        "No committed valve product selection",
        "No valve size, DN, connection or setting selected",
        "No pump selection",
        "No pipe resizing",
        "No final balancing",
    )


def balancing_point_accepted_valve_candidate_consequence_disposition_intent_to_dict_v1(
    intent: (
        BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1
        | None
    ),
) -> dict:
    source = (
        intent
        or BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1()
    )
    return {
        "schema": source.schema,
        "disposition_by_point_id": {
            point_id: {
                "balancing_point_id": entry.balancing_point_id,
                "disposition": entry.disposition,
                "catalog_id_basis": entry.catalog_id_basis,
                "valve_ref_basis": entry.valve_ref_basis,
                "current_kv_m3_h_basis": float(
                    entry.current_kv_m3_h_basis
                ),
                "consequence_fingerprint": entry.consequence_fingerprint,
            }
            for point_id, entry in sorted(
                source.disposition_by_point_id.items()
            )
        },
    }


def balancing_point_accepted_valve_candidate_consequence_disposition_intent_from_dict_v1(
    data: dict | None,
) -> BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1:
    intent = (
        BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1()
    )
    if not isinstance(data, dict):
        return intent
    raw_entries = data.get("disposition_by_point_id", {})
    if not isinstance(raw_entries, dict):
        return intent
    for raw_point_id, raw_entry in raw_entries.items():
        if not isinstance(raw_entry, dict):
            continue
        point_id = _stable_text_v1(
            raw_entry.get("balancing_point_id") or raw_point_id
        )
        disposition = _stable_text_v1(raw_entry.get("disposition"))
        catalogue = _stable_text_v1(
            raw_entry.get("catalog_id_basis")
        )
        reference = _stable_text_v1(
            raw_entry.get("valve_ref_basis")
        )
        kv = _positive_finite_v1(
            raw_entry.get("current_kv_m3_h_basis")
        )
        fingerprint = _stable_text_v1(
            raw_entry.get("consequence_fingerprint")
        )
        if (
            not point_id
            or disposition not in VALID_DISPOSITIONS
            or not catalogue
            or not reference
            or kv is None
        ):
            continue
        intent.disposition_by_point_id[point_id] = (
            PointAcceptedValveCandidateConsequenceDispositionV1(
                balancing_point_id=point_id,
                disposition=disposition,
                catalog_id_basis=catalogue,
                valve_ref_basis=reference,
                current_kv_m3_h_basis=kv,
                consequence_fingerprint=fingerprint,
            )
        )
    return intent


def resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
    intent: (
        BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1
        | None
    ),
    consequence_evidence: (
        BalancingPointAcceptedValveCandidateHydraulicConsequenceV1 | None
    ),
    *,
    tolerance: float = 1e-9,
    require_consequence_fingerprint: bool = False,
) -> ResolvedPointAcceptedValveCandidateConsequenceDispositionV1:
    source = (
        intent
        or BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1()
    )
    if not isinstance(
        consequence_evidence,
        BalancingPointAcceptedValveCandidateHydraulicConsequenceV1,
    ):
        return _blocked_resolution(
            "H-S52-C accepted valve-candidate consequence evidence required"
        )
    if tolerance < 0.0:
        return _blocked_resolution(
            "tolerance must be zero or greater"
        )

    evidence_rows = tuple(consequence_evidence.rows or ())
    evidence_ids = {
        _stable_text_v1(row.balancing_point_id)
        for row in evidence_rows
    }
    blockers: list[str] = [
        f"{point_id}: disposition has no current H-S52-C point evidence"
        for point_id in sorted(source.disposition_by_point_id)
        if point_id not in evidence_ids
    ]
    rows: list[
        ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1
    ] = []

    for evidence_row in evidence_rows:
        point_id = _stable_text_v1(evidence_row.balancing_point_id)
        entry = source.disposition_by_point_id.get(point_id)

        if (
            evidence_row.consequence_state_id
            == NO_ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_REQUIRED
        ):
            if entry is not None:
                blocker = (
                    "Disposition exists where no consequence is required"
                )
                blockers.append(f"{point_id}: {blocker}")
                rows.append(_blocked_row_v1(point_id, entry, blocker))
            else:
                rows.append(
                    ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1(
                        balancing_point_id=point_id,
                        ready=bool(evidence_row.ready),
                        status=(
                            "No consequence disposition required — "
                            "no valve duty"
                        ),
                    )
                )
            continue

        if entry is None:
            rows.append(
                ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1(
                    balancing_point_id=point_id,
                    ready=bool(evidence_row.ready),
                    status=(
                        "Manual catalogue-candidate consequence "
                        "disposition pending"
                        if evidence_row.consequence_available
                        else "Accepted catalogue-candidate consequence pending"
                    ),
                )
            )
            continue

        current_catalogue = _stable_text_v1(evidence_row.catalog_id)
        current_reference = _stable_text_v1(evidence_row.valve_ref)
        current_kv = _positive_finite_v1(
            evidence_row.current_kv_m3_h
        )
        if (
            evidence_row.consequence_state_id
            != ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE
            or not evidence_row.consequence_available
            or current_kv is None
            or entry.catalog_id_basis != current_catalogue
            or entry.valve_ref_basis != current_reference
            or not math.isclose(
                entry.current_kv_m3_h_basis,
                current_kv,
                rel_tol=tolerance,
                abs_tol=tolerance,
            )
        ):
            blocker = (
                "Disposition is stale for the current accepted "
                "catalogue valve-candidate consequence"
            )
            blockers.append(f"{point_id}: {blocker}")
            rows.append(_blocked_row_v1(point_id, entry, blocker))
            continue

        current_fingerprint = (
            build_accepted_valve_candidate_consequence_fingerprint_v1(
                evidence_row
            )
        )
        fingerprint_blocker = ""
        if entry.consequence_fingerprint:
            if (
                not current_fingerprint
                or entry.consequence_fingerprint != current_fingerprint
            ):
                fingerprint_blocker = (
                    "Catalogue-candidate consequence disposition "
                    "fingerprint does not match current H-S52-C evidence"
                )
        elif require_consequence_fingerprint:
            fingerprint_blocker = (
                "Catalogue-candidate consequence disposition predates "
                "exact post-resize evidence; fresh manual review required"
            )
        if fingerprint_blocker:
            blockers.append(f"{point_id}: {fingerprint_blocker}")
            rows.append(
                _blocked_row_v1(point_id, entry, fingerprint_blocker)
            )
            continue

        approved = (
            entry.disposition == APPROVED_FOR_LATER_VALVE_DESIGN
        )
        revision = (
            entry.disposition == VALVE_CANDIDATE_REVISION_REQUIRED
        )
        rows.append(
            ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1(
                balancing_point_id=point_id,
                ready=True,
                disposition=entry.disposition,
                catalog_id_basis=entry.catalog_id_basis,
                valve_ref_basis=entry.valve_ref_basis,
                current_kv_m3_h_basis=entry.current_kv_m3_h_basis,
                approved_for_later_valve_design=approved,
                valve_candidate_revision_required=revision,
                status=(
                    "Approved for later detailed valve design — "
                    "no valve size or setting committed"
                    if approved
                    else (
                        "Catalogue valve-candidate revision required — "
                        "no automatic change"
                    )
                ),
            )
        )

    all_blockers = _unique_v1(
        (*tuple(consequence_evidence.blockers or ()), *tuple(blockers))
    )
    ready = bool(consequence_evidence.ready) and not all_blockers and all(
        row.ready for row in rows
    )
    return ResolvedPointAcceptedValveCandidateConsequenceDispositionV1(
        ready=ready,
        status=(
            "Ready — manual accepted catalogue valve-candidate "
            "consequence dispositions resolved"
            if ready
            else "Blocked — " + "; ".join(all_blockers)
        ),
        blockers=all_blockers,
        rows=tuple(rows),
    )


def build_accepted_valve_candidate_consequence_fingerprint_v1(
    evidence_row: object,
) -> str:
    """Fingerprint the exact H-S52-C consequence reviewed manually.

    Catalogue identity and Kv alone are insufficient: the same product must
    be reviewed again when flow or controlled-circuit duty changes.
    """

    point_id = _stable_text_v1(
        getattr(evidence_row, "balancing_point_id", "")
    )
    catalogue = _stable_text_v1(
        getattr(evidence_row, "catalog_id", "")
    )
    reference = _stable_text_v1(
        getattr(evidence_row, "valve_ref", "")
    )
    consequence_state_id = _stable_text_v1(
        getattr(evidence_row, "consequence_state_id", "")
    )
    formula = _stable_text_v1(getattr(evidence_row, "formula", ""))
    if (
        not point_id
        or not catalogue
        or not reference
        or consequence_state_id
        != ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE
        or not bool(getattr(evidence_row, "consequence_available", False))
        or not bool(getattr(evidence_row, "accepted", False))
        or not formula
    ):
        return ""

    numeric_fields = (
        "current_kv_m3_h",
        "flow_m3_h",
        "controlled_circuit_dp_pa",
        "implied_valve_dp_bar",
        "implied_valve_dp_pa",
        "implied_authority",
    )
    numbers: list[tuple[str, str]] = []
    for field_name in numeric_fields:
        value = _positive_finite_v1(
            getattr(evidence_row, field_name, None)
        )
        if value is None:
            return ""
        numbers.append((field_name, float(value).hex()))

    payload = repr((
        ("balancing_point_id", point_id),
        ("consequence_state_id", consequence_state_id),
        ("catalog_id", catalogue),
        ("valve_ref", reference),
        ("formula", formula),
        *tuple(numbers),
    )).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _blocked_row_v1(point_id, entry, blocker):
    return ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1(
        balancing_point_id=point_id,
        ready=False,
        disposition=entry.disposition,
        catalog_id_basis=entry.catalog_id_basis,
        valve_ref_basis=entry.valve_ref_basis,
        current_kv_m3_h_basis=entry.current_kv_m3_h_basis,
        status="Blocked — stale catalogue-candidate consequence disposition",
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
    if not math.isfinite(number) or number <= 0.0:
        return None
    return number


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_resolution(
    *blockers: str,
) -> ResolvedPointAcceptedValveCandidateConsequenceDispositionV1:
    clean = _unique_v1(tuple(blockers))
    return ResolvedPointAcceptedValveCandidateConsequenceDispositionV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
