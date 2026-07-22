# ======================================================================
# H-S45-C — Point-scoped low-authority design-disposition evidence
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass

from HVAC.hydronics.proportioning.balancing_point_valve_authority_preview_v1 import (
    BalancingPointValveAuthorityPreviewRowV1,
    BalancingPointValveAuthorityPreviewV1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    ACCEPTABLE_AUTHORITY_PREVIEW,
    HIGH_THROTTLING_BURDEN,
    MANUAL_REVIEW_REQUIRED,
    TOO_LOW_AUTHORITY_PREVIEW,
    VALVE_AUTHORITY_NONE_REQUIRED,
)


NO_VALVE_REQUIRED = "no_valve_required"
AUTHORITY_ACCEPTABLE_FOR_REVIEW = "authority_acceptable_for_review"
LOW_AUTHORITY_MANUAL_REVIEW_REQUIRED = (
    "low_authority_manual_review_required"
)
HIGH_THROTTLING_MANUAL_REVIEW_REQUIRED = (
    "high_throttling_manual_review_required"
)
EVIDENCE_UNAVAILABLE = "evidence_unavailable"

_DISPOSITION_LABELS = {
    NO_VALVE_REQUIRED: "No valve required",
    AUTHORITY_ACCEPTABLE_FOR_REVIEW: "Authority acceptable for review",
    LOW_AUTHORITY_MANUAL_REVIEW_REQUIRED: (
        "Low-authority manual review required"
    ),
    HIGH_THROTTLING_MANUAL_REVIEW_REQUIRED: (
        "High-throttling manual review required"
    ),
    EVIDENCE_UNAVAILABLE: (
        "Blocked because required evidence is unavailable"
    ),
}


@dataclass(frozen=True, slots=True)
class BalancingPointLowAuthorityDesignDispositionRowV1(
    BalancingPointValveAuthorityPreviewRowV1
):
    """H-S45-B evidence plus a non-authoritative review disposition."""

    design_disposition_id: str = ""
    design_disposition_label: str = ""
    manual_review_required: bool = False
    evidence_available: bool = False


@dataclass(frozen=True, slots=True)
class BalancingPointLowAuthorityDesignDispositionV1:
    """
    H-S45-C point-scoped design-disposition evidence.

    This classifies what the H-S45-B result means for review. It does not
    select a valve, calculate/select Kv or Kvs, change valve pressure drop,
    add pipe restriction, resize pipe, select a pump, persist intent, or
    perform final balancing.
    """

    schema: str = "balancing_point_low_authority_design_disposition_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointLowAuthorityDesignDispositionRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No valve selected",
        "No Kv or Kvs calculated or selected",
        "No valve product selected",
        "No design valve pressure increased",
        "No pipe restriction added",
        "No pipe resizing",
        "No pump selected",
        "No hydraulic recalculation",
        "No persistence mutation",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Disposition is evidence only; manual review remains authoritative."
    )


def build_balancing_point_low_authority_design_disposition_v1(
    authority_preview: BalancingPointValveAuthorityPreviewV1 | None,
) -> BalancingPointLowAuthorityDesignDispositionV1:
    """Map each H-S45-B point result to a clear review disposition."""

    if authority_preview is None:
        return _blocked_projection("H-S45-B point authority evidence required")
    if not isinstance(authority_preview, BalancingPointValveAuthorityPreviewV1):
        return _blocked_projection(
            "authority_preview is not BalancingPointValveAuthorityPreviewV1"
        )

    input_rows = tuple(authority_preview.rows or ())
    if not input_rows:
        return _blocked_projection(
            "H-S45-B point authority rows required",
            *tuple(authority_preview.blockers or ()),
        )

    point_ids = tuple(str(row.balancing_point_id or "") for row in input_rows)
    if any(not point_id for point_id in point_ids):
        return _blocked_projection("Every H-S45-B row requires balancing_point_id")
    duplicates = sorted(
        {point_id for point_id in point_ids if point_ids.count(point_id) > 1}
    )
    if duplicates:
        return _blocked_projection(
            "Duplicate H-S45-B balancing_point_id values: "
            + ", ".join(duplicates)
        )

    rows = tuple(_resolve_row_v1(row) for row in input_rows)
    upstream_blockers = tuple(
        f"H-S45-B: {value}"
        for value in tuple(authority_preview.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = (
        bool(authority_preview.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not authority_preview.ready and not blockers:
        blockers = ("H-S45-B point authority evidence is not ready",)
        ready = False

    return BalancingPointLowAuthorityDesignDispositionV1(
        ready=ready,
        status=(
            "Ready — point-scoped design dispositions available"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(
    input_row: BalancingPointValveAuthorityPreviewRowV1,
) -> BalancingPointLowAuthorityDesignDispositionRowV1:
    common = asdict(input_row)
    existing_blockers = _unique_v1(tuple(input_row.blockers or ()))
    band_id = str(input_row.authority_band_id or "")

    if (
        not input_row.ready
        or existing_blockers
        or band_id == MANUAL_REVIEW_REQUIRED
    ):
        blockers = existing_blockers or (
            "Required H-S45-B point evidence is unavailable",
        )
        label = _DISPOSITION_LABELS[EVIDENCE_UNAVAILABLE]
        common.update(
            ready=False,
            status=label,
            blockers=blockers,
            note=(
                str(input_row.note or "")
                + " H-S45-C releases no design disposition beyond the "
                "evidence-unavailable state."
            ).strip(),
        )
        return BalancingPointLowAuthorityDesignDispositionRowV1(
            **common,
            design_disposition_id=EVIDENCE_UNAVAILABLE,
            design_disposition_label=label,
            manual_review_required=True,
            evidence_available=False,
        )

    disposition_by_band = {
        VALVE_AUTHORITY_NONE_REQUIRED: (NO_VALVE_REQUIRED, False),
        ACCEPTABLE_AUTHORITY_PREVIEW: (
            AUTHORITY_ACCEPTABLE_FOR_REVIEW,
            False,
        ),
        TOO_LOW_AUTHORITY_PREVIEW: (
            LOW_AUTHORITY_MANUAL_REVIEW_REQUIRED,
            True,
        ),
        HIGH_THROTTLING_BURDEN: (
            HIGH_THROTTLING_MANUAL_REVIEW_REQUIRED,
            True,
        ),
    }
    resolved = disposition_by_band.get(band_id)
    if resolved is None:
        label = _DISPOSITION_LABELS[EVIDENCE_UNAVAILABLE]
        blocker = f"Unsupported H-S45-B authority band: {band_id or 'missing'}"
        common.update(
            ready=False,
            status=label,
            blockers=(blocker,),
            note="No design disposition released.",
        )
        return BalancingPointLowAuthorityDesignDispositionRowV1(
            **common,
            design_disposition_id=EVIDENCE_UNAVAILABLE,
            design_disposition_label=label,
            manual_review_required=True,
            evidence_available=False,
        )

    disposition_id, manual_review_required = resolved
    label = _DISPOSITION_LABELS[disposition_id]
    common.update(
        ready=True,
        status=label,
        blockers=(),
        note=(
            str(input_row.note or "")
            + " H-S45-C disposition is review evidence only; it does not "
            "choose or alter a valve or hydraulic result."
        ).strip(),
    )
    return BalancingPointLowAuthorityDesignDispositionRowV1(
        **common,
        design_disposition_id=disposition_id,
        design_disposition_label=label,
        manual_review_required=manual_review_required,
        evidence_available=True,
    )


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(
    *blockers: str,
) -> BalancingPointLowAuthorityDesignDispositionV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointLowAuthorityDesignDispositionV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
    )
