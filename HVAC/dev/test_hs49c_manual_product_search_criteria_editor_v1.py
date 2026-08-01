from pathlib import Path

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
    BalancingPointValveProductSearchDutyEnvelopeRowV1,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)
from HVAC.project.project_state import ProjectState


class Stub:
    pass


def main() -> None:
    point_id = "balancing-point:main:leg-002"
    envelope = BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=True,
        rows=(BalancingPointValveProductSearchDutyEnvelopeRowV1(
            balancing_point_id=point_id,
            point_scope="main",
            point_role="common_main_takeoff",
            topology="Shared",
            governed_route_ids=("route-1", "route-2"),
            ready=True,
            envelope_state_id=PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
            product_search_required=True,
            envelope_available=True,
            approved_for_product_search=True,
            point_flow_kg_s=0.125,
            flow_m3_h=0.4509,
            required_kv=2.91,
            accepted_kvs=10.0,
            kvs_series_id="generic_preferred_kvs_series_v1",
            implied_valve_dp_bar=0.0020331,
            implied_valve_dp_pa=203.31,
            controlled_circuit_dp_pa=12600.0,
            implied_authority=203.31 / (203.31 + 12600.0),
            design_valve_dp_pa=2400.0,
            design_authority=2400.0 / (2400.0 + 12600.0),
        ),),
    )
    stub = Stub()
    stub._project_state = ProjectState(project_id="hs49c", name="H-S49-C")
    stub._context = Stub()
    stub._balancing_point_valve_product_search_duty_envelope_preview = envelope
    refreshes = []
    stub.refresh = lambda: refreshes.append(True)

    HydronicsSchematicPanelAdapter.set_product_search_criteria(stub, {
        "action": "set",
        "balancing_point_id": point_id,
        "catalog_id": "catalog-v1",
        "kv_tolerance_percent": 5.0,
        "valve_ref_contains": "STAD",
        "note_contains": "ports",
    })
    intent = stub._project_state.hydronic_point_valve_product_search_criteria_intent
    assert intent is not None
    entry = intent.criteria_by_point_id[point_id]
    assert entry.accepted_kvs_basis == 10.0
    assert entry.catalog_id == "catalog-v1"
    assert entry.kv_tolerance_percent == 5.0
    assert entry.valve_ref_contains == "STAD"
    assert len(entry.duty_envelope_fingerprint) == 64
    assert refreshes

    HydronicsSchematicPanelAdapter.set_product_search_criteria(stub, {
        "action": "clear",
        "balancing_point_id": point_id,
    })
    assert point_id not in intent.criteria_by_point_id

    adapter = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    panel = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py").read_text()
    assert "set_product_search_criteria_callback" in adapter
    assert "resolve_balancing_point_valve_product_search_criteria_v1(" in adapter
    assert "set_product_search_criteria_editor_rows" in adapter
    assert "Manual valve product-search criteria — design intent" in panel
    assert "Apply does not query" in panel
    assert "_product_search_criteria_catalog_id_combo" in panel
    assert "_product_search_criteria_tolerance_spin" in panel
    assert "_product_search_criteria_ref_edit" in panel
    assert "_product_search_criteria_note_edit" in panel
    assert '"Manual valve product-search criteria — design intent"' in panel
    assert "): 1200" in panel

    print("OK — H-S49-C manual valve product-search criteria editor passed.")


if __name__ == "__main__":
    main()
