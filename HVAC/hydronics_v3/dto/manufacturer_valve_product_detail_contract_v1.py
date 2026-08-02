# ======================================================================
# H-S64-A — Manufacturer valve product-detail contract
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math


PREMIUM_COST_BAND = "premium"
STANDARD_COST_BAND = "standard"
BUDGET_COST_BAND = "budget"
VALID_COST_BANDS = frozenset({
    PREMIUM_COST_BAND,
    STANDARD_COST_BAND,
    BUDGET_COST_BAND,
})


@dataclass(frozen=True, slots=True)
class ManufacturerValvePresetPointV1:
    """One declared manufacturer preset position and its Kv evidence."""

    setting_value: float
    kv_m3_h: float


@dataclass(frozen=True, slots=True)
class ManufacturerValveProductDetailV1:
    """Exact product evidence; never a selected or recommended valve."""

    valve_ref: str
    manufacturer_name: str
    product_family: str
    model_name: str
    valve_type_id: str
    nominal_dn: int
    connection_type: str
    kvs_m3_h: float
    preset_points: tuple[ManufacturerValvePresetPointV1, ...]
    cost_band_id: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class ManufacturerValveProductDetailCatalogV1:
    """Versioned runtime catalogue of explicit manufacturer product data."""

    catalog_id: str
    catalog_revision: str
    products: tuple[ManufacturerValveProductDetailV1, ...]


@dataclass(frozen=True, slots=True)
class ManufacturerValveProductDetailContractValidationV1:
    schema: str = (
        "manufacturer_valve_product_detail_contract_validation_v1"
    )
    ready: bool = False
    catalog_id: str = ""
    catalog_revision: str = ""
    product_count: int = 0
    cost_band_ids: tuple[str, ...] = ()
    status: str = "Manufacturer valve product-detail contract not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No product ranking or recommendation",
        "No cost-band quality inference",
        "No valve product accepted or committed",
        "No valve setting selected",
        "No hydraulic mutation",
        "No ProjectState persistence",
    )
    note: str = (
        "Cost band is declared catalogue metadata only; it is not an "
        "engineering or quality classification."
    )


def validate_manufacturer_valve_product_detail_catalog_v1(
    catalog: object,
) -> ManufacturerValveProductDetailContractValidationV1:
    """Validate one immutable product-detail contract deterministically."""

    if not isinstance(catalog, ManufacturerValveProductDetailCatalogV1):
        return _blocked_v1(
            "ManufacturerValveProductDetailCatalogV1 required"
        )

    catalog_id = _stable_text_v1(catalog.catalog_id)
    revision = _stable_text_v1(catalog.catalog_revision)
    products = catalog.products
    blockers: list[str] = []

    if not catalog_id:
        blockers.append("catalog_id is required")
    if not revision:
        blockers.append("catalog_revision is required")
    if not isinstance(products, tuple) or not products:
        blockers.append("products must be a non-empty tuple")
        products = ()

    seen_refs: set[str] = set()
    cost_bands: list[str] = []
    for index, product in enumerate(products, start=1):
        prefix = f"Product {index}"
        if not isinstance(product, ManufacturerValveProductDetailV1):
            blockers.append(
                f"{prefix} must be ManufacturerValveProductDetailV1"
            )
            continue

        valve_ref = _stable_text_v1(product.valve_ref)
        if not valve_ref:
            blockers.append(f"{prefix} valve_ref is required")
        elif valve_ref in seen_refs:
            blockers.append(f"Duplicate valve_ref: {valve_ref}")
        else:
            seen_refs.add(valve_ref)
            prefix = valve_ref

        required_text = (
            ("manufacturer_name", product.manufacturer_name),
            ("product_family", product.product_family),
            ("model_name", product.model_name),
            ("valve_type_id", product.valve_type_id),
            ("connection_type", product.connection_type),
        )
        for field_name, value in required_text:
            if not _stable_text_v1(value):
                blockers.append(f"{prefix}: {field_name} is required")

        if (
            isinstance(product.nominal_dn, bool)
            or not isinstance(product.nominal_dn, int)
            or product.nominal_dn <= 0
        ):
            blockers.append(f"{prefix}: nominal_dn must be a positive integer")

        kvs = _positive_finite_v1(product.kvs_m3_h)
        if kvs is None:
            blockers.append(f"{prefix}: kvs_m3_h must be positive and finite")

        cost_band = _stable_text_v1(product.cost_band_id).casefold()
        if cost_band not in VALID_COST_BANDS:
            blockers.append(
                f"{prefix}: cost_band_id must be premium, standard or budget"
            )
        elif cost_band not in cost_bands:
            cost_bands.append(cost_band)

        points = product.preset_points
        if not isinstance(points, tuple) or len(points) < 2:
            blockers.append(
                f"{prefix}: at least two preset_points are required as a tuple"
            )
            continue

        previous_setting: float | None = None
        previous_kv: float | None = None
        for point_index, point in enumerate(points, start=1):
            if not isinstance(point, ManufacturerValvePresetPointV1):
                blockers.append(
                    f"{prefix}: preset point {point_index} has invalid type"
                )
                continue
            setting = _positive_finite_v1(point.setting_value)
            kv = _positive_finite_v1(point.kv_m3_h)
            if setting is None:
                blockers.append(
                    f"{prefix}: preset point {point_index} setting must be "
                    "positive and finite"
                )
            if kv is None:
                blockers.append(
                    f"{prefix}: preset point {point_index} Kv must be "
                    "positive and finite"
                )
            if setting is not None and previous_setting is not None:
                if setting <= previous_setting:
                    blockers.append(
                        f"{prefix}: preset settings must be strictly increasing"
                    )
            if kv is not None and previous_kv is not None:
                if kv <= previous_kv:
                    blockers.append(
                        f"{prefix}: preset Kv values must be strictly increasing"
                    )
            if kv is not None and kvs is not None and kv > kvs:
                blockers.append(
                    f"{prefix}: preset Kv must not exceed product Kvs"
                )
            if setting is not None:
                previous_setting = setting
            if kv is not None:
                previous_kv = kv

    clean = _unique_v1(tuple(blockers))
    ready = bool(catalog_id and revision and products and not clean)
    return ManufacturerValveProductDetailContractValidationV1(
        ready=ready,
        catalog_id=catalog_id,
        catalog_revision=revision,
        product_count=len(products),
        cost_band_ids=tuple(cost_bands),
        status=(
            "Ready — manufacturer valve product-detail contract validated"
            if ready
            else "Blocked — " + "; ".join(clean)
        ),
        blockers=clean,
    )


def _blocked_v1(
    *blockers: str,
) -> ManufacturerValveProductDetailContractValidationV1:
    clean = _unique_v1(tuple(blockers))
    return ManufacturerValveProductDetailContractValidationV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
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
    return number if math.isfinite(number) and number > 0.0 else None


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)
