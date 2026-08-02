# ======================================================================
# H-S64-A — Manufacturer valve product-detail contract
# ======================================================================

from dataclasses import FrozenInstanceError, replace

from HVAC.hydronics_v3.dto.manufacturer_valve_product_detail_contract_v1 import (
    BUDGET_COST_BAND,
    PREMIUM_COST_BAND,
    STANDARD_COST_BAND,
    ManufacturerValvePresetPointV1,
    ManufacturerValveProductDetailCatalogV1,
    ManufacturerValveProductDetailV1,
    validate_manufacturer_valve_product_detail_catalog_v1,
)


def _product(
    valve_ref: str,
    cost_band_id: str,
    *,
    nominal_dn: int = 20,
    kvs_m3_h: float = 10.0,
    preset_points: tuple[ManufacturerValvePresetPointV1, ...] | None = None,
) -> ManufacturerValveProductDetailV1:
    return ManufacturerValveProductDetailV1(
        valve_ref=valve_ref,
        manufacturer_name="Example manufacturer",
        product_family="Example balancing range",
        model_name=valve_ref,
        valve_type_id="manual_balancing_valve",
        nominal_dn=nominal_dn,
        connection_type="female_threaded",
        kvs_m3_h=kvs_m3_h,
        preset_points=(
            preset_points
            if preset_points is not None
            else (
                ManufacturerValvePresetPointV1(1.0, 1.0),
                ManufacturerValvePresetPointV1(2.0, 2.8),
                ManufacturerValvePresetPointV1(3.0, 5.7),
                ManufacturerValvePresetPointV1(4.0, 10.0),
            )
        ),
        cost_band_id=cost_band_id,
        note="Declared product evidence only",
    )


def _catalog(*products) -> ManufacturerValveProductDetailCatalogV1:
    return ManufacturerValveProductDetailCatalogV1(
        catalog_id="manufacturer-valve-products-v1",
        catalog_revision="2026-08-02",
        products=tuple(products),
    )


def main() -> None:
    premium = _product("PREMIUM-DN20", PREMIUM_COST_BAND)
    standard = _product("STANDARD-DN20", STANDARD_COST_BAND)
    budget = _product("BUDGET-DN20", BUDGET_COST_BAND)
    catalog = _catalog(premium, standard, budget)

    before = repr(catalog)
    result = validate_manufacturer_valve_product_detail_catalog_v1(
        catalog
    )
    repeated = validate_manufacturer_valve_product_detail_catalog_v1(
        catalog
    )
    assert result == repeated
    assert repr(catalog) == before
    assert result.ready is True, result.status
    assert result.catalog_id == "manufacturer-valve-products-v1"
    assert result.catalog_revision == "2026-08-02"
    assert result.product_count == 3
    assert result.cost_band_ids == (
        PREMIUM_COST_BAND,
        STANDARD_COST_BAND,
        BUDGET_COST_BAND,
    )
    assert "No product ranking or recommendation" in result.exclusions
    assert "No cost-band quality inference" in result.exclusions
    assert "No valve product accepted or committed" in result.exclusions
    assert "No valve setting selected" in result.exclusions
    assert "No ProjectState persistence" in result.exclusions
    assert "metadata only" in result.note

    try:
        premium.nominal_dn = 25
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Product detail contract must be immutable")

    duplicate = validate_manufacturer_valve_product_detail_catalog_v1(
        _catalog(premium, replace(standard, valve_ref=premium.valve_ref))
    )
    assert duplicate.ready is False
    assert "Duplicate valve_ref" in duplicate.status

    invalid_band = validate_manufacturer_valve_product_detail_catalog_v1(
        _catalog(replace(premium, cost_band_id="best"))
    )
    assert invalid_band.ready is False
    assert "premium, standard or budget" in invalid_band.status

    incomplete_identity = (
        validate_manufacturer_valve_product_detail_catalog_v1(
            _catalog(replace(premium, manufacturer_name="", nominal_dn=0))
        )
    )
    assert incomplete_identity.ready is False
    assert "manufacturer_name is required" in incomplete_identity.status
    assert "nominal_dn must be a positive integer" in (
        incomplete_identity.status
    )

    too_few_points = validate_manufacturer_valve_product_detail_catalog_v1(
        _catalog(
            replace(
                premium,
                preset_points=(
                    ManufacturerValvePresetPointV1(1.0, 1.0),
                ),
            )
        )
    )
    assert too_few_points.ready is False
    assert "at least two preset_points" in too_few_points.status

    unordered = validate_manufacturer_valve_product_detail_catalog_v1(
        _catalog(
            _product(
                "UNORDERED-DN20",
                STANDARD_COST_BAND,
                preset_points=(
                    ManufacturerValvePresetPointV1(2.0, 3.0),
                    ManufacturerValvePresetPointV1(1.0, 2.0),
                ),
            )
        )
    )
    assert unordered.ready is False
    assert "settings must be strictly increasing" in unordered.status
    assert "Kv values must be strictly increasing" in unordered.status

    above_kvs = validate_manufacturer_valve_product_detail_catalog_v1(
        _catalog(
            _product(
                "ABOVE-KVS-DN20",
                BUDGET_COST_BAND,
                kvs_m3_h=5.0,
                preset_points=(
                    ManufacturerValvePresetPointV1(1.0, 2.0),
                    ManufacturerValvePresetPointV1(2.0, 6.0),
                ),
            )
        )
    )
    assert above_kvs.ready is False
    assert "preset Kv must not exceed product Kvs" in above_kvs.status

    wrong_type = validate_manufacturer_valve_product_detail_catalog_v1(
        object()
    )
    assert wrong_type.ready is False
    assert "ManufacturerValveProductDetailCatalogV1 required" in (
        wrong_type.status
    )

    print(
        "OK — H-S64-A manufacturer valve product-detail contract passed."
    )


if __name__ == "__main__":
    main()
