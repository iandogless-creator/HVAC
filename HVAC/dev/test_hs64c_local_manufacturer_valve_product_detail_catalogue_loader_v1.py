# ======================================================================
# H-S64-C — Explicit local manufacturer valve product-detail loader
# ======================================================================

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1,
)
from HVAC.hydronics.proportioning.balancing_point_manufacturer_valve_candidate_comparison_v1 import (
    build_balancing_point_manufacturer_valve_candidate_comparison_v1,
)
from HVAC.hydronics_v3.catalogues.local_manufacturer_valve_product_detail_catalogue_loader_v1 import (
    LOCAL_MANUFACTURER_VALVE_PRODUCT_DETAIL_CATALOGUE_SCHEMA_V1,
    load_local_manufacturer_valve_product_detail_catalogue_v1,
)
from HVAC.hydronics_v3.dto.manufacturer_valve_product_detail_contract_v1 import (
    BUDGET_COST_BAND,
    PREMIUM_COST_BAND,
    STANDARD_COST_BAND,
    validate_manufacturer_valve_product_detail_catalog_v1,
)


def _product(
    valve_ref: str,
    cost_band_id: str,
    preset_kvs: tuple[float, ...],
) -> dict[str, object]:
    return {
        "valve_ref": valve_ref,
        "manufacturer_name": f"Example {cost_band_id.title()} Manufacturer",
        "product_family": "Example balancing valves",
        "model_name": f"Example {valve_ref}",
        "valve_type_id": "static_balancing_valve",
        "nominal_dn": 20,
        "connection_type": "threaded",
        "kvs_m3_h": 10.0,
        "preset_points": [
            {
                "setting_value": float(index),
                "kv_m3_h": kv,
            }
            for index, kv in enumerate(preset_kvs, start=1)
        ],
        "cost_band_id": cost_band_id,
        "note": "Test fixture product data only",
    }


def _payload() -> dict[str, object]:
    return {
        "schema": (
            LOCAL_MANUFACTURER_VALVE_PRODUCT_DETAIL_CATALOGUE_SCHEMA_V1
        ),
        "catalog_id": "local-manufacturer-fixture-v1",
        "catalog_revision": "fixture-2026-08-02",
        "products": [
            _product("PREMIUM-20", PREMIUM_COST_BAND, (3.0, 6.0, 10.0)),
            _product("STANDARD-20", STANDARD_COST_BAND, (4.0, 7.0, 10.0)),
            _product("BUDGET-20", BUDGET_COST_BAND, (2.0, 8.0, 10.0)),
        ],
    }


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _expect_value_error(
    path: Path,
    payload: object,
    expected: str,
) -> None:
    _write(path, payload)
    try:
        load_local_manufacturer_valve_product_detail_catalogue_v1(path)
    except ValueError as exc:
        assert expected in str(exc), str(exc)
    else:
        raise AssertionError(f"Expected ValueError containing: {expected}")


def _approved_duty():
    row = BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
        balancing_point_id="balancing-point:manufacturer-loader",
        ready=True,
        envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
        detailed_valve_design_required=True,
        envelope_available=True,
        approved_for_later_valve_design=True,
        catalog_id="generic-catalog-v1",
        valve_ref="GENERIC-KVS-10",
        current_kv_m3_h=10.0,
        required_kv=6.0,
    )
    return BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1(
        ready=True,
        rows=(row,),
    )


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "manufacturer_valves.json"
        payload = _payload()
        _write(path, payload)
        before = path.read_bytes()

        catalog = (
            load_local_manufacturer_valve_product_detail_catalogue_v1(path)
        )
        repeated = (
            load_local_manufacturer_valve_product_detail_catalogue_v1(path)
        )

        assert catalog == repeated
        assert path.read_bytes() == before
        assert catalog.catalog_id == "local-manufacturer-fixture-v1"
        assert catalog.catalog_revision == "fixture-2026-08-02"
        assert tuple(product.valve_ref for product in catalog.products) == (
            "PREMIUM-20",
            "STANDARD-20",
            "BUDGET-20",
        )
        assert tuple(product.cost_band_id for product in catalog.products) == (
            PREMIUM_COST_BAND,
            STANDARD_COST_BAND,
            BUDGET_COST_BAND,
        )
        assert all(product.nominal_dn == 20 for product in catalog.products)
        assert all(product.kvs_m3_h == 10.0 for product in catalog.products)
        assert isinstance(catalog.products[0].preset_points, tuple)
        assert catalog.products[0].preset_points[1].setting_value == 2.0
        assert catalog.products[0].preset_points[1].kv_m3_h == 6.0

        validation = validate_manufacturer_valve_product_detail_catalog_v1(
            catalog
        )
        assert validation.ready is True, validation.status
        assert validation.product_count == 3

        comparison = (
            build_balancing_point_manufacturer_valve_candidate_comparison_v1(
                _approved_duty(),
                catalog,
            )
        )
        assert comparison.ready is True, comparison.status
        comparison_row = comparison.rows[0]
        assert comparison_row.compatible_candidate_count == 3
        assert comparison_row.premium_candidate_count == 1
        assert comparison_row.standard_candidate_count == 1
        assert comparison_row.budget_candidate_count == 1
        assert tuple(
            candidate.valve_ref for candidate in comparison_row.candidates
        ) == (
            "PREMIUM-20",
            "STANDARD-20",
            "BUDGET-20",
        )

        _expect_value_error(path, [], "root must be an object")
        bad_schema = _payload()
        bad_schema["schema"] = "wrong"
        _expect_value_error(path, bad_schema, "schema must be")

        missing_revision = _payload()
        missing_revision["catalog_revision"] = ""
        _expect_value_error(
            path,
            missing_revision,
            "catalog_revision is required",
        )

        no_products = _payload()
        no_products["products"] = []
        _expect_value_error(path, no_products, "at least one products row")

        bad_dn = _payload()
        bad_dn["products"][0]["nominal_dn"] = True
        _expect_value_error(path, bad_dn, "positive integer")

        bad_points = _payload()
        bad_points["products"][0]["preset_points"] = []
        _expect_value_error(path, bad_points, "at least two rows")

        duplicate = _payload()
        duplicate["products"][1]["valve_ref"] = "PREMIUM-20"
        _expect_value_error(path, duplicate, "Duplicate valve_ref")

        invalid_band = _payload()
        invalid_band["products"][0]["cost_band_id"] = "luxury"
        _expect_value_error(path, invalid_band, "premium, standard or budget")

        descending_kv = _payload()
        descending_kv["products"][0]["preset_points"][1]["kv_m3_h"] = 1.0
        _expect_value_error(
            path,
            descending_kv,
            "preset Kv values must be strictly increasing",
        )

        path.write_text("{not-json", encoding="utf-8")
        try:
            load_local_manufacturer_valve_product_detail_catalogue_v1(path)
        except ValueError as exc:
            assert "JSON is invalid" in str(exc)
        else:
            raise AssertionError("Expected invalid JSON ValueError")

        missing_path = Path(temp_dir) / "missing.json"
        try:
            load_local_manufacturer_valve_product_detail_catalogue_v1(
                missing_path
            )
        except ValueError as exc:
            assert "cannot be read" in str(exc)
        else:
            raise AssertionError("Expected unreadable catalogue ValueError")

    print(
        "OK — H-S64-C explicit local manufacturer valve product-detail "
        "catalogue loader passed."
    )


if __name__ == "__main__":
    main()
