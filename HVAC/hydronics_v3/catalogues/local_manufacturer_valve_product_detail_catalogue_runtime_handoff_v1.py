# ======================================================================
# H-S64-D — Local manufacturer catalogue runtime handoff
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from HVAC.hydronics_v3.catalogues.local_manufacturer_valve_product_detail_catalogue_loader_v1 import (
    load_local_manufacturer_valve_product_detail_catalogue_v1,
)
from HVAC.hydronics_v3.dto.manufacturer_valve_product_detail_contract_v1 import (
    ManufacturerValveProductDetailCatalogV1,
)


@dataclass(frozen=True, slots=True)
class LocalManufacturerValveProductDetailCatalogueRuntimeHandoffV1:
    schema: str = (
        "local_manufacturer_valve_product_detail_catalogue_"
        "runtime_handoff_v1"
    )
    ready: bool = False
    source_supplied: bool = False
    source_path: str = ""
    catalog: ManufacturerValveProductDetailCatalogV1 | None = None
    catalog_id: str = ""
    catalog_revision: str = ""
    product_count: int = 0
    status: str = (
        "Local manufacturer valve product-detail catalogue unavailable"
    )
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No bundled manufacturer product data",
        "No ProjectState persistence",
        "No automatic file watching or reload",
        "No product ranking or recommendation",
        "No valve product accepted or committed",
        "No valve setting selected",
        "No hydraulic mutation",
    )
    note: str = (
        "The supplied path is session-only runtime evidence. Re-supply the "
        "path explicitly to reload changed file contents."
    )


def build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1(
    path: str | Path | None,
) -> LocalManufacturerValveProductDetailCatalogueRuntimeHandoffV1:
    """Load or clear one explicit session-only manufacturer catalogue."""

    if path is None or (isinstance(path, str) and not path.strip()):
        blocker = (
            "Explicit local manufacturer valve product-detail catalogue "
            "path is required"
        )
        return LocalManufacturerValveProductDetailCatalogueRuntimeHandoffV1(
            ready=False,
            source_supplied=False,
            status="Unavailable — " + blocker,
            blockers=(blocker,),
        )

    try:
        source_path = Path(path).expanduser()
    except TypeError:
        blocker = (
            "Local manufacturer valve product-detail catalogue path must "
            "be text or Path"
        )
        return LocalManufacturerValveProductDetailCatalogueRuntimeHandoffV1(
            ready=False,
            source_supplied=True,
            status="Blocked — " + blocker,
            blockers=(blocker,),
        )

    source_text = str(source_path)
    try:
        catalog = (
            load_local_manufacturer_valve_product_detail_catalogue_v1(
                source_path
            )
        )
    except ValueError as exc:
        blocker = str(exc).strip() or (
            "Local manufacturer valve product-detail catalogue could not "
            "be loaded"
        )
        return LocalManufacturerValveProductDetailCatalogueRuntimeHandoffV1(
            ready=False,
            source_supplied=True,
            source_path=source_text,
            status="Blocked — " + blocker,
            blockers=(blocker,),
        )

    return LocalManufacturerValveProductDetailCatalogueRuntimeHandoffV1(
        ready=True,
        source_supplied=True,
        source_path=source_text,
        catalog=catalog,
        catalog_id=catalog.catalog_id,
        catalog_revision=catalog.catalog_revision,
        product_count=len(catalog.products),
        status=(
            "Ready — explicit local manufacturer valve product-detail "
            f"catalogue loaded; {len(catalog.products)} product(s); "
            "comparison evidence only"
        ),
    )
