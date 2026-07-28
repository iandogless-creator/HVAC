# ======================================================================
# H-S53-C — Explicit detailed valve product-data blockers
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1,
)


NO_DETAILED_VALVE_PRODUCT_DATA_REQUIRED = (
    "no_detailed_valve_product_data_required"
)
DETAILED_VALVE_PRODUCT_DATA_PENDING = (
    "detailed_valve_product_data_pending"
)
DETAILED_VALVE_PRODUCT_DATA_BLOCKED = (
    "detailed_valve_product_data_blocked"
)

CURRENT_CATALOGUE_MISSING_PRODUCT_EVIDENCE = (
    "nominal valve size / DN",
    "connection / end type",
    "setting / preset characteristic data",
)


@dataclass(frozen=True, slots=True)
class BalancingPointDetailedValveDesignReadinessRowV1:
    balancing_point_id: str = ""
    ready: bool = False
    readiness_state_id: str = ""
    detailed_valve_design_required: bool = False
    duty_envelope_available: bool = False
    catalog_id: str = ""
    valve_ref: str = ""
    current_kv_m3_h: float | None = None
    missing_product_evidence: tuple[str, ...] = ()
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BalancingPointDetailedValveDesignReadinessV1:
    """
    Read-only boundary between an approved H-S53-A hydraulic duty and a
    later product-detail contract.

    The current ValveCatalogDTO deliberately supplies valve reference, Kv
    and note evidence only. It does not authorise DN, connection or setting
    values, so those omissions remain explicit blockers.
    """

    schema: str = "balancing_point_detailed_valve_design_readiness_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointDetailedValveDesignReadinessRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic detailed valve design",
        "No catalogue schema extension",
        "No manufacturer or product data invented",
        "No committed valve product selection",
        "No valve size, DN, connection or setting selected",
        "No product-derived hydraulic mutation",
        "No pump selection",
        "No pipe resizing",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "The current generic catalogue is Kv evidence only. A separate "
        "future product-detail contract must supply DN, connection and "
        "setting-characteristic evidence."
    )


def build_balancing_point_detailed_valve_design_readiness_v1(
    duty_envelopes: (
        BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1 | None
    ),
) -> BalancingPointDetailedValveDesignReadinessV1:
    if not isinstance(
        duty_envelopes,
        BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1,
    ):
        return _blocked_projection(
            "H-S53-A approved valve-candidate design duty required"
        )

    source_rows = tuple(duty_envelopes.rows or ())
    if not source_rows:
        return _blocked_projection("H-S53-A design duty rows required")

    point_ids = tuple(
        _stable_text_v1(getattr(row, "balancing_point_id", ""))
        for row in source_rows
    )
    if any(not point_id for point_id in point_ids):
        return _blocked_projection(
            "Every H-S53-A row requires balancing_point_id"
        )
    if len(set(point_ids)) != len(point_ids):
        return _blocked_projection(
            "Duplicate H-S53-A balancing_point_id values"
        )

    rows = tuple(_resolve_row_v1(row) for row in source_rows)
    upstream = tuple(
        f"H-S53-A: {value}"
        for value in tuple(duty_envelopes.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream, *row_blockers))
    ready = (
        bool(duty_envelopes.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not ready and not blockers:
        blockers = ("Detailed valve-design readiness is not complete",)

    blocked_count = sum(
        1
        for row in rows
        if row.readiness_state_id == DETAILED_VALVE_PRODUCT_DATA_BLOCKED
    )
    pending_count = sum(
        1
        for row in rows
        if row.readiness_state_id == DETAILED_VALVE_PRODUCT_DATA_PENDING
    )
    return BalancingPointDetailedValveDesignReadinessV1(
        ready=ready,
        status=(
            "Ready — no unresolved detailed valve product-data blockers"
            if ready
            else (
                f"Blocked — {blocked_count} point(s) require detailed "
                f"product data; {pending_count} duty envelope(s) pending"
            )
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(
    source,
) -> BalancingPointDetailedValveDesignReadinessRowV1:
    point_id = _stable_text_v1(
        getattr(source, "balancing_point_id", "")
    )
    required = bool(
        getattr(source, "detailed_valve_design_required", False)
    )
    if not required:
        return BalancingPointDetailedValveDesignReadinessRowV1(
            balancing_point_id=point_id,
            ready=bool(getattr(source, "ready", False)),
            readiness_state_id=NO_DETAILED_VALVE_PRODUCT_DATA_REQUIRED,
            status="No detailed valve product data required — no valve duty",
        )

    catalog_id = _stable_text_v1(getattr(source, "catalog_id", ""))
    valve_ref = _stable_text_v1(getattr(source, "valve_ref", ""))
    current_kv = _positive_finite_v1(
        getattr(source, "current_kv_m3_h", None)
    )
    envelope_available = bool(
        getattr(source, "envelope_available", False)
    )
    if not envelope_available:
        source_blockers = _unique_v1(
            tuple(getattr(source, "blockers", ()) or ())
        )
        blockers = source_blockers or (
            "H-S53-A approved detailed valve-design duty envelope required",
        )
        return BalancingPointDetailedValveDesignReadinessRowV1(
            balancing_point_id=point_id,
            ready=False,
            readiness_state_id=DETAILED_VALVE_PRODUCT_DATA_PENDING,
            detailed_valve_design_required=True,
            duty_envelope_available=False,
            catalog_id=catalog_id,
            valve_ref=valve_ref,
            current_kv_m3_h=current_kv,
            status="Blocked — approved detailed valve-design duty pending",
            blockers=blockers,
        )

    basis_missing: list[str] = []
    if not catalog_id:
        basis_missing.append("catalogue identity")
    if not valve_ref:
        basis_missing.append("valve reference")
    if current_kv is None:
        basis_missing.append("current catalogue Kv")
    if basis_missing:
        blockers = tuple(
            f"H-S53-A duty lacks {value}" for value in basis_missing
        )
        return BalancingPointDetailedValveDesignReadinessRowV1(
            balancing_point_id=point_id,
            ready=False,
            readiness_state_id=DETAILED_VALVE_PRODUCT_DATA_BLOCKED,
            detailed_valve_design_required=True,
            duty_envelope_available=True,
            catalog_id=catalog_id,
            valve_ref=valve_ref,
            current_kv_m3_h=current_kv,
            status="Blocked — approved duty identity is incomplete",
            blockers=blockers,
        )

    missing = CURRENT_CATALOGUE_MISSING_PRODUCT_EVIDENCE
    blockers = tuple(
        f"Current valve catalogue lacks {value}" for value in missing
    )
    return BalancingPointDetailedValveDesignReadinessRowV1(
        balancing_point_id=point_id,
        ready=False,
        readiness_state_id=DETAILED_VALVE_PRODUCT_DATA_BLOCKED,
        detailed_valve_design_required=True,
        duty_envelope_available=True,
        catalog_id=catalog_id,
        valve_ref=valve_ref,
        current_kv_m3_h=current_kv,
        missing_product_evidence=missing,
        status=(
            "Blocked — approved hydraulic duty ready; detailed valve "
            "product data required"
        ),
        blockers=blockers,
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
    if number <= 0.0 or number == float("inf") or number != number:
        return None
    return number


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(
    *blockers: str,
) -> BalancingPointDetailedValveDesignReadinessV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointDetailedValveDesignReadinessV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
