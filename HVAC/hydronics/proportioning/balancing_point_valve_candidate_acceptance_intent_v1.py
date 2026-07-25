# ======================================================================
# H-S52-A — Manual point valve-candidate acceptance intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field

from HVAC.hydronics.proportioning.balancing_point_valve_catalogue_candidate_match_evidence_v1 import (
    BalancingPointValveCatalogueCandidateMatchEvidenceV1,
)


@dataclass(frozen=True, slots=True)
class PointValveCandidateAcceptanceV1:
    """One persisted manual candidate identity at a balancing point."""

    balancing_point_id: str
    catalog_id: str
    valve_ref: str


@dataclass(slots=True)
class BalancingPointValveCandidateAcceptanceIntentV1:
    """
    Persisted manual valve-candidate intent keyed by stable point identity.

    Catalogue identity and valve reference are stored, but current catalogue
    Kv/note evidence is not duplicated into ProjectState.  This is not a
    committed valve product, valve setting or final balancing result.
    """

    schema: str = "balancing_point_valve_candidate_acceptance_intent_v1"
    accepted_by_point_id: dict[
        str,
        PointValveCandidateAcceptanceV1,
    ] = field(default_factory=dict)

    def accept_candidate(
        self,
        *,
        balancing_point_id: str,
        catalog_id: str,
        valve_ref: str,
    ) -> None:
        point_id = _stable_text_v1(balancing_point_id)
        catalogue = _stable_text_v1(catalog_id)
        reference = _stable_text_v1(valve_ref)
        if not point_id:
            raise ValueError("balancing_point_id is required")
        if not catalogue:
            raise ValueError("catalog_id is required")
        if not reference:
            raise ValueError("valve_ref is required")
        self.accepted_by_point_id[point_id] = (
            PointValveCandidateAcceptanceV1(
                balancing_point_id=point_id,
                catalog_id=catalogue,
                valve_ref=reference,
            )
        )

    def clear_candidate(self, balancing_point_id: str) -> bool:
        point_id = _stable_text_v1(balancing_point_id)
        if not point_id:
            return False
        return self.accepted_by_point_id.pop(point_id, None) is not None

    def to_dict(self) -> dict:
        return balancing_point_valve_candidate_acceptance_intent_to_dict_v1(
            self
        )

    @classmethod
    def from_dict(
        cls,
        data: dict | None,
    ) -> "BalancingPointValveCandidateAcceptanceIntentV1":
        return (
            balancing_point_valve_candidate_acceptance_intent_from_dict_v1(
                data
            )
        )


@dataclass(frozen=True, slots=True)
class ResolvedPointValveCandidateAcceptanceRowV1:
    balancing_point_id: str = ""
    accepted: bool = False
    catalog_id: str = ""
    valve_ref: str = ""
    current_kv_m3_h: float | None = None
    current_note: str = ""
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedPointValveCandidateAcceptanceV1:
    schema: str = "resolved_point_valve_candidate_acceptance_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[ResolvedPointValveCandidateAcceptanceRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic candidate acceptance",
        "No candidate ranking or recommendation",
        "No committed valve product selection",
        "No valve size, DN, connection or setting selected",
        "No product-derived hydraulic mutation",
        "No final balancing",
        "No pump selection or pipe resizing",
    )
    note: str = (
        "Manual identity is resolved against current H-S50-A evidence; "
        "catalogue Kv and notes remain read-only current evidence."
    )


def balancing_point_valve_candidate_acceptance_intent_to_dict_v1(
    intent: BalancingPointValveCandidateAcceptanceIntentV1 | None,
) -> dict:
    source = intent or BalancingPointValveCandidateAcceptanceIntentV1()
    return {
        "schema": source.schema,
        "accepted_by_point_id": {
            point_id: {
                "balancing_point_id": entry.balancing_point_id,
                "catalog_id": entry.catalog_id,
                "valve_ref": entry.valve_ref,
            }
            for point_id, entry in sorted(
                source.accepted_by_point_id.items()
            )
        },
    }


def balancing_point_valve_candidate_acceptance_intent_from_dict_v1(
    data: dict | None,
) -> BalancingPointValveCandidateAcceptanceIntentV1:
    intent = BalancingPointValveCandidateAcceptanceIntentV1()
    if not isinstance(data, dict):
        return intent
    raw_entries = data.get("accepted_by_point_id", {})
    if not isinstance(raw_entries, dict):
        return intent
    for raw_point_id, raw_entry in raw_entries.items():
        if not isinstance(raw_entry, dict):
            continue
        point_id = _stable_text_v1(
            raw_entry.get("balancing_point_id") or raw_point_id
        )
        catalogue = _stable_text_v1(raw_entry.get("catalog_id"))
        reference = _stable_text_v1(raw_entry.get("valve_ref"))
        if not point_id or not catalogue or not reference:
            continue
        intent.accepted_by_point_id[point_id] = (
            PointValveCandidateAcceptanceV1(
                balancing_point_id=point_id,
                catalog_id=catalogue,
                valve_ref=reference,
            )
        )
    return intent


def resolve_balancing_point_valve_candidate_acceptance_v1(
    intent: BalancingPointValveCandidateAcceptanceIntentV1 | None,
    candidate_evidence: (
        BalancingPointValveCatalogueCandidateMatchEvidenceV1 | None
    ),
) -> ResolvedPointValveCandidateAcceptanceV1:
    """Resolve manual identities against current H-S50-A candidates."""

    source = intent or BalancingPointValveCandidateAcceptanceIntentV1()
    if not isinstance(
        candidate_evidence,
        BalancingPointValveCatalogueCandidateMatchEvidenceV1,
    ):
        return _blocked_resolution(
            "H-S50-A catalogue candidate-match evidence required"
        )

    evidence_rows = tuple(candidate_evidence.rows or ())
    evidence_ids = {
        _stable_text_v1(getattr(row, "balancing_point_id", ""))
        for row in evidence_rows
        if _stable_text_v1(getattr(row, "balancing_point_id", ""))
    }
    blockers: list[str] = [
        f"{point_id}: accepted valve candidate has no current point evidence"
        for point_id in sorted(source.accepted_by_point_id)
        if point_id not in evidence_ids
    ]
    rows: list[ResolvedPointValveCandidateAcceptanceRowV1] = []

    for evidence_row in evidence_rows:
        point_id = _stable_text_v1(evidence_row.balancing_point_id)
        entry = source.accepted_by_point_id.get(point_id)
        candidates = tuple(evidence_row.candidates or ())

        if entry is None:
            rows.append(
                ResolvedPointValveCandidateAcceptanceRowV1(
                    balancing_point_id=point_id,
                    accepted=False,
                    catalog_id=_stable_text_v1(
                        getattr(evidence_row, "catalog_id", "")
                    ),
                    status=(
                        "Manual valve-candidate acceptance pending"
                        if candidates
                        else "No current catalogue candidate available"
                    ),
                )
            )
            continue

        if entry.catalog_id != _stable_text_v1(
            getattr(evidence_row, "catalog_id", "")
        ):
            blocker = (
                "Accepted catalogue identity does not match current "
                "point evidence"
            )
            blockers.append(f"{point_id}: {blocker}")
            rows.append(
                _stale_row_v1(entry, blocker)
            )
            continue

        matching = next(
            (
                candidate
                for candidate in candidates
                if (
                    _stable_text_v1(candidate.catalog_id)
                    == entry.catalog_id
                    and _stable_text_v1(candidate.valve_ref)
                    == entry.valve_ref
                )
            ),
            None,
        )
        if matching is None:
            blocker = (
                "Accepted valve reference is not a current H-S50-A "
                "candidate for this point"
            )
            blockers.append(f"{point_id}: {blocker}")
            rows.append(_stale_row_v1(entry, blocker))
            continue

        rows.append(
            ResolvedPointValveCandidateAcceptanceRowV1(
                balancing_point_id=point_id,
                accepted=True,
                catalog_id=entry.catalog_id,
                valve_ref=entry.valve_ref,
                current_kv_m3_h=float(matching.kv_m3_h),
                current_note=_stable_text_v1(
                    getattr(matching, "note", "")
                ),
                status=(
                    "Manual valve-candidate identity resolved — "
                    "no product hydraulics committed"
                ),
            )
        )

    upstream = tuple(
        f"H-S50-A: {value}"
        for value in tuple(candidate_evidence.blockers or ())
    )
    all_blockers = _unique_v1((*upstream, *tuple(blockers)))
    ready = bool(candidate_evidence.ready) and not all_blockers
    return ResolvedPointValveCandidateAcceptanceV1(
        ready=ready,
        status=(
            "Ready — manual valve-candidate intent resolved"
            if ready
            else "Blocked — " + "; ".join(all_blockers)
        ),
        blockers=all_blockers,
        rows=tuple(rows),
    )


def _stale_row_v1(
    entry: PointValveCandidateAcceptanceV1,
    blocker: str,
) -> ResolvedPointValveCandidateAcceptanceRowV1:
    return ResolvedPointValveCandidateAcceptanceRowV1(
        balancing_point_id=entry.balancing_point_id,
        accepted=False,
        catalog_id=entry.catalog_id,
        valve_ref=entry.valve_ref,
        status="Blocked — stale manual valve-candidate acceptance",
        blockers=(blocker,),
    )


def _stable_text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_resolution(
    *blockers: str,
) -> ResolvedPointValveCandidateAcceptanceV1:
    clean = _unique_v1(tuple(blockers))
    return ResolvedPointValveCandidateAcceptanceV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
