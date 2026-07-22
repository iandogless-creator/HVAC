# ======================================================================
# H-S48-D — Manual accepted-Kvs consequence disposition
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import math

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import (
    ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
    NO_ACCEPTED_KVS_CONSEQUENCE_REQUIRED,
    BalancingPointAcceptedKvsHydraulicConsequenceV1,
)


APPROVED_FOR_PRODUCT_SEARCH = "approved_for_product_search"
KVS_REVISION_REQUIRED = "kvs_revision_required"
VALID_DISPOSITIONS = frozenset({
    APPROVED_FOR_PRODUCT_SEARCH,
    KVS_REVISION_REQUIRED,
})


@dataclass(frozen=True, slots=True)
class PointAcceptedKvsConsequenceDispositionV1:
    balancing_point_id: str
    disposition: str
    accepted_kvs_basis: float


@dataclass(slots=True)
class BalancingPointAcceptedKvsConsequenceDispositionIntentV1:
    schema: str = "balancing_point_accepted_kvs_consequence_disposition_intent_v1"
    disposition_by_point_id: dict[
        str, PointAcceptedKvsConsequenceDispositionV1
    ] = field(default_factory=dict)

    def set_disposition(
        self,
        *,
        balancing_point_id: str,
        disposition: str,
        accepted_kvs_basis: float,
    ) -> None:
        point_id = _stable_id_v1(balancing_point_id)
        decision = _stable_id_v1(disposition)
        kvs = _positive_finite_v1(accepted_kvs_basis)
        if not point_id:
            raise ValueError("balancing_point_id is required")
        if decision not in VALID_DISPOSITIONS:
            raise ValueError("Unknown accepted-Kvs consequence disposition")
        if kvs is None:
            raise ValueError("accepted_kvs_basis must be positive and finite")
        self.disposition_by_point_id[point_id] = (
            PointAcceptedKvsConsequenceDispositionV1(
                balancing_point_id=point_id,
                disposition=decision,
                accepted_kvs_basis=kvs,
            )
        )

    def clear_disposition(self, balancing_point_id: str) -> bool:
        point_id = _stable_id_v1(balancing_point_id)
        if not point_id:
            return False
        return self.disposition_by_point_id.pop(point_id, None) is not None

    def to_dict(self) -> dict:
        return balancing_point_accepted_kvs_consequence_disposition_intent_to_dict_v1(
            self
        )

    @classmethod
    def from_dict(
        cls,
        data: dict | None,
    ) -> "BalancingPointAcceptedKvsConsequenceDispositionIntentV1":
        return balancing_point_accepted_kvs_consequence_disposition_intent_from_dict_v1(
            data
        )


@dataclass(frozen=True, slots=True)
class ResolvedPointAcceptedKvsConsequenceDispositionRowV1:
    balancing_point_id: str = ""
    ready: bool = False
    disposition: str = ""
    accepted_kvs_basis: float | None = None
    approved_for_product_search: bool = False
    kvs_revision_required: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedPointAcceptedKvsConsequenceDispositionV1:
    schema: str = "resolved_point_accepted_kvs_consequence_disposition_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[ResolvedPointAcceptedKvsConsequenceDispositionRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic consequence approval",
        "No Kvs mutation",
        "No hydraulic mutation",
        "No product search started",
        "No valve product selected",
        "No valve size or setting selected",
        "No manufacturer catalogue used",
        "No final balancing",
    )


def balancing_point_accepted_kvs_consequence_disposition_intent_to_dict_v1(
    intent: BalancingPointAcceptedKvsConsequenceDispositionIntentV1 | None,
) -> dict:
    source = intent or BalancingPointAcceptedKvsConsequenceDispositionIntentV1()
    return {
        "schema": source.schema,
        "disposition_by_point_id": {
            point_id: {
                "balancing_point_id": entry.balancing_point_id,
                "disposition": entry.disposition,
                "accepted_kvs_basis": float(entry.accepted_kvs_basis),
            }
            for point_id, entry in sorted(
                source.disposition_by_point_id.items()
            )
        },
    }


def balancing_point_accepted_kvs_consequence_disposition_intent_from_dict_v1(
    data: dict | None,
) -> BalancingPointAcceptedKvsConsequenceDispositionIntentV1:
    intent = BalancingPointAcceptedKvsConsequenceDispositionIntentV1()
    if not isinstance(data, dict):
        return intent
    raw_entries = data.get("disposition_by_point_id", {})
    if not isinstance(raw_entries, dict):
        return intent
    for raw_point_id, raw_entry in raw_entries.items():
        if not isinstance(raw_entry, dict):
            continue
        point_id = _stable_id_v1(
            raw_entry.get("balancing_point_id") or raw_point_id
        )
        disposition = _stable_id_v1(raw_entry.get("disposition"))
        kvs = _positive_finite_v1(raw_entry.get("accepted_kvs_basis"))
        if not point_id or disposition not in VALID_DISPOSITIONS or kvs is None:
            continue
        intent.disposition_by_point_id[point_id] = (
            PointAcceptedKvsConsequenceDispositionV1(
                balancing_point_id=point_id,
                disposition=disposition,
                accepted_kvs_basis=kvs,
            )
        )
    return intent


def resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
    intent: BalancingPointAcceptedKvsConsequenceDispositionIntentV1 | None,
    consequence_evidence: BalancingPointAcceptedKvsHydraulicConsequenceV1 | None,
    *,
    tolerance: float = 1e-9,
) -> ResolvedPointAcceptedKvsConsequenceDispositionV1:
    source = intent or BalancingPointAcceptedKvsConsequenceDispositionIntentV1()
    if consequence_evidence is None:
        return _blocked_resolution("H-S48-C consequence evidence required")
    if not isinstance(
        consequence_evidence,
        BalancingPointAcceptedKvsHydraulicConsequenceV1,
    ):
        return _blocked_resolution(
            "consequence_evidence is not "
            "BalancingPointAcceptedKvsHydraulicConsequenceV1"
        )
    if tolerance < 0.0:
        return _blocked_resolution("tolerance must be zero or greater")

    evidence_rows = tuple(consequence_evidence.rows or ())
    evidence_ids = {
        _stable_id_v1(row.balancing_point_id) for row in evidence_rows
    }
    blockers: list[str] = [
        f"{point_id}: disposition has no current H-S48-C point evidence"
        for point_id in sorted(source.disposition_by_point_id)
        if point_id not in evidence_ids
    ]
    rows: list[ResolvedPointAcceptedKvsConsequenceDispositionRowV1] = []

    for evidence_row in evidence_rows:
        point_id = _stable_id_v1(evidence_row.balancing_point_id)
        entry = source.disposition_by_point_id.get(point_id)

        if (
            evidence_row.consequence_state_id
            == NO_ACCEPTED_KVS_CONSEQUENCE_REQUIRED
        ):
            if entry is not None:
                blocker = "Disposition exists where no consequence is required"
                blockers.append(f"{point_id}: {blocker}")
                rows.append(_blocked_row(point_id, entry, blocker))
            else:
                rows.append(
                    ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
                        balancing_point_id=point_id,
                        ready=bool(evidence_row.ready),
                        status="No consequence disposition required — no valve duty",
                    )
                )
            continue

        if entry is None:
            rows.append(
                ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
                    balancing_point_id=point_id,
                    ready=bool(evidence_row.ready),
                    status=(
                        "Manual consequence disposition pending"
                        if evidence_row.consequence_available
                        else "Accepted Kvs consequence pending"
                    ),
                )
            )
            continue

        current_kvs = _positive_finite_v1(evidence_row.accepted_kvs)
        if (
            evidence_row.consequence_state_id
            != ACCEPTED_KVS_CONSEQUENCE_AVAILABLE
            or not evidence_row.consequence_available
            or current_kvs is None
            or not math.isclose(
                entry.accepted_kvs_basis,
                current_kvs,
                rel_tol=tolerance,
                abs_tol=tolerance,
            )
        ):
            blocker = "Disposition is stale for the current accepted Kvs consequence"
            blockers.append(f"{point_id}: {blocker}")
            rows.append(_blocked_row(point_id, entry, blocker))
            continue

        approved = entry.disposition == APPROVED_FOR_PRODUCT_SEARCH
        revision = entry.disposition == KVS_REVISION_REQUIRED
        rows.append(
            ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
                balancing_point_id=point_id,
                ready=True,
                disposition=entry.disposition,
                accepted_kvs_basis=entry.accepted_kvs_basis,
                approved_for_product_search=approved,
                kvs_revision_required=revision,
                status=(
                    "Approved for later product search — search not started"
                    if approved
                    else "Kvs revision required — no automatic change"
                ),
            )
        )

    all_blockers = _unique_v1(
        (*tuple(consequence_evidence.blockers or ()), *tuple(blockers))
    )
    ready = bool(consequence_evidence.ready) and not all_blockers and all(
        row.ready for row in rows
    )
    return ResolvedPointAcceptedKvsConsequenceDispositionV1(
        ready=ready,
        status=(
            "Ready — manual accepted-Kvs consequence dispositions resolved"
            if ready
            else "Blocked — " + "; ".join(all_blockers)
        ),
        blockers=all_blockers,
        rows=tuple(rows),
    )


def _blocked_row(point_id, entry, blocker):
    return ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
        balancing_point_id=point_id,
        ready=False,
        disposition=entry.disposition,
        accepted_kvs_basis=entry.accepted_kvs_basis,
        status="Blocked — stale consequence disposition",
        blockers=(blocker,),
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


def _blocked_resolution(
    *blockers: str,
) -> ResolvedPointAcceptedKvsConsequenceDispositionV1:
    clean = _unique_v1(tuple(blockers))
    return ResolvedPointAcceptedKvsConsequenceDispositionV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
