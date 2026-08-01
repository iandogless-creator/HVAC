# ======================================================================
# H-S62-C — Exact product-search criteria duty-envelope freshness
# ======================================================================

from dataclasses import replace
from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_valve_catalogue_candidate_match_evidence_v1 import (
    build_balancing_point_valve_catalogue_candidate_match_evidence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_criteria_intent_v1 import (
    BalancingPointValveProductSearchCriteriaIntentV1,
    balancing_point_valve_product_search_criteria_intent_from_dict_v1,
    balancing_point_valve_product_search_criteria_intent_to_dict_v1,
    build_product_search_duty_envelope_fingerprint_v1,
    resolve_balancing_point_valve_product_search_criteria_v1,
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


POINT_ID = "balancing-point:subleg:hs62c"


def _row():
    return BalancingPointValveProductSearchDutyEnvelopeRowV1(
        balancing_point_id=POINT_ID,
        point_scope="subleg",
        point_role="downstream",
        topology="Route-exclusive",
        governed_route_ids=("route-1",),
        ready=True,
        envelope_state_id=PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
        product_search_required=True,
        envelope_available=True,
        approved_for_product_search=True,
        point_flow_kg_s=0.125,
        flow_m3_h=0.4509,
        required_kv=0.92,
        accepted_kvs=1.0,
        kvs_series_id="generic_preferred_kvs_series_v1",
        implied_valve_dp_bar=0.20331,
        implied_valve_dp_pa=20331.0,
        controlled_circuit_dp_pa=12600.0,
        implied_authority=20331.0 / (20331.0 + 12600.0),
        design_valve_dp_pa=2400.0,
        design_authority=2400.0 / (2400.0 + 12600.0),
        status="Approved product-search envelope available",
    )


def _envelopes(row):
    return BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=True,
        status="Ready",
        rows=(row,),
    )


def main() -> None:
    row = _row()
    fingerprint = build_product_search_duty_envelope_fingerprint_v1(row)
    assert len(fingerprint) == 64

    legacy = BalancingPointValveProductSearchCriteriaIntentV1()
    legacy.set_criteria(
        balancing_point_id=POINT_ID,
        accepted_kvs_basis=1.0,
        catalog_id="catalog-v1",
        kv_tolerance_percent=5.0,
    )
    compatible = resolve_balancing_point_valve_product_search_criteria_v1(
        legacy,
        _envelopes(row),
    )
    assert compatible.ready is True
    assert compatible.rows[0].criteria_available is True

    post_resize_legacy = (
        resolve_balancing_point_valve_product_search_criteria_v1(
            legacy,
            _envelopes(row),
            require_duty_envelope_fingerprint=True,
        )
    )
    assert post_resize_legacy.ready is False
    assert "predate exact post-resize duty" in post_resize_legacy.status

    intent = BalancingPointValveProductSearchCriteriaIntentV1()
    intent.set_criteria(
        balancing_point_id=POINT_ID,
        accepted_kvs_basis=1.0,
        catalog_id="catalog-v1",
        kv_tolerance_percent=5.0,
        valve_ref_contains="STAD",
        duty_envelope_fingerprint=fingerprint,
    )
    current = resolve_balancing_point_valve_product_search_criteria_v1(
        intent,
        _envelopes(row),
        require_duty_envelope_fingerprint=True,
    )
    assert current.ready is True
    assert current.rows[0].criteria_available is True

    # Same accepted Kvs, changed controlled-circuit duty: the old filters must
    # not revive and must not reach catalogue candidate matching.
    changed = replace(
        row,
        controlled_circuit_dp_pa=13200.0,
        implied_authority=20331.0 / (20331.0 + 13200.0),
        design_authority=2400.0 / (2400.0 + 13200.0),
    )
    stale = resolve_balancing_point_valve_product_search_criteria_v1(
        intent,
        _envelopes(changed),
        require_duty_envelope_fingerprint=True,
    )
    assert stale.ready is False
    assert stale.rows[0].criteria_available is False
    assert "fingerprint does not match" in stale.status
    catalogue = ValveCatalogDTO(
        catalog_id="catalog-v1",
        kv_options=[ValveKvOptionDTO("STAD-1", 1.0, "ports")],
    )
    matches = build_balancing_point_valve_catalogue_candidate_match_evidence_v1(
        _envelopes(changed),
        stale,
        catalogue,
    )
    assert matches.ready is False

    changed_flow = replace(
        row,
        point_flow_kg_s=0.130,
        flow_m3_h=0.468,
        implied_valve_dp_bar=0.219024,
        implied_valve_dp_pa=21902.4,
        implied_authority=21902.4 / (21902.4 + 12600.0),
    )
    stale_flow = resolve_balancing_point_valve_product_search_criteria_v1(
        intent,
        _envelopes(changed_flow),
        require_duty_envelope_fingerprint=True,
    )
    assert stale_flow.ready is False

    payload = balancing_point_valve_product_search_criteria_intent_to_dict_v1(
        intent
    )
    assert payload["criteria_by_point_id"][POINT_ID][
        "duty_envelope_fingerprint"
    ] == fingerprint
    restored = balancing_point_valve_product_search_criteria_intent_from_dict_v1(
        payload
    )
    assert restored.criteria_by_point_id[
        POINT_ID
    ].duty_envelope_fingerprint == fingerprint

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "build_product_search_duty_envelope_fingerprint_v1(" in adapter_source
    assert "require_duty_envelope_fingerprint=(" in adapter_source
    assert "Current exact H-S49-A duty envelope is unavailable" in adapter_source

    print(
        "OK — H-S62-C exact product-search criteria duty-envelope "
        "freshness passed."
    )


if __name__ == "__main__":
    main()
