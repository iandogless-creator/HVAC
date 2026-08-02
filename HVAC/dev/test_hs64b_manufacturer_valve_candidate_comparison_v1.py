# ======================================================================
# H-S64-B — Manufacturer valve candidate comparison evidence
# ======================================================================

from __future__ import annotations

from dataclasses import replace

from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
    DETAILED_VALVE_DESIGN_DUTY_PENDING,
    NO_DETAILED_VALVE_DESIGN_DUTY_REQUIRED,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1,
)
from HVAC.hydronics.proportioning.balancing_point_manufacturer_valve_candidate_comparison_v1 import (
    MANUFACTURER_VALVE_COMPARISON_AVAILABLE,
    MANUFACTURER_VALVE_COMPARISON_PENDING,
    NO_MANUFACTURER_VALVE_COMPARISON_REQUIRED,
    build_balancing_point_manufacturer_valve_candidate_comparison_v1,
)
from HVAC.hydronics_v3.dto.manufacturer_valve_product_detail_contract_v1 import (
    BUDGET_COST_BAND,
    PREMIUM_COST_BAND,
    STANDARD_COST_BAND,
    ManufacturerValvePresetPointV1,
    ManufacturerValveProductDetailCatalogV1,
    ManufacturerValveProductDetailV1,
)


POINT_ID = "balancing-point:subleg:manufacturer-comparison"


def _duty_row(
    *,
    point_id: str = POINT_ID,
    required_kv: float | None = 6.0,
) -> BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1:
    return BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
        balancing_point_id=point_id,
        point_scope="subleg",
        point_role="common_route_downstream",
        label="Manufacturer comparison point",
        topology="Route-exclusive",
        governed_route_ids=("route-1",),
        ready=True,
        envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
        detailed_valve_design_required=True,
        envelope_available=True,
        approved_for_later_valve_design=True,
        catalog_id="generic-catalog-v1",
        valve_ref="GENERIC-KVS-10",
        current_kv_m3_h=10.0,
        point_flow_kg_s=0.1794,
        flow_m3_h=0.6471,
        required_kv=required_kv,
        controlled_circuit_dp_pa=34_605.0,
        implied_valve_dp_pa=418.8,
        implied_authority=0.012,
        design_valve_dp_pa=2257.3,
        design_authority=0.061,
        status="Approved detailed valve-design duty available",
    )


def _duties(
    *rows: BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1,
) -> BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1:
    return BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1(
        ready=True,
        rows=rows or (_duty_row(),),
        status="Ready — approved detailed valve-design duties",
    )


def _product(
    valve_ref: str,
    cost_band_id: str,
    points: tuple[tuple[float, float], ...],
    *,
    manufacturer_name: str,
    kvs_m3_h: float = 10.0,
) -> ManufacturerValveProductDetailV1:
    return ManufacturerValveProductDetailV1(
        valve_ref=valve_ref,
        manufacturer_name=manufacturer_name,
        product_family="Example balancing valves",
        model_name=f"Example {valve_ref}",
        valve_type_id="static_balancing_valve",
        nominal_dn=20,
        connection_type="threaded",
        kvs_m3_h=kvs_m3_h,
        preset_points=tuple(
            ManufacturerValvePresetPointV1(
                setting_value=setting,
                kv_m3_h=kv,
            )
            for setting, kv in points
        ),
        cost_band_id=cost_band_id,
        note="Test fixture product data only",
    )


def _catalog(
    *products: ManufacturerValveProductDetailV1,
) -> ManufacturerValveProductDetailCatalogV1:
    return ManufacturerValveProductDetailCatalogV1(
        catalog_id="manufacturer-detail-fixture-v1",
        catalog_revision="2026-08-02",
        products=products or (
            _product(
                "STANDARD-20",
                STANDARD_COST_BAND,
                ((1.0, 4.0), (2.0, 7.0), (3.0, 10.0)),
                manufacturer_name="Example Standard Manufacturer",
            ),
            _product(
                "BUDGET-20",
                BUDGET_COST_BAND,
                ((1.0, 2.0), (2.0, 8.0), (3.0, 10.0)),
                manufacturer_name="Example Budget Manufacturer",
            ),
            _product(
                "PREMIUM-20",
                " Premium ",
                ((1.0, 3.0), (2.0, 6.0), (3.0, 10.0)),
                manufacturer_name="Example Premium Manufacturer",
            ),
        ),
    )


def main() -> None:
    duties = _duties()
    catalog = _catalog()
    before_duties = repr(duties)
    before_catalog = repr(catalog)

    result = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            duties,
            catalog,
        )
    )
    repeated = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            duties,
            catalog,
        )
    )

    assert result == repeated
    assert repr(duties) == before_duties
    assert repr(catalog) == before_catalog
    assert result.ready is True, result.status
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.ready is True
    assert row.comparison_state_id == MANUFACTURER_VALVE_COMPARISON_AVAILABLE
    assert row.comparison_available is True
    assert row.approved_basis_catalog_id == "generic-catalog-v1"
    assert row.approved_basis_valve_ref == "GENERIC-KVS-10"
    assert row.approved_current_kv_m3_h == 10.0
    assert row.required_kv == 6.0
    assert row.product_catalog_id == "manufacturer-detail-fixture-v1"
    assert row.product_catalog_revision == "2026-08-02"
    assert row.compatible_candidate_count == 3
    assert row.premium_candidate_count == 1
    assert row.standard_candidate_count == 1
    assert row.budget_candidate_count == 1

    assert tuple(candidate.valve_ref for candidate in row.candidates) == (
        "STANDARD-20",
        "BUDGET-20",
        "PREMIUM-20",
    )
    assert all(candidate.compatible for candidate in row.candidates)
    standard, budget, premium = row.candidates
    assert standard.cost_band_id == STANDARD_COST_BAND
    assert standard.lower_setting_value == 1.0
    assert standard.lower_setting_kv_m3_h == 4.0
    assert standard.upper_setting_value == 2.0
    assert standard.upper_setting_kv_m3_h == 7.0
    assert budget.cost_band_id == BUDGET_COST_BAND
    assert budget.manufacturer_name == "Example Budget Manufacturer"
    assert premium.cost_band_id == PREMIUM_COST_BAND
    assert premium.lower_setting_value == 2.0
    assert premium.upper_setting_value == 2.0
    assert premium.lower_setting_kv_m3_h == 6.0
    assert premium.upper_setting_kv_m3_h == 6.0
    assert all(candidate.kvs_basis_matches for candidate in row.candidates)
    assert all(candidate.target_kv_bracketed for candidate in row.candidates)
    assert "no ranking or recommendation" in row.status
    assert "No product ranking or recommendation" in result.exclusions
    assert "No valve setting selected" in result.exclusions
    assert "No ProjectState persistence" in result.exclusions

    mismatched_product = _product(
        "MISMATCHED-KVS",
        STANDARD_COST_BAND,
        ((1.0, 2.0), (2.0, 6.0), (3.0, 9.0)),
        manufacturer_name="Example Mismatched Manufacturer",
        kvs_m3_h=9.0,
    )
    mismatched = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            duties,
            _catalog(mismatched_product),
        )
    )
    assert mismatched.ready is True
    mismatch = mismatched.rows[0].candidates[0]
    assert mismatch.kvs_basis_matches is False
    assert mismatch.target_kv_bracketed is True
    assert mismatch.compatible is False
    assert "does not match approved current Kv" in mismatch.evidence_notes[0]

    outside_curve_product = _product(
        "OUTSIDE-CURVE",
        BUDGET_COST_BAND,
        ((1.0, 2.0), (2.0, 5.0)),
        manufacturer_name="Example Outside Curve Manufacturer",
    )
    outside_curve = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            duties,
            _catalog(outside_curve_product),
        )
    )
    outside = outside_curve.rows[0].candidates[0]
    assert outside.kvs_basis_matches is True
    assert outside.target_kv_bracketed is False
    assert outside.compatible is False
    assert outside_curve.rows[0].compatible_candidate_count == 0
    assert outside_curve.rows[0].comparison_available is True
    assert "outside declared preset evidence" in outside.evidence_notes[0]

    invalid_catalog = replace(catalog, products=())
    blocked_catalog = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            duties,
            invalid_catalog,
        )
    )
    assert blocked_catalog.ready is False
    assert "non-empty tuple" in blocked_catalog.status

    missing_basis = replace(_duty_row(), catalog_id="")
    blocked_basis = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            _duties(missing_basis),
            catalog,
        )
    )
    assert blocked_basis.ready is False
    assert "approved basis catalogue identity" in blocked_basis.status

    pending_source = replace(
        _duty_row(),
        envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_PENDING,
        envelope_available=False,
        approved_for_later_valve_design=False,
    )
    pending = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            _duties(pending_source),
            catalog,
        )
    )
    assert pending.ready is True
    assert pending.rows[0].comparison_state_id == (
        MANUFACTURER_VALVE_COMPARISON_PENDING
    )
    assert pending.rows[0].comparison_available is False
    assert pending.rows[0].candidates == ()

    no_duty_source = replace(
        _duty_row(),
        envelope_state_id=NO_DETAILED_VALVE_DESIGN_DUTY_REQUIRED,
        detailed_valve_design_required=False,
        envelope_available=False,
        approved_for_later_valve_design=False,
        catalog_id="",
        valve_ref="",
        current_kv_m3_h=None,
        required_kv=None,
    )
    no_duty = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            _duties(no_duty_source),
            catalog,
        )
    )
    assert no_duty.ready is True
    assert no_duty.rows[0].comparison_state_id == (
        NO_MANUFACTURER_VALVE_COMPARISON_REQUIRED
    )
    assert no_duty.rows[0].comparison_required is False

    wrong_source = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            None,
            catalog,
        )
    )
    assert wrong_source.ready is False
    assert "H-S53-A" in wrong_source.status

    bad_tolerance = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            duties,
            catalog,
            kvs_tolerance=float("nan"),
        )
    )
    assert bad_tolerance.ready is False
    assert "kvs_tolerance" in bad_tolerance.status

    duplicate_points = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            _duties(_duty_row(), _duty_row()),
            catalog,
        )
    )
    assert duplicate_points.ready is False
    assert "Duplicate H-S53-A" in duplicate_points.status

    print(
        "OK — H-S64-B premium/standard/budget manufacturer valve "
        "candidate comparison evidence passed."
    )


if __name__ == "__main__":
    main()
