# ======================================================================
# H-S45-B — Point-scoped valve-authority calculation and classification
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_controlled_circuit_dp_authority_v1 import (
    BalancingPointControlledCircuitDpAuthorityV1,
    BalancingPointControlledCircuitDpRowV1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    ACCEPTABLE_AUTHORITY_PREVIEW,
    HIGH_THROTTLING_BURDEN,
    MANUAL_REVIEW_REQUIRED,
    TOO_LOW_AUTHORITY_PREVIEW,
    VALVE_AUTHORITY_NONE_REQUIRED,
    build_valve_authority_bands_v1,
    classify_valve_authority_band_v1,
)
from HVAC.hydronics.proportioning.valve_authority_preview_v1 import (
    calculate_valve_authority_v1,
)


@dataclass(frozen=True, slots=True)
class BalancingPointValveAuthorityPreviewRowV1(
    BalancingPointControlledCircuitDpRowV1
):
    """H-S45-A point pressure evidence plus canonical authority result."""

    authority_formula: str = (
        "authority = design_valve_dp_pa / "
        "(design_valve_dp_pa + controlled_circuit_dp_pa)"
    )


@dataclass(frozen=True, slots=True)
class BalancingPointValveAuthorityPreviewV1:
    """
    H-S45-B point-scoped authority preview.

    This consumes H-S45-A pressure authority and the existing H-S32 formula
    and design bands. It does not choose a physical valve location, product,
    Kv/Kvs, pump, pipe size, persisted intent, or final balancing result.
    """

    schema: str = "balancing_point_valve_authority_preview_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointValveAuthorityPreviewRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No valve product selected",
        "No Kv or Kvs calculated or selected",
        "No lockshield turn count",
        "No manufacturer valve data",
        "No physical valve position inferred",
        "No pump selected",
        "No pipe resizing",
        "No persistence mutation",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Authority is calculated at each stable balancing point from its "
        "H-S44-D design valve Δp and H-S45-A controlled-circuit Δp."
    )


def build_balancing_point_valve_authority_preview_v1(
    controlled_circuit_authority: (
        BalancingPointControlledCircuitDpAuthorityV1 | None
    ),
) -> BalancingPointValveAuthorityPreviewV1:
    """Calculate and classify canonical authority for each H-S45-A point."""

    if controlled_circuit_authority is None:
        return _blocked_projection("H-S45-A point controlled-circuit authority required")
    if not isinstance(
        controlled_circuit_authority,
        BalancingPointControlledCircuitDpAuthorityV1,
    ):
        return _blocked_projection(
            "controlled_circuit_authority is not "
            "BalancingPointControlledCircuitDpAuthorityV1"
        )

    input_rows = tuple(controlled_circuit_authority.rows or ())
    if not input_rows:
        return _blocked_projection(
            "H-S45-A point controlled-circuit rows required",
            *tuple(controlled_circuit_authority.blockers or ()),
        )

    point_ids = tuple(str(row.balancing_point_id or "") for row in input_rows)
    if any(not point_id for point_id in point_ids):
        return _blocked_projection("Every H-S45-A row requires balancing_point_id")
    duplicates = sorted(
        {point_id for point_id in point_ids if point_ids.count(point_id) > 1}
    )
    if duplicates:
        return _blocked_projection(
            "Duplicate H-S45-A balancing_point_id values: " + ", ".join(duplicates)
        )

    labels = {
        band.band_id: band.label
        for band in build_valve_authority_bands_v1()
    }
    rows = tuple(_resolve_row_v1(row, labels=labels) for row in input_rows)
    upstream_blockers = tuple(
        f"H-S45-A: {value}"
        for value in tuple(controlled_circuit_authority.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = (
        bool(controlled_circuit_authority.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not controlled_circuit_authority.ready and not blockers:
        blockers = ("H-S45-A point controlled-circuit authority is not ready",)
        ready = False

    return BalancingPointValveAuthorityPreviewV1(
        ready=ready,
        status=(
            "Ready — point-scoped valve authority calculated and classified"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(
    input_row: BalancingPointControlledCircuitDpRowV1,
    *,
    labels: dict[str, str],
) -> BalancingPointValveAuthorityPreviewRowV1:
    common = asdict(input_row)

    if input_row.authority_band_id == VALVE_AUTHORITY_NONE_REQUIRED:
        common.update(
            ready=bool(input_row.ready) and not tuple(input_row.blockers or ()),
            authority=None,
            authority_band_id=VALVE_AUTHORITY_NONE_REQUIRED,
            authority_label=labels[VALVE_AUTHORITY_NONE_REQUIRED],
            status="No valve authority preview required",
            blockers=tuple(input_row.blockers or ()),
            note=(
                str(input_row.note or "")
                + " H-S45-B remains dormant because no point valve duty exists."
            ).strip(),
        )
        return BalancingPointValveAuthorityPreviewRowV1(**common)

    blockers = list(input_row.blockers or ())
    if not input_row.ready and not blockers:
        blockers.append("H-S45-A point controlled-circuit row is not ready")

    design_dp = _positive_finite_v1(input_row.design_valve_dp_pa)
    controlled_dp = _positive_finite_v1(input_row.controlled_circuit_dp_pa)
    if design_dp is None:
        blockers.append("Positive finite design valve Δp required")
    if controlled_dp is None:
        blockers.append("Positive finite controlled-circuit Δp required")

    if blockers:
        clean = _unique_v1(tuple(str(value) for value in blockers))
        common.update(
            ready=False,
            authority=None,
            authority_band_id=MANUAL_REVIEW_REQUIRED,
            authority_label=labels[MANUAL_REVIEW_REQUIRED],
            status="Blocked — " + "; ".join(clean),
            blockers=clean,
            note="No point-scoped authority ratio released.",
        )
        return BalancingPointValveAuthorityPreviewRowV1(**common)

    authority = calculate_valve_authority_v1(
        design_valve_dp_pa=design_dp,
        controlled_circuit_dp_pa=controlled_dp,
    )
    band_id = classify_valve_authority_band_v1(authority)
    label = labels.get(band_id, labels[MANUAL_REVIEW_REQUIRED])
    if band_id == MANUAL_REVIEW_REQUIRED:
        common.update(
            ready=False,
            authority=authority,
            authority_band_id=band_id,
            authority_label=label,
            status="Blocked — authority ratio could not be classified",
            blockers=("Authority ratio could not be classified",),
            note="No valve selection.",
        )
        return BalancingPointValveAuthorityPreviewRowV1(**common)

    status_by_band = {
        ACCEPTABLE_AUTHORITY_PREVIEW: "Ready — acceptable authority preview",
        TOO_LOW_AUTHORITY_PREVIEW: (
            "Warning — valve authority below preview minimum"
        ),
        HIGH_THROTTLING_BURDEN: "Warning — high throttling burden preview",
    }
    common.update(
        ready=True,
        authority=authority,
        authority_band_id=band_id,
        authority_label=label,
        status=status_by_band.get(band_id, f"Ready — {label}"),
        blockers=(),
        note=(
            str(input_row.note or "")
            + " H-S45-B uses the canonical H-S32 formula and bands; point "
            "scope and governed-route pressure provenance are unchanged."
        ).strip(),
    )
    return BalancingPointValveAuthorityPreviewRowV1(**common)


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


def _blocked_projection(*blockers: str) -> BalancingPointValveAuthorityPreviewV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointValveAuthorityPreviewV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
    )
