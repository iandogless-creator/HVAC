# ======================================================================
# H-S64-C — Explicit local manufacturer valve product-detail loader
# ======================================================================

from __future__ import annotations

import json
import math
from pathlib import Path

from HVAC.hydronics_v3.dto.manufacturer_valve_product_detail_contract_v1 import (
    ManufacturerValvePresetPointV1,
    ManufacturerValveProductDetailCatalogV1,
    ManufacturerValveProductDetailV1,
    validate_manufacturer_valve_product_detail_catalog_v1,
)


LOCAL_MANUFACTURER_VALVE_PRODUCT_DETAIL_CATALOGUE_SCHEMA_V1 = (
    "local_manufacturer_valve_product_detail_catalogue_v1"
)


def load_local_manufacturer_valve_product_detail_catalogue_v1(
    path: str | Path,
) -> ManufacturerValveProductDetailCatalogV1:
    """Load explicit manufacturer data as immutable comparison evidence."""

    source_path = Path(path)
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            "Local manufacturer valve product-detail catalogue cannot be "
            f"read: {source_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Local manufacturer valve product-detail catalogue JSON is "
            f"invalid: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise ValueError(
            "Local manufacturer valve product-detail catalogue root must "
            "be an object"
        )
    schema = _required_text_v1(raw.get("schema"), "schema")
    if schema != (
        LOCAL_MANUFACTURER_VALVE_PRODUCT_DETAIL_CATALOGUE_SCHEMA_V1
    ):
        raise ValueError(
            "Local manufacturer valve product-detail catalogue schema must "
            "be "
            + LOCAL_MANUFACTURER_VALVE_PRODUCT_DETAIL_CATALOGUE_SCHEMA_V1
        )

    catalog_id = _required_text_v1(raw.get("catalog_id"), "catalog_id")
    revision = _required_text_v1(
        raw.get("catalog_revision"),
        "catalog_revision",
    )
    raw_products = raw.get("products")
    if not isinstance(raw_products, list) or not raw_products:
        raise ValueError(
            "Local manufacturer valve product-detail catalogue requires "
            "at least one products row"
        )

    products = tuple(
        _load_product_v1(raw_product, index=index)
        for index, raw_product in enumerate(raw_products, start=1)
    )
    catalog = ManufacturerValveProductDetailCatalogV1(
        catalog_id=catalog_id,
        catalog_revision=revision,
        products=products,
    )
    validation = validate_manufacturer_valve_product_detail_catalog_v1(
        catalog
    )
    if not validation.ready:
        raise ValueError(
            "Local manufacturer valve product-detail catalogue violates "
            "H-S64-A: "
            + "; ".join(validation.blockers)
        )
    return catalog


def _load_product_v1(
    raw: object,
    *,
    index: int,
) -> ManufacturerValveProductDetailV1:
    prefix = f"Product {index}"
    if not isinstance(raw, dict):
        raise ValueError(f"{prefix} must be an object")

    valve_ref = _required_text_v1(
        raw.get("valve_ref"),
        f"{prefix} valve_ref",
    )
    raw_points = raw.get("preset_points")
    if not isinstance(raw_points, list) or len(raw_points) < 2:
        raise ValueError(
            f"{valve_ref}: preset_points must contain at least two rows"
        )
    preset_points = tuple(
        _load_preset_point_v1(
            raw_point,
            valve_ref=valve_ref,
            index=point_index,
        )
        for point_index, raw_point in enumerate(raw_points, start=1)
    )

    return ManufacturerValveProductDetailV1(
        valve_ref=valve_ref,
        manufacturer_name=_required_text_v1(
            raw.get("manufacturer_name"),
            f"{valve_ref} manufacturer_name",
        ),
        product_family=_required_text_v1(
            raw.get("product_family"),
            f"{valve_ref} product_family",
        ),
        model_name=_required_text_v1(
            raw.get("model_name"),
            f"{valve_ref} model_name",
        ),
        valve_type_id=_required_text_v1(
            raw.get("valve_type_id"),
            f"{valve_ref} valve_type_id",
        ),
        nominal_dn=_positive_int_v1(
            raw.get("nominal_dn"),
            f"{valve_ref} nominal_dn",
        ),
        connection_type=_required_text_v1(
            raw.get("connection_type"),
            f"{valve_ref} connection_type",
        ),
        kvs_m3_h=_positive_finite_v1(
            raw.get("kvs_m3_h"),
            f"{valve_ref} kvs_m3_h",
        ),
        preset_points=preset_points,
        cost_band_id=_required_text_v1(
            raw.get("cost_band_id"),
            f"{valve_ref} cost_band_id",
        ).casefold(),
        note=str(raw.get("note") or "").strip(),
    )


def _load_preset_point_v1(
    raw: object,
    *,
    valve_ref: str,
    index: int,
) -> ManufacturerValvePresetPointV1:
    prefix = f"{valve_ref}: preset point {index}"
    if not isinstance(raw, dict):
        raise ValueError(f"{prefix} must be an object")
    return ManufacturerValvePresetPointV1(
        setting_value=_positive_finite_v1(
            raw.get("setting_value"),
            f"{prefix} setting_value",
        ),
        kv_m3_h=_positive_finite_v1(
            raw.get("kv_m3_h"),
            f"{prefix} kv_m3_h",
        ),
    )


def _required_text_v1(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _positive_int_v1(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _positive_finite_v1(value: object, field_name: str) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field_name} must be positive and finite")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be positive and finite"
        ) from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{field_name} must be positive and finite")
    return number
