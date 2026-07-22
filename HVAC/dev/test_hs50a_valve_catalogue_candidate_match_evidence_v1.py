from HVAC.hydronics.proportioning.balancing_point_valve_catalogue_candidate_match_evidence_v1 import (
    CATALOGUE_MATCH_EVIDENCE_AVAILABLE,
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


def main() -> None:
    point_id = "balancing-point:subleg:approved"
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
            kv_tolerance_percent=5.0,
            valve_ref_contains="stad",
            note_contains="ports",
            status="Manual product-search criteria available — search not executed",
        ),),
    )
    catalog = ValveCatalogDTO(
        catalog_id="catalog-v1",
        kv_options=[
            ValveKvOptionDTO("STAD-10.2", 10.2, "Commissioning ports"),
            ValveKvOptionDTO("STAD-9.8", 9.8, "Ports and drain"),
            ValveKvOptionDTO("OTHER-10", 10.0, "Commissioning ports"),
            ValveKvOptionDTO("STAD-16", 16.0, "Commissioning ports"),
        ],
    )
    result = build_balancing_point_valve_catalogue_candidate_match_evidence_v1(
        envelopes, criteria, catalog
    )
    assert result.ready is True
    row = result.rows[0]
    assert row.match_state_id == CATALOGUE_MATCH_EVIDENCE_AVAILABLE
    assert row.match_evidence_available is True
    assert [item.valve_ref for item in row.candidates] == [
        "STAD-10.2", "STAD-9.8"
    ]
    assert round(row.candidates[0].kv_deviation_percent, 3) == 2.0
    assert "supplied order retained" in row.status
    assert "No candidate ranking or recommendation" in result.exclusions
    assert "No valve product selected" in result.exclusions

    no_match_catalog = ValveCatalogDTO(
        catalog_id="catalog-v1",
        kv_options=[ValveKvOptionDTO("STAD-16", 16.0, "ports")],
    )
    no_match = build_balancing_point_valve_catalogue_candidate_match_evidence_v1(
        envelopes, criteria, no_match_catalog
    )
    assert no_match.ready is True
    assert no_match.rows[0].candidates == ()
    assert "No catalogue candidates match" in no_match.rows[0].status

    wrong_catalog = ValveCatalogDTO(
        catalog_id="other-catalog",
        kv_options=[ValveKvOptionDTO("STAD-10", 10.0, "ports")],
    )
    blocked = build_balancing_point_valve_catalogue_candidate_match_evidence_v1(
        envelopes, criteria, wrong_catalog
    )
    assert blocked.ready is False
    assert "does not match" in blocked.rows[0].blockers[0]

    invalid_catalog = ValveCatalogDTO(
        catalog_id="catalog-v1",
        kv_options=[ValveKvOptionDTO("bad", 0.0)],
    )
    invalid = build_balancing_point_valve_catalogue_candidate_match_evidence_v1(
        envelopes, criteria, invalid_catalog
    )
    assert invalid.ready is False
    assert "Positive finite Kv" in invalid.blockers[0]

    print("OK — H-S50-A valve catalogue candidate-match evidence passed.")


if __name__ == "__main__":
    main()
