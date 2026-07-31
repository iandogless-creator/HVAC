# ======================================================================
# H-S48-A — Manual point Kvs candidate acceptance intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math

from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_evidence_v1 import (
    GENERIC_PREFERRED_KVS_SERIES_ID_V1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_utilisation_evidence_v1 import (
    BalancingPointKvsCandidateUtilisationEvidenceV1,
)


@dataclass(frozen=True, slots=True)
class PointKvsCandidateAcceptanceV1:
    balancing_point_id: str
    accepted_kvs: float
    kvs_series_id: str = GENERIC_PREFERRED_KVS_SERIES_ID_V1
    # H-S62-A — exact H-S47-C point-duty evidence accepted manually.
    duty_fingerprint: str = ""


@dataclass(slots=True)
class BalancingPointKvsCandidateAcceptanceIntentV1:
    """
    Persisted manual acceptance keyed by stable balancing-point ID.

    This stores user intent only. It does not select a valve product, size,
    setting or manufacturer, alter hydraulics, or commit final balancing.
    """

    schema: str = "balancing_point_kvs_candidate_acceptance_intent_v1"
    accepted_by_point_id: dict[str, PointKvsCandidateAcceptanceV1] = field(
        default_factory=dict
    )

    def accept_candidate(
        self,
        *,
        balancing_point_id: str,
        accepted_kvs: float,
        kvs_series_id: str = GENERIC_PREFERRED_KVS_SERIES_ID_V1,
        duty_fingerprint: str = "",
    ) -> None:
        point_id = _stable_id_v1(balancing_point_id)
        kvs = _positive_finite_v1(accepted_kvs)
        series_id = _stable_id_v1(kvs_series_id)
        fingerprint = _stable_id_v1(duty_fingerprint)
        if not point_id:
            raise ValueError("balancing_point_id is required")
        if kvs is None:
            raise ValueError("accepted_kvs must be positive and finite")
        if not series_id:
            raise ValueError("kvs_series_id is required")
        self.accepted_by_point_id[point_id] = PointKvsCandidateAcceptanceV1(
            balancing_point_id=point_id,
            accepted_kvs=kvs,
            kvs_series_id=series_id,
            duty_fingerprint=fingerprint,
        )

    def clear_candidate(self, balancing_point_id: str) -> bool:
        point_id = _stable_id_v1(balancing_point_id)
        if not point_id:
            return False
        return self.accepted_by_point_id.pop(point_id, None) is not None

    def to_dict(self) -> dict:
        return balancing_point_kvs_candidate_acceptance_intent_to_dict_v1(self)

    @classmethod
    def from_dict(
        cls,
        data: dict | None,
    ) -> "BalancingPointKvsCandidateAcceptanceIntentV1":
        return balancing_point_kvs_candidate_acceptance_intent_from_dict_v1(
            data
        )


@dataclass(frozen=True, slots=True)
class ResolvedPointKvsCandidateAcceptanceRowV1:
    balancing_point_id: str = ""
    accepted: bool = False
    accepted_kvs: float | None = None
    kvs_series_id: str = ""
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedPointKvsCandidateAcceptanceV1:
    schema: str = "resolved_point_kvs_candidate_acceptance_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[ResolvedPointKvsCandidateAcceptanceRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic Kvs acceptance",
        "No valve product selected",
        "No valve size or setting selected",
        "No manufacturer catalogue used",
        "No hydraulic mutation",
        "No final balancing",
    )


def balancing_point_kvs_candidate_acceptance_intent_to_dict_v1(
    intent: BalancingPointKvsCandidateAcceptanceIntentV1 | None,
) -> dict:
    source = intent or BalancingPointKvsCandidateAcceptanceIntentV1()
    return {
        "schema": source.schema,
        "accepted_by_point_id": {
            point_id: {
                "balancing_point_id": entry.balancing_point_id,
                "accepted_kvs": float(entry.accepted_kvs),
                "kvs_series_id": entry.kvs_series_id,
                "duty_fingerprint": entry.duty_fingerprint,
            }
            for point_id, entry in sorted(
                source.accepted_by_point_id.items()
            )
        },
    }


def balancing_point_kvs_candidate_acceptance_intent_from_dict_v1(
    data: dict | None,
) -> BalancingPointKvsCandidateAcceptanceIntentV1:
    intent = BalancingPointKvsCandidateAcceptanceIntentV1()
    if not isinstance(data, dict):
        return intent
    raw_entries = data.get("accepted_by_point_id", {})
    if not isinstance(raw_entries, dict):
        return intent
    for raw_point_id, raw_entry in raw_entries.items():
        if not isinstance(raw_entry, dict):
            continue
        point_id = _stable_id_v1(
            raw_entry.get("balancing_point_id") or raw_point_id
        )
        kvs = _positive_finite_v1(raw_entry.get("accepted_kvs"))
        series_id = _stable_id_v1(raw_entry.get("kvs_series_id"))
        fingerprint = _stable_id_v1(
            raw_entry.get("duty_fingerprint")
        )
        if not point_id or kvs is None or not series_id:
            continue
        intent.accepted_by_point_id[point_id] = PointKvsCandidateAcceptanceV1(
            balancing_point_id=point_id,
            accepted_kvs=kvs,
            kvs_series_id=series_id,
            duty_fingerprint=fingerprint,
        )
    return intent


def resolve_balancing_point_kvs_candidate_acceptance_v1(
    intent: BalancingPointKvsCandidateAcceptanceIntentV1 | None,
    utilisation_evidence: (
        BalancingPointKvsCandidateUtilisationEvidenceV1 | None
    ),
    *,
    tolerance: float = 1e-9,
    require_duty_fingerprint: bool = False,
) -> ResolvedPointKvsCandidateAcceptanceV1:
    """Resolve persisted intent against current H-S47-C candidate evidence."""

    source = intent or BalancingPointKvsCandidateAcceptanceIntentV1()
    if utilisation_evidence is None:
        return _blocked_resolution("H-S47-C utilisation evidence required")
    if not isinstance(
        utilisation_evidence,
        BalancingPointKvsCandidateUtilisationEvidenceV1,
    ):
        return _blocked_resolution(
            "utilisation_evidence is not "
            "BalancingPointKvsCandidateUtilisationEvidenceV1"
        )
    if tolerance < 0.0:
        return _blocked_resolution("tolerance must be zero or greater")

    evidence_rows = tuple(utilisation_evidence.rows or ())
    evidence_ids = {
        _stable_id_v1(getattr(row, "balancing_point_id", ""))
        for row in evidence_rows
    }
    orphan_ids = sorted(
        point_id
        for point_id in source.accepted_by_point_id
        if point_id not in evidence_ids
    )
    blockers: list[str] = [
        f"{point_id}: accepted Kvs has no current point evidence"
        for point_id in orphan_ids
    ]
    rows: list[ResolvedPointKvsCandidateAcceptanceRowV1] = []

    for evidence_row in evidence_rows:
        point_id = _stable_id_v1(evidence_row.balancing_point_id)
        entry = source.accepted_by_point_id.get(point_id)
        candidates = tuple(evidence_row.kvs_candidates or ())

        if entry is None:
            rows.append(
                ResolvedPointKvsCandidateAcceptanceRowV1(
                    balancing_point_id=point_id,
                    accepted=False,
                    status=(
                        "Not applicable — no Kvs candidates required"
                        if not candidates
                        else "Manual Kvs candidate acceptance pending"
                    ),
                )
            )
            continue

        if not candidates:
            blocker = "Accepted Kvs exists where no candidate is required"
            blockers.append(f"{point_id}: {blocker}")
            rows.append(
                ResolvedPointKvsCandidateAcceptanceRowV1(
                    balancing_point_id=point_id,
                    accepted=False,
                    accepted_kvs=entry.accepted_kvs,
                    kvs_series_id=entry.kvs_series_id,
                    status="Blocked — stale manual Kvs acceptance",
                    blockers=(blocker,),
                )
            )
            continue

        matching = next(
            (
                value for value in candidates
                if math.isclose(
                    float(value),
                    entry.accepted_kvs,
                    rel_tol=tolerance,
                    abs_tol=tolerance,
                )
            ),
            None,
        )
        if (
            matching is None
            or entry.kvs_series_id != evidence_row.kvs_series_id
        ):
            blocker = "Accepted Kvs is not a current H-S47-C candidate"
            blockers.append(f"{point_id}: {blocker}")
            rows.append(
                ResolvedPointKvsCandidateAcceptanceRowV1(
                    balancing_point_id=point_id,
                    accepted=False,
                    accepted_kvs=entry.accepted_kvs,
                    kvs_series_id=entry.kvs_series_id,
                    status="Blocked — stale manual Kvs acceptance",
                    blockers=(blocker,),
                )
            )
            continue

        current_fingerprint = (
            build_balancing_point_kvs_acceptance_duty_fingerprint_v1(
                evidence_row
            )
        )
        fingerprint_blocker = ""
        if entry.duty_fingerprint:
            if (
                not current_fingerprint
                or entry.duty_fingerprint != current_fingerprint
            ):
                fingerprint_blocker = (
                    "Accepted Kvs duty fingerprint does not match "
                    "current H-S47-C point duty"
                )
        elif require_duty_fingerprint:
            fingerprint_blocker = (
                "Accepted Kvs predates exact point-duty evidence; "
                "fresh manual review required"
            )
        if fingerprint_blocker:
            blockers.append(f"{point_id}: {fingerprint_blocker}")
            rows.append(
                ResolvedPointKvsCandidateAcceptanceRowV1(
                    balancing_point_id=point_id,
                    accepted=False,
                    accepted_kvs=entry.accepted_kvs,
                    kvs_series_id=entry.kvs_series_id,
                    status="Blocked — stale manual Kvs acceptance",
                    blockers=(fingerprint_blocker,),
                )
            )
            continue

        rows.append(
            ResolvedPointKvsCandidateAcceptanceRowV1(
                balancing_point_id=point_id,
                accepted=True,
                accepted_kvs=float(matching),
                kvs_series_id=entry.kvs_series_id,
                status="Manual generic Kvs candidate accepted",
            )
        )

    all_blockers = _unique_v1(
        (*tuple(utilisation_evidence.blockers or ()), *tuple(blockers))
    )
    ready = bool(utilisation_evidence.ready) and not all_blockers
    return ResolvedPointKvsCandidateAcceptanceV1(
        ready=ready,
        status=(
            "Ready — manual Kvs acceptance intent resolved"
            if ready
            else "Blocked — " + "; ".join(all_blockers)
        ),
        blockers=all_blockers,
        rows=tuple(rows),
    )



def build_balancing_point_kvs_acceptance_duty_fingerprint_v1(
    evidence_row: object,
) -> str:
    """Fingerprint the exact current point duty behind manual Kvs review.

    Derived values are deliberately retained alongside their authoritative
    inputs. This makes any material/size-driven change to the point duty,
    required Kv or controlled-circuit consequence visible as stale evidence.
    """

    point_id = _stable_id_v1(
        getattr(evidence_row, "balancing_point_id", "")
    )
    if not point_id:
        return ""

    numeric_fields = (
        "point_flow_kg_s",
        "design_valve_dp_pa",
        "controlled_circuit_dp_pa",
        "flow_m3_h",
        "required_kv",
        "fluid_density_kg_m3",
    )
    numbers: list[tuple[str, str]] = []
    for field_name in numeric_fields:
        value = _positive_finite_v1(getattr(evidence_row, field_name, None))
        if value is None:
            return ""
        numbers.append((field_name, float(value).hex()))

    text_fields = (
        "point_scope",
        "point_role",
        "topology",
        "fluid_density_basis_id",
        "kvs_series_id",
    )
    texts = tuple(
        (field_name, _stable_id_v1(getattr(evidence_row, field_name, "")))
        for field_name in text_fields
    )

    route_fields = ("governed_route_ids", "downstream_route_ids")
    routes = tuple(
        (
            field_name,
            tuple(
                _stable_id_v1(value)
                for value in tuple(
                    getattr(evidence_row, field_name, ()) or ()
                )
            ),
        )
        for field_name in route_fields
    )
    payload = repr((
        ("balancing_point_id", point_id),
        *texts,
        *tuple(numbers),
        *routes,
    )).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

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


def _blocked_resolution(*blockers: str) -> ResolvedPointKvsCandidateAcceptanceV1:
    clean = _unique_v1(tuple(blockers))
    return ResolvedPointKvsCandidateAcceptanceV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
    )
