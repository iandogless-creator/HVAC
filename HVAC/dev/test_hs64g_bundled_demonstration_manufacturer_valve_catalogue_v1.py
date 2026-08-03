# ======================================================================
# H-S64-G — Bundled demonstration manufacturer valve catalogue
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1,
)
from HVAC.hydronics.proportioning.balancing_point_manufacturer_valve_candidate_comparison_v1 import (
    build_balancing_point_manufacturer_valve_candidate_comparison_v1,
)
from HVAC.hydronics_v3.catalogues.bundled_demonstration_manufacturer_valve_catalogue_v1 import (
    BUNDLED_DEMONSTRATION_MANUFACTURER_VALVE_CATALOGUE_PATH_V1,
    load_bundled_demonstration_manufacturer_valve_catalogue_v1,
)
from HVAC.hydronics_v3.catalogues.local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1 import (
    build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1,
)
from HVAC.hydronics_v3.dto.manufacturer_valve_product_detail_contract_v1 import (
    BUDGET_COST_BAND,
    PREMIUM_COST_BAND,
    STANDARD_COST_BAND,
    validate_manufacturer_valve_product_detail_catalog_v1,
)


def _approved_duty() -> BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1:
    return BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1(
        ready=True,
        rows=(
            BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
                balancing_point_id="balancing-point:hs64g-demonstration",
                ready=True,
                envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
                detailed_valve_design_required=True,
                envelope_available=True,
                approved_for_later_valve_design=True,
                catalog_id="generic-catalog-v1",
                valve_ref="GENERIC-KVS-10",
                current_kv_m3_h=10.0,
                required_kv=1.608,
            ),
        ),
    )


def main() -> None:
    assert BUNDLED_DEMONSTRATION_MANUFACTURER_VALVE_CATALOGUE_PATH_V1.is_file()

    catalogue = load_bundled_demonstration_manufacturer_valve_catalogue_v1()
    repeated = load_bundled_demonstration_manufacturer_valve_catalogue_v1()
    assert catalogue == repeated
    assert catalogue.catalog_id == (
        "hvacgooee-demonstration-manufacturer-valves-v1"
    )
    assert catalogue.catalog_revision == "demo-2026-08-03"
    assert len(catalogue.products) == 3
    assert tuple(product.cost_band_id for product in catalogue.products) == (
        PREMIUM_COST_BAND,
        STANDARD_COST_BAND,
        BUDGET_COST_BAND,
    )
    assert all(product.nominal_dn == 20 for product in catalogue.products)
    assert all(product.kvs_m3_h == 10.0 for product in catalogue.products)
    assert all("Fictional" in product.manufacturer_name for product in catalogue.products)
    assert all(
        "not a real manufacturer product" in product.note
        and "not for specification or final design" in product.note
        and "does not imply quality" in product.note
        for product in catalogue.products
    )

    validation = validate_manufacturer_valve_product_detail_catalog_v1(
        catalogue
    )
    assert validation.ready is True, validation.status
    assert validation.product_count == 3

    runtime = (
        build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1(
            BUNDLED_DEMONSTRATION_MANUFACTURER_VALVE_CATALOGUE_PATH_V1
        )
    )
    assert runtime.ready is True, runtime.status
    assert runtime.product_count == 3
    assert runtime.catalog == catalogue

    comparison = (
        build_balancing_point_manufacturer_valve_candidate_comparison_v1(
            _approved_duty(),
            catalogue,
        )
    )
    assert comparison.ready is True, comparison.status
    row = comparison.rows[0]
    assert row.compatible_candidate_count == 3
    assert row.premium_candidate_count == 1
    assert row.standard_candidate_count == 1
    assert row.budget_candidate_count == 1
    assert all(candidate.compatible for candidate in row.candidates)
    assert tuple(candidate.valve_ref for candidate in row.candidates) == (
        "DEMO-PREMIUM-DN20-KVS10",
        "DEMO-STANDARD-DN20-KVS10",
        "DEMO-BUDGET-DN20-KVS10",
    )
    assert "No product ranking or recommendation" in comparison.exclusions
    assert "No valve setting selected" in comparison.exclusions

    print(
        "OK — H-S64-G bundled fictional premium/standard/budget "
        "manufacturer valve demonstration catalogue passed."
    )


if __name__ == "__main__":
    main()
