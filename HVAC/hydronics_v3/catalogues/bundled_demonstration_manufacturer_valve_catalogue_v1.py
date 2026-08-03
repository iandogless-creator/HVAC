# ======================================================================
# H-S64-G — Bundled demonstration manufacturer valve catalogue
# ======================================================================

from __future__ import annotations

from pathlib import Path

from HVAC.hydronics_v3.catalogues.local_manufacturer_valve_product_detail_catalogue_loader_v1 import (
    load_local_manufacturer_valve_product_detail_catalogue_v1,
)
from HVAC.hydronics_v3.dto.manufacturer_valve_product_detail_contract_v1 import (
    ManufacturerValveProductDetailCatalogV1,
)


BUNDLED_DEMONSTRATION_MANUFACTURER_VALVE_CATALOGUE_PATH_V1 = (
    Path(__file__).with_name(
        "bundled_demonstration_manufacturer_valve_catalogue_v1.json"
    )
)


def load_bundled_demonstration_manufacturer_valve_catalogue_v1(
) -> ManufacturerValveProductDetailCatalogV1:
    """Load fictional comparison evidence shipped for workflow demonstration."""

    return load_local_manufacturer_valve_product_detail_catalogue_v1(
        BUNDLED_DEMONSTRATION_MANUFACTURER_VALVE_CATALOGUE_PATH_V1
    )
