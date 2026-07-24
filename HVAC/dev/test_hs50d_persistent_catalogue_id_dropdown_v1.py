# ======================================================================
# H-S50-D — Persistent catalogue-ID dropdown
# ======================================================================

from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


def main() -> None:
    point_id = "balancing-point:subleg:test"
    envelope = SimpleNamespace(
        balancing_point_id=point_id,
        envelope_available=True,
        approved_for_product_search=True,
        point_scope="subleg",
        point_role="common_route_downstream",
        accepted_kvs=10.0,
    )
    resolved = SimpleNamespace(
        balancing_point_id=point_id,
        catalog_id="local-generic-valves-v1",
        kv_tolerance_percent=1.0,
        valve_ref_contains="LOCAL",
        note_contains="generic",
        criteria_available=True,
        status="Manual product-search criteria available",
        blockers=(),
    )
    rows = (
        HydronicsSchematicPanelAdapter
        ._build_product_search_criteria_editor_rows_v1(
            SimpleNamespace(rows=(envelope,)),
            SimpleNamespace(rows=(resolved,)),
            available_catalog_ids=(
                "",
                "local-generic-valves-v1",
                "local-generic-valves-v1",
            ),
        )
    )
    assert len(rows) == 1
    assert rows[0]["catalog_id"] == "local-generic-valves-v1"
    assert rows[0]["available_catalog_ids"] == (
        "local-generic-valves-v1",
    )

    pending_rows = (
        HydronicsSchematicPanelAdapter
        ._build_product_search_criteria_editor_rows_v1(
            SimpleNamespace(rows=(envelope,)),
            SimpleNamespace(rows=()),
            available_catalog_ids=("local-generic-valves-v1",),
        )
    )
    assert pending_rows[0]["catalog_id"] == ""
    assert pending_rows[0]["available_catalog_ids"] == (
        "local-generic-valves-v1",
    )

    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert "_product_search_criteria_catalog_id_combo = QComboBox" in panel_source
    assert "_product_search_criteria_catalog_id_edit" not in panel_source
    assert 'currentData()' in panel_source
    assert 'selected_catalog_id = (' in panel_source
    assert 'saved_catalog_id' in panel_source
    assert 'if len(available_catalog_ids) == 1' in panel_source
    assert '— unavailable' in panel_source

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert '"available_catalog_ids": clean_catalog_ids' in adapter_source
    assert '"_supplied_valve_catalog_dto_v1"' in adapter_source

    print("OK — H-S50-D persistent catalogue-ID dropdown passed.")


if __name__ == "__main__":
    main()
