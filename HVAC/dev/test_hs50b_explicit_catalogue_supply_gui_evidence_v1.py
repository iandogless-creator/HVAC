from pathlib import Path

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_point_valve_catalogue_candidate_match_evidence_v1 import (
    build_balancing_point_valve_catalogue_candidate_match_evidence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_criteria_intent_v1 import (
    PRODUCT_SEARCH_CRITERIA_AVAILABLE,
    ResolvedPointValveProductSearchCriteriaRowV1,
    ResolvedPointValveProductSearchCriteriaV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
    BalancingPointValveProductSearchDutyEnvelopeRowV1,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)
from HVAC.hydronics_v3.dto.valve_catalog_dto import (
    ValveCatalogDTO,
    ValveKvOptionDTO,
)


class Stub:
    pass


def main() -> None:
    catalog = ValveCatalogDTO(
        catalog_id="catalog-v1",
        kv_options=[
            ValveKvOptionDTO("VALVE-B", 10.1, "second"),
            ValveKvOptionDTO("VALVE-A", 9.9, "first"),
        ],
    )
    stub = Stub()
    refreshes = []
    stub.refresh = lambda: refreshes.append(True)
    HydronicsSchematicPanelAdapter.supply_valve_catalog_dto_v1(stub, catalog)
    supplied = stub._supplied_valve_catalog_dto_v1
    assert supplied is not catalog
    assert supplied.catalog_id == "catalog-v1"
    assert supplied.kv_options is not catalog.kv_options
    assert refreshes == [True]
    HydronicsSchematicPanelAdapter.supply_valve_catalog_dto_v1(stub, None)
    assert stub._supplied_valve_catalog_dto_v1 is None
    assert refreshes == [True, True]

    point_id = "balancing-point:approved"
    envelopes = BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=True,
        rows=(BalancingPointValveProductSearchDutyEnvelopeRowV1(
            balancing_point_id=point_id,
            ready=True,
            envelope_state_id=PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
            product_search_required=True,
            envelope_available=True,
            approved_for_product_search=True,
            accepted_kvs=10.0,
        ),),
    )
    criteria = ResolvedPointValveProductSearchCriteriaV1(
        ready=True,
        rows=(ResolvedPointValveProductSearchCriteriaRowV1(
            balancing_point_id=point_id,
            ready=True,
            criteria_state_id=PRODUCT_SEARCH_CRITERIA_AVAILABLE,
            criteria_available=True,
            accepted_kvs_basis=10.0,
            catalog_id="catalog-v1",
            kv_tolerance_percent=2.0,
        ),),
    )
    evidence = build_balancing_point_valve_catalogue_candidate_match_evidence_v1(
        envelopes, criteria, catalog
    )
    rows = HydronicsSchematicPanelAdapter._build_catalogue_candidate_match_gui_rows_v1(
        evidence
    )
    assert [row["valve_ref"] for row in rows] == ["VALVE-B", "VALVE-A"]
    assert rows[0]["deviation"] == "1.00%"
    assert all(row["ready"] == "Yes" for row in rows)

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()
    supply_start = adapter_source.index("    def supply_valve_catalog_dto_v1(")
    supply_end = adapter_source.index("    def set_product_search_criteria(", supply_start)
    supply_source = adapter_source[supply_start:supply_end]
    assert "ProjectState" in supply_source
    assert "No ProjectState field is" in supply_source
    assert "mark_dirty" not in supply_source
    assert "project." not in supply_source
    assert "build_balancing_point_valve_catalogue_candidate_match_evidence_v1(" in adapter_source
    assert "set_catalogue_candidate_match_rows" in adapter_source
    assert "Valve catalogue candidate-match evidence — read-only" in panel_source
    assert "): 1300" in panel_source

    print("OK — H-S50-B explicit catalogue supply and GUI evidence passed.")


if __name__ == "__main__":
    main()
