# ======================================================================
# H-S64-B — Manufacturer valve candidate comparison evidence
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1,
)
from HVAC.hydronics_v3.dto.manufacturer_valve_product_detail_contract_v1 import (
    BUDGET_COST_BAND,
    PREMIUM_COST_BAND,
    STANDARD_COST_BAND,
    ManufacturerValvePresetPointV1,
    ManufacturerValveProductDetailCatalogV1,
    validate_manufacturer_valve_product_detail_catalog_v1,
)


NO_MANUFACTURER_VALVE_COMPARISON_REQUIRED = (
    "no_manufacturer_valve_comparison_required"
)
MANUFACTURER_VALVE_COMPARISON_PENDING = (
    "manufacturer_valve_comparison_pending"
)
MANUFACTURER_VALVE_COMPARISON_AVAILABLE = (
    "manufacturer_valve_comparison_available"
)
MANUFACTURER_VALVE_COMPARISON_UNAVAILABLE = (
    "manufacturer_valve_comparison_unavailable"
)


@dataclass(frozen=True, slots=True)
class ManufacturerValveCandidateComparisonEvidenceV1:
    valve_ref: str = ""
    manufacturer_name: str = ""
    product_family: str = ""
    model_name: str = ""
    valve_type_id: str = ""
    nominal_dn: int | None = None
    connection_type: str = ""
    cost_band_id: str = ""
    approved_current_kv_m3_h: float | None = None
    product_kvs_m3_h: float | None = None
    kvs_basis_matches: bool = False
    required_kv: float | None = None
    target_kv_bracketed: bool = False
    lower_setting_value: float | None = None
    lower_setting_kv_m3_h: float | None = None
    upper_setting_value: float | None = None
    upper_setting_kv_m3_h: float | None = None
    compatible: bool = False
    status: str = ""
    evidence_notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BalancingPointManufacturerValveCandidateComparisonRowV1:
    balancing_point_id: str = ""
    ready: bool = False
    comparison_state_id: str = ""
    comparison_required: bool = False
    comparison_available: bool = False
    approved_basis_catalog_id: str = ""
    approved_basis_valve_ref: str = ""
    approved_current_kv_m3_h: float | None = None
    required_kv: float | None = None
    product_catalog_id: str = ""
    product_catalog_revision: str = ""
    candidates: tuple[
        ManufacturerValveCandidateComparisonEvidenceV1, ...
    ] = ()
    compatible_candidate_count: int = 0
    premium_candidate_count: int = 0
    standard_candidate_count: int = 0
    budget_candidate_count: int = 0
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BalancingPointManufacturerValveCandidateComparisonV1:
    schema: str = (
        "balancing_point_manufacturer_valve_candidate_comparison_v1"
    )
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[
        BalancingPointManufacturerValveCandidateComparisonRowV1, ...
    ] = ()
    exclusions: tuple[str, ...] = (
        "No product ranking or recommendation",
        "No automatic premium, standard or budget choice",
        "No cost-band quality inference",
        "No valve product accepted or committed",
        "No valve setting selected",
        "No hydraulic mutation",
        "No ProjectState persistence",
    )
    note: str = (
        "Every supplied product remains comparison evidence in catalogue "
        "order. Compatibility does not grant selection authority."
    )


def build_balancing_point_manufacturer_valve_candidate_comparison_v1(
    duty_envelopes: (
        BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1 | None
    ),
    product_catalog: ManufacturerValveProductDetailCatalogV1 | None,
    *,
    kvs_tolerance: float = 1e-9,
) -> BalancingPointManufacturerValveCandidateComparisonV1:
    """Compare approved duties with explicit manufacturer product data."""

    if not isinstance(
        duty_envelopes,
        BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1,
    ):
        return _blocked_v1(
            "H-S53-A approved valve-candidate design duty required"
        )
    if not math.isfinite(kvs_tolerance) or kvs_tolerance < 0.0:
        return _blocked_v1("kvs_tolerance must be finite and non-negative")

    catalog_validation = (
        validate_manufacturer_valve_product_detail_catalog_v1(
            product_catalog
        )
    )
    if not catalog_validation.ready:
        return _blocked_v1(
            *tuple(catalog_validation.blockers or ()),
        )

    source_rows = tuple(duty_envelopes.rows or ())
    if not source_rows:
        return _blocked_v1("H-S53-A design duty rows required")

    point_ids = tuple(
        _stable_text_v1(getattr(row, "balancing_point_id", ""))
        for row in source_rows
    )
    if any(not point_id for point_id in point_ids):
        return _blocked_v1(
            "Every H-S53-A row requires balancing_point_id"
        )
    if len(set(point_ids)) != len(point_ids):
        return _blocked_v1(
            "Duplicate H-S53-A balancing_point_id values"
        )

    rows = tuple(
        _resolve_row_v1(
            source,
            product_catalog,
            kvs_tolerance=kvs_tolerance,
        )
        for source in source_rows
    )
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
        blockers = (
            "Manufacturer valve comparison evidence is not ready",
        )

    available_count = sum(
        1 for row in rows if row.comparison_available
    )
    compatible_count = sum(
        row.compatible_candidate_count for row in rows
    )
    return BalancingPointManufacturerValveCandidateComparisonV1(
        ready=ready,
        status=(
            "Ready — manufacturer valve comparison evidence available at "
            f"{available_count} point(s); {compatible_count} compatible "
            "candidate(s); supplied order retained"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(
    source,
    product_catalog: ManufacturerValveProductDetailCatalogV1,
    *,
    kvs_tolerance: float,
) -> BalancingPointManufacturerValveCandidateComparisonRowV1:
    point_id = _stable_text_v1(
        getattr(source, "balancing_point_id", "")
    )
    required = bool(
        getattr(source, "detailed_valve_design_required", False)
    )
    common = dict(
        balancing_point_id=point_id,
        comparison_required=required,
        approved_basis_catalog_id=_stable_text_v1(
            getattr(source, "catalog_id", "")
        ),
        approved_basis_valve_ref=_stable_text_v1(
            getattr(source, "valve_ref", "")
        ),
        approved_current_kv_m3_h=_positive_finite_v1(
            getattr(source, "current_kv_m3_h", None)
        ),
        required_kv=_positive_finite_v1(
            getattr(source, "required_kv", None)
        ),
        product_catalog_id=product_catalog.catalog_id.strip(),
        product_catalog_revision=product_catalog.catalog_revision.strip(),
    )

    if not required:
        return BalancingPointManufacturerValveCandidateComparisonRowV1(
            **common,
            ready=bool(getattr(source, "ready", False)),
            comparison_state_id=(
                NO_MANUFACTURER_VALVE_COMPARISON_REQUIRED
            ),
            status=(
                "No manufacturer valve comparison required — no valve duty"
            ),
        )

    envelope_available = bool(
        getattr(source, "envelope_available", False)
    ) and (
        _stable_text_v1(getattr(source, "envelope_state_id", ""))
        == DETAILED_VALVE_DESIGN_DUTY_AVAILABLE
    )
    if not envelope_available:
        return BalancingPointManufacturerValveCandidateComparisonRowV1(
            **common,
            ready=bool(getattr(source, "ready", False)),
            comparison_state_id=MANUFACTURER_VALVE_COMPARISON_PENDING,
            status=(
                "Manufacturer valve comparison pending — approved "
                "H-S53-A duty unavailable"
            ),
        )

    missing: list[str] = []
    if not common["approved_basis_catalog_id"]:
        missing.append("approved basis catalogue identity")
    if not common["approved_basis_valve_ref"]:
        missing.append("approved basis valve reference")
    if common["approved_current_kv_m3_h"] is None:
        missing.append("approved current Kv")
    if common["required_kv"] is None:
        missing.append("required Kv")
    if missing:
        blocker = "H-S53-A duty lacks " + ", ".join(missing)
        return BalancingPointManufacturerValveCandidateComparisonRowV1(
            **common,
            ready=False,
            comparison_state_id=(
                MANUFACTURER_VALVE_COMPARISON_UNAVAILABLE
            ),
            status="Blocked — manufacturer valve comparison unavailable",
            blockers=(blocker,),
        )

    candidates = tuple(
        _compare_product_v1(
            product,
            approved_current_kv=common["approved_current_kv_m3_h"],
            required_kv=common["required_kv"],
            kvs_tolerance=kvs_tolerance,
        )
        for product in product_catalog.products
    )
    compatible = tuple(
        candidate for candidate in candidates if candidate.compatible
    )
    band_counts = {
        PREMIUM_COST_BAND: 0,
        STANDARD_COST_BAND: 0,
        BUDGET_COST_BAND: 0,
    }
    for candidate in compatible:
        band_counts[candidate.cost_band_id] += 1

    return BalancingPointManufacturerValveCandidateComparisonRowV1(
        **common,
        ready=True,
        comparison_state_id=MANUFACTURER_VALVE_COMPARISON_AVAILABLE,
        comparison_available=True,
        candidates=candidates,
        compatible_candidate_count=len(compatible),
        premium_candidate_count=band_counts[PREMIUM_COST_BAND],
        standard_candidate_count=band_counts[STANDARD_COST_BAND],
        budget_candidate_count=band_counts[BUDGET_COST_BAND],
        status=(
            "Manufacturer valve comparison available — "
            f"{len(compatible)} of {len(candidates)} product(s) compatible; "
            "no ranking or recommendation"
        ),
    )


def _compare_product_v1(
    product,
    *,
    approved_current_kv: float,
    required_kv: float,
    kvs_tolerance: float,
) -> ManufacturerValveCandidateComparisonEvidenceV1:
    product_kvs = float(product.kvs_m3_h)
    kvs_matches = math.isclose(
        product_kvs,
        approved_current_kv,
        rel_tol=kvs_tolerance,
        abs_tol=kvs_tolerance,
    )
    lower, upper = _bracket_target_kv_v1(
        product.preset_points,
        required_kv,
        tolerance=kvs_tolerance,
    )
    bracketed = lower is not None and upper is not None
    compatible = kvs_matches and bracketed
    notes: list[str] = []
    if not kvs_matches:
        notes.append("Product Kvs does not match approved current Kv basis")
    if not bracketed:
        notes.append("Required Kv lies outside declared preset evidence")
    if compatible:
        notes.append(
            "Approved current Kv basis matched and required Kv bracketed"
        )

    return ManufacturerValveCandidateComparisonEvidenceV1(
        valve_ref=product.valve_ref,
        manufacturer_name=product.manufacturer_name,
        product_family=product.product_family,
        model_name=product.model_name,
        valve_type_id=product.valve_type_id,
        nominal_dn=product.nominal_dn,
        connection_type=product.connection_type,
        cost_band_id=_stable_text_v1(product.cost_band_id).casefold(),
        approved_current_kv_m3_h=approved_current_kv,
        product_kvs_m3_h=product_kvs,
        kvs_basis_matches=kvs_matches,
        required_kv=required_kv,
        target_kv_bracketed=bracketed,
        lower_setting_value=(
            None if lower is None else float(lower.setting_value)
        ),
        lower_setting_kv_m3_h=(
            None if lower is None else float(lower.kv_m3_h)
        ),
        upper_setting_value=(
            None if upper is None else float(upper.setting_value)
        ),
        upper_setting_kv_m3_h=(
            None if upper is None else float(upper.kv_m3_h)
        ),
        compatible=compatible,
        status=(
            "Compatible manufacturer candidate comparison evidence"
            if compatible
            else "Not compatible with approved valve duty evidence"
        ),
        evidence_notes=tuple(notes),
    )


def _bracket_target_kv_v1(
    points: tuple[ManufacturerValvePresetPointV1, ...],
    target_kv: float,
    *,
    tolerance: float,
) -> tuple[
    ManufacturerValvePresetPointV1 | None,
    ManufacturerValvePresetPointV1 | None,
]:
    lower = None
    upper = None
    for point in points:
        kv = float(point.kv_m3_h)
        if math.isclose(
            kv,
            target_kv,
            rel_tol=tolerance,
            abs_tol=tolerance,
        ):
            return point, point
        if kv < target_kv:
            lower = point
            continue
        upper = point
        break
    return lower, upper


def _stable_text_v1(value: object) -> str:
    return str(value or "").strip()


def _positive_finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0.0 else None


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_v1(
    *blockers: str,
) -> BalancingPointManufacturerValveCandidateComparisonV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointManufacturerValveCandidateComparisonV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
