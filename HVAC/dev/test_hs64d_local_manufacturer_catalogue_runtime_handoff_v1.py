# ======================================================================
# H-S64-D — Local manufacturer catalogue runtime handoff
# ======================================================================

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.hydronics_v3.catalogues.local_manufacturer_valve_product_detail_catalogue_loader_v1 import (
    LOCAL_MANUFACTURER_VALVE_PRODUCT_DETAIL_CATALOGUE_SCHEMA_V1,
)
from HVAC.hydronics_v3.catalogues.local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1 import (
    build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1,
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
        "catalog_id": "runtime-manufacturer-fixture-v1",
        "catalog_revision": "fixture-2026-08-02",
        "products": [
            _product("PREMIUM-20", "premium", (3.0, 6.0, 10.0)),
            _product("STANDARD-20", "standard", (4.0, 7.0, 10.0)),
            _product("BUDGET-20", "budget", (2.0, 8.0, 10.0)),
        ],
    }


def main() -> None:
    unavailable = (
        build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1(
            None
        )
    )
    assert unavailable.ready is False
    assert unavailable.source_supplied is False
    assert unavailable.catalog is None
    assert "path is required" in unavailable.status
    assert (
        "No bundled real manufacturer product data"
        in unavailable.exclusions
    )
    assert "No ProjectState persistence" in unavailable.exclusions
    assert "No valve setting selected" in unavailable.exclusions

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "manufacturer_valves.json"
        path.write_text(json.dumps(_payload()), encoding="utf-8")
        before = path.read_bytes()

        loaded = (
            build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1(
                path
            )
        )
        repeated = (
            build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1(
                path
            )
        )
        assert loaded == repeated
        assert path.read_bytes() == before
        assert loaded.ready is True, loaded.status
        assert loaded.source_supplied is True
        assert loaded.source_path == str(path)
        assert loaded.catalog is not None
        assert loaded.catalog_id == "runtime-manufacturer-fixture-v1"
        assert loaded.catalog_revision == "fixture-2026-08-02"
        assert loaded.product_count == 3
        assert tuple(product.valve_ref for product in loaded.catalog.products) == (
            "PREMIUM-20",
            "STANDARD-20",
            "BUDGET-20",
        )

        path.write_text("{invalid-json", encoding="utf-8")
        blocked = (
            build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1(
                path,
            )
        )
        assert blocked.ready is False
        assert blocked.source_supplied is True
        assert blocked.catalog is None
        assert "JSON is invalid" in blocked.status

        cleared = (
            build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1(
                None,
            )
        )
        assert cleared.ready is False
        assert cleared.source_supplied is False
        assert cleared.catalog is None

    bad_type = (
        build_local_manufacturer_valve_product_detail_catalogue_runtime_handoff_v1(
            True
        )
    )
    assert bad_type.ready is False
    assert "text or Path" in bad_type.status

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    supply_start = adapter_source.index(
        "    def supply_local_manufacturer_valve_product_detail_"
        "catalogue_path_v1("
    )
    supply_end = adapter_source.index(
        "    def set_product_search_criteria(",
        supply_start,
    )
    supply_source = adapter_source[supply_start:supply_end]
    assert "No path or catalogue content is written to ProjectState" in (
        supply_source
    )
    assert "mark_dirty" not in supply_source
    assert "project." not in supply_source
    assert "self._project_state" not in supply_source
    assert (
        "self._local_manufacturer_valve_product_detail_catalogue_runtime_v1"
        in supply_source
    )
    assert "self.refresh()" in supply_source
    assert "return runtime" in supply_source
    assert (
        "build_balancing_point_manufacturer_valve_candidate_comparison_v1("
        in adapter_source
    )
    refresh_start = adapter_source.index("    def refresh(self) -> None:")
    duty_build = adapter_source.index(
        "build_balancing_point_approved_valve_candidate_design_duty_envelope_v1(",
        refresh_start,
    )
    comparison_build = adapter_source.index(
        "build_balancing_point_manufacturer_valve_candidate_comparison_v1(",
        duty_build,
    )
    assert duty_build < comparison_build
    comparison_source = adapter_source[
        comparison_build:comparison_build + 900
    ]
    assert 'manufacturer_catalogue_runtime,\n                        "catalog"' in (
        comparison_source
    )
    assert (
        "_balancing_point_manufacturer_valve_candidate_comparison_preview_v1"
        in adapter_source
    )

    print(
        "OK — H-S64-D local manufacturer catalogue session-only runtime "
        "handoff passed."
    )


if __name__ == "__main__":
    main()
