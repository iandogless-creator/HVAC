# ======================================================================
# H-S47-B — Non-product Kvs candidate evidence
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_required_kv_preview_v1 import (
    NO_REQUIRED_KV,
    REQUIRED_KV_PREVIEW_AVAILABLE,
    BalancingPointRequiredKvPreviewRowV1,
    BalancingPointRequiredKvPreviewV1,
)


GENERIC_PREFERRED_KVS_SERIES_V1 = (
    0.1,
    0.16,
    0.25,
    0.4,
    0.63,
    1.0,
    1.6,
    2.5,
    4.0,
    6.3,
    10.0,
    16.0,
    25.0,
    40.0,
    63.0,
    100.0,
)
GENERIC_PREFERRED_KVS_SERIES_ID_V1 = "generic_preferred_kvs_series_v1"
NO_KVS_CANDIDATES_REQUIRED = "no_kvs_candidates_required"
GENERIC_KVS_CANDIDATES_AVAILABLE = "generic_kvs_candidates_available"
GENERIC_KVS_CANDIDATES_UNAVAILABLE = "generic_kvs_candidates_unavailable"


@dataclass(frozen=True, slots=True)
class BalancingPointKvsCandidateEvidenceRowV1(
    BalancingPointRequiredKvPreviewRowV1
):
    """H-S47-A required Kv plus generic, non-product Kvs candidates."""

    kvs_candidate_state_id: str = ""
    kvs_candidates_available: bool = False
    kvs_series_id: str = ""
    kvs_candidates: tuple[float, ...] = ()
    kvs_capacity_ratios: tuple[float, ...] = ()
    kvs_operating_fractions: tuple[float, ...] = ()
    kvs_candidate_summary: str = ""


@dataclass(frozen=True, slots=True)
class BalancingPointKvsCandidateEvidenceV1:
    """
    H-S47-B generic Kvs candidate evidence.

    The first candidate_count generic values at or above required Kv are
    exposed for comparison. Values are not manufacturer products, valve
    sizes, settings, selections, approvals or committed balancing results.
    """

    schema: str = "balancing_point_kvs_candidate_evidence_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointKvsCandidateEvidenceRowV1, ...] = ()
    kvs_series_id: str = GENERIC_PREFERRED_KVS_SERIES_ID_V1
    kvs_series: tuple[float, ...] = GENERIC_PREFERRED_KVS_SERIES_V1
    candidate_count: int = 3
    exclusions: tuple[str, ...] = (
        "No engineering approval granted",
        "No Kvs candidate selected",
        "No valve selected",
        "No valve size selected",
        "No valve product selected",
        "No manufacturer catalogue used",
        "No valve setting or preset selected",
        "No design valve pressure changed",
        "No pipe restriction added",
        "No pipe resizing",
        "No pump selected",
        "No hydraulic recalculation",
        "No persistence mutation",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Generic Kvs candidates are comparison evidence only; manual "
        "engineering approval remains pending."
    )


def build_balancing_point_kvs_candidate_evidence_v1(
    required_kv_preview: BalancingPointRequiredKvPreviewV1 | None,
    *,
    kvs_series: tuple[float, ...] = GENERIC_PREFERRED_KVS_SERIES_V1,
    candidate_count: int = 3,
) -> BalancingPointKvsCandidateEvidenceV1:
    """Show the first generic Kvs values at or above each required Kv."""

    clean_series, series_blockers = _normalise_series_v1(kvs_series)
    if series_blockers:
        return _blocked_projection(
            *series_blockers,
            kvs_series=clean_series,
            candidate_count=candidate_count,
        )
    if isinstance(candidate_count, bool) or not isinstance(candidate_count, int):
        return _blocked_projection(
            "candidate_count must be an integer",
            kvs_series=clean_series,
            candidate_count=3,
        )
    if candidate_count <= 0:
        return _blocked_projection(
            "candidate_count must be greater than zero",
            kvs_series=clean_series,
            candidate_count=candidate_count,
        )
    if required_kv_preview is None:
        return _blocked_projection(
            "H-S47-A required Kv preview required",
            kvs_series=clean_series,
            candidate_count=candidate_count,
        )
    if not isinstance(
        required_kv_preview,
        BalancingPointRequiredKvPreviewV1,
    ):
        return _blocked_projection(
            "required_kv_preview is not BalancingPointRequiredKvPreviewV1",
            kvs_series=clean_series,
            candidate_count=candidate_count,
        )

    input_rows = tuple(required_kv_preview.rows or ())
    if not input_rows:
        return _blocked_projection(
            "H-S47-A required Kv rows required",
            *tuple(required_kv_preview.blockers or ()),
            kvs_series=clean_series,
            candidate_count=candidate_count,
        )

    rows = tuple(
        _resolve_row_v1(
            row,
            kvs_series=clean_series,
            candidate_count=candidate_count,
        )
        for row in input_rows
    )
    upstream_blockers = tuple(
        f"H-S47-A: {value}"
        for value in tuple(required_kv_preview.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = (
        bool(required_kv_preview.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not required_kv_preview.ready and not blockers:
        blockers = ("H-S47-A required Kv preview is not ready",)
        ready = False

    candidate_rows = sum(1 for row in rows if row.kvs_candidates_available)
    return BalancingPointKvsCandidateEvidenceV1(
        ready=ready,
        status=(
            f"Ready — generic Kvs candidates available at {candidate_rows} "
            "point(s); no candidate selected"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
        kvs_series=clean_series,
        candidate_count=candidate_count,
    )


def _resolve_row_v1(
    input_row: BalancingPointRequiredKvPreviewRowV1,
    *,
    kvs_series: tuple[float, ...],
    candidate_count: int,
) -> BalancingPointKvsCandidateEvidenceRowV1:
    common = asdict(input_row)
    existing_blockers = _unique_v1(tuple(input_row.blockers or ()))

    if input_row.required_kv_state_id == NO_REQUIRED_KV:
        common.update(
            ready=bool(input_row.ready) and not existing_blockers,
            status="No Kvs candidates required — no valve duty",
            blockers=existing_blockers,
            note=(
                str(input_row.note or "")
                + " H-S47-B candidate comparison is dormant for this point."
            ).strip(),
        )
        return BalancingPointKvsCandidateEvidenceRowV1(
            **common,
            kvs_candidate_state_id=NO_KVS_CANDIDATES_REQUIRED,
            kvs_candidates_available=False,
            kvs_series_id=GENERIC_PREFERRED_KVS_SERIES_ID_V1,
        )

    required_kv = _positive_finite_v1(input_row.required_kv)
    blockers = list(existing_blockers)
    if (
        not input_row.ready
        or not input_row.required_kv_available
        or input_row.required_kv_state_id != REQUIRED_KV_PREVIEW_AVAILABLE
    ):
        blockers.append("H-S47-A required Kv evidence unavailable")
    if required_kv is None:
        blockers.append("Positive finite required Kv required")

    if blockers:
        clean = _unique_v1(tuple(blockers))
        common.update(
            ready=False,
            status="Blocked — generic Kvs candidate evidence unavailable",
            blockers=clean,
            note="No generic Kvs candidates released.",
        )
        return BalancingPointKvsCandidateEvidenceRowV1(
            **common,
            kvs_candidate_state_id=GENERIC_KVS_CANDIDATES_UNAVAILABLE,
            kvs_candidates_available=False,
            kvs_series_id=GENERIC_PREFERRED_KVS_SERIES_ID_V1,
        )

    candidates = tuple(
        value for value in kvs_series if value >= required_kv
    )[:candidate_count]
    if not candidates:
        blocker = (
            f"Generic Kvs series has no value at or above required Kv "
            f"{required_kv:.3f}"
        )
        common.update(
            ready=False,
            status="Blocked — " + blocker,
            blockers=(blocker,),
            note="No generic Kvs candidates released.",
        )
        return BalancingPointKvsCandidateEvidenceRowV1(
            **common,
            kvs_candidate_state_id=GENERIC_KVS_CANDIDATES_UNAVAILABLE,
            kvs_candidates_available=False,
            kvs_series_id=GENERIC_PREFERRED_KVS_SERIES_ID_V1,
        )

    capacity_ratios = tuple(value / required_kv for value in candidates)
    operating_fractions = tuple(required_kv / value for value in candidates)
    summary = ", ".join(_format_kvs_v1(value) for value in candidates)
    common.update(
        ready=True,
        status="Generic Kvs candidates available — no selection",
        blockers=(),
        note=(
            str(input_row.note or "")
            + " H-S47-B candidates are generic preferred values at or above "
            "required Kv; they are not products, sizes, settings or selections."
        ).strip(),
    )
    return BalancingPointKvsCandidateEvidenceRowV1(
        **common,
        kvs_candidate_state_id=GENERIC_KVS_CANDIDATES_AVAILABLE,
        kvs_candidates_available=True,
        kvs_series_id=GENERIC_PREFERRED_KVS_SERIES_ID_V1,
        kvs_candidates=candidates,
        kvs_capacity_ratios=capacity_ratios,
        kvs_operating_fractions=operating_fractions,
        kvs_candidate_summary=summary,
    )


def _normalise_series_v1(
    values: tuple[float, ...],
) -> tuple[tuple[float, ...], tuple[str, ...]]:
    try:
        source = tuple(values or ())
    except TypeError:
        return (), ("kvs_series must be iterable",)
    clean: list[float] = []
    for value in source:
        number = _positive_finite_v1(value)
        if number is None:
            return tuple(clean), ("Every generic Kvs value must be positive and finite",)
        if number not in clean:
            clean.append(number)
    if not clean:
        return (), ("Generic Kvs series required",)
    if clean != sorted(clean):
        return tuple(clean), ("Generic Kvs series must be ascending",)
    return tuple(clean), ()


def _format_kvs_v1(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


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
    kvs_series: tuple[float, ...],
    candidate_count: int,
) -> BalancingPointKvsCandidateEvidenceV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointKvsCandidateEvidenceV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
        kvs_series=kvs_series,
        candidate_count=candidate_count,
    )
