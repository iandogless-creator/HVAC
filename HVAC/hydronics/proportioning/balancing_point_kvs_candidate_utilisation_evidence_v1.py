# ======================================================================
# H-S47-C — Kvs candidate utilisation evidence
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_evidence_v1 import (
    GENERIC_KVS_CANDIDATES_AVAILABLE,
    NO_KVS_CANDIDATES_REQUIRED,
    BalancingPointKvsCandidateEvidenceRowV1,
    BalancingPointKvsCandidateEvidenceV1,
)


NO_KVS_UTILISATION_REQUIRED = "no_kvs_utilisation_required"
KVS_UTILISATION_EVIDENCE_AVAILABLE = "kvs_utilisation_evidence_available"
KVS_UTILISATION_EVIDENCE_UNAVAILABLE = "kvs_utilisation_evidence_unavailable"


@dataclass(frozen=True, slots=True)
class BalancingPointKvsCandidateUtilisationEvidenceRowV1(
    BalancingPointKvsCandidateEvidenceRowV1
):
    """H-S47-B candidates plus transparent full-open utilisation evidence."""

    kvs_utilisation_state_id: str = ""
    kvs_utilisation_available: bool = False
    kvs_utilisation_percentages: tuple[float, ...] = ()
    kvs_utilisation_summary: str = ""


@dataclass(frozen=True, slots=True)
class BalancingPointKvsCandidateUtilisationEvidenceV1:
    """
    H-S47-C candidate utilisation evidence.

    Utilisation is required Kv divided by generic candidate Kvs, expressed as
    a percentage. No suitability threshold, candidate acceptance, product,
    valve size, setting, persistence or final balancing authority is added.
    """

    schema: str = "balancing_point_kvs_candidate_utilisation_evidence_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[
        BalancingPointKvsCandidateUtilisationEvidenceRowV1, ...
    ] = ()
    exclusions: tuple[str, ...] = (
        "No suitability threshold applied",
        "No engineering approval granted",
        "No Kvs candidate accepted or selected",
        "No valve selected",
        "No valve size selected",
        "No valve product selected",
        "No manufacturer catalogue used",
        "No valve setting or preset selected",
        "No hydraulic recalculation",
        "No persistence mutation",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Kvs utilisation is comparison evidence only; manual engineering "
        "approval remains pending."
    )


def build_balancing_point_kvs_candidate_utilisation_evidence_v1(
    candidate_evidence: BalancingPointKvsCandidateEvidenceV1 | None,
) -> BalancingPointKvsCandidateUtilisationEvidenceV1:
    """Expose each H-S47-B operating fraction as a percentage."""

    if candidate_evidence is None:
        return _blocked_projection("H-S47-B Kvs candidate evidence required")
    if not isinstance(
        candidate_evidence,
        BalancingPointKvsCandidateEvidenceV1,
    ):
        return _blocked_projection(
            "candidate_evidence is not BalancingPointKvsCandidateEvidenceV1"
        )

    input_rows = tuple(candidate_evidence.rows or ())
    if not input_rows:
        return _blocked_projection(
            "H-S47-B Kvs candidate rows required",
            *tuple(candidate_evidence.blockers or ()),
        )

    rows = tuple(_resolve_row_v1(row) for row in input_rows)
    upstream_blockers = tuple(
        f"H-S47-B: {value}"
        for value in tuple(candidate_evidence.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = (
        bool(candidate_evidence.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not candidate_evidence.ready and not blockers:
        blockers = ("H-S47-B Kvs candidate evidence is not ready",)
        ready = False

    available_count = sum(
        1 for row in rows if row.kvs_utilisation_available
    )
    return BalancingPointKvsCandidateUtilisationEvidenceV1(
        ready=ready,
        status=(
            f"Ready — Kvs utilisation evidence available at "
            f"{available_count} point(s); no threshold or selection"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(
    input_row: BalancingPointKvsCandidateEvidenceRowV1,
) -> BalancingPointKvsCandidateUtilisationEvidenceRowV1:
    common = asdict(input_row)
    existing_blockers = _unique_v1(tuple(input_row.blockers or ()))

    if input_row.kvs_candidate_state_id == NO_KVS_CANDIDATES_REQUIRED:
        common.update(
            ready=bool(input_row.ready) and not existing_blockers,
            status="No Kvs utilisation required — no valve duty",
            blockers=existing_blockers,
            note=(
                str(input_row.note or "")
                + " H-S47-C utilisation evidence is dormant for this point."
            ).strip(),
        )
        return BalancingPointKvsCandidateUtilisationEvidenceRowV1(
            **common,
            kvs_utilisation_state_id=NO_KVS_UTILISATION_REQUIRED,
            kvs_utilisation_available=False,
        )

    candidates = tuple(input_row.kvs_candidates or ())
    fractions = tuple(input_row.kvs_operating_fractions or ())
    blockers = list(existing_blockers)
    if (
        not input_row.ready
        or not input_row.kvs_candidates_available
        or input_row.kvs_candidate_state_id
        != GENERIC_KVS_CANDIDATES_AVAILABLE
    ):
        blockers.append("H-S47-B Kvs candidate evidence unavailable")
    if not candidates:
        blockers.append("Generic Kvs candidates required")
    if len(candidates) != len(fractions):
        blockers.append("Kvs candidates and operating fractions must align")
    if any(_positive_finite_v1(value) is None for value in fractions):
        blockers.append("Positive finite Kvs operating fractions required")

    if blockers:
        clean = _unique_v1(tuple(blockers))
        common.update(
            ready=False,
            status="Blocked — Kvs utilisation evidence unavailable",
            blockers=clean,
            note="No Kvs utilisation evidence released.",
        )
        return BalancingPointKvsCandidateUtilisationEvidenceRowV1(
            **common,
            kvs_utilisation_state_id=KVS_UTILISATION_EVIDENCE_UNAVAILABLE,
            kvs_utilisation_available=False,
        )

    percentages = tuple(float(value) * 100.0 for value in fractions)
    summary = " | ".join(
        f"{_format_kvs_v1(kvs)}: {percentage:.1f}%"
        for kvs, percentage in zip(candidates, percentages)
    )
    common.update(
        ready=True,
        status="Kvs utilisation evidence available — no threshold or selection",
        blockers=(),
        note=(
            str(input_row.note or "")
            + " H-S47-C reports required-Kv/candidate-Kvs percentages only; "
            "it applies no suitability classification."
        ).strip(),
    )
    return BalancingPointKvsCandidateUtilisationEvidenceRowV1(
        **common,
        kvs_utilisation_state_id=KVS_UTILISATION_EVIDENCE_AVAILABLE,
        kvs_utilisation_available=True,
        kvs_utilisation_percentages=percentages,
        kvs_utilisation_summary=summary,
    )


def _format_kvs_v1(value: float) -> str:
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


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


def _blocked_projection(
    *blockers: str,
) -> BalancingPointKvsCandidateUtilisationEvidenceV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointKvsCandidateUtilisationEvidenceV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
    )
