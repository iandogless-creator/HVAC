from HVAC.hydronics.proportioning.balancing_point_valve_product_search_criteria_intent_v1 import (
    PRODUCT_SEARCH_CRITERIA_AVAILABLE,
    PRODUCT_SEARCH_CRITERIA_PENDING,
    BalancingPointValveProductSearchCriteriaIntentV1,
    balancing_point_valve_product_search_criteria_intent_from_dict_v1,
    balancing_point_valve_product_search_criteria_intent_to_dict_v1,
    resolve_balancing_point_valve_product_search_criteria_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
    BalancingPointValveProductSearchDutyEnvelopeRowV1,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    point_id = "balancing-point:main:leg-002"
    envelope = BalancingPointValveProductSearchDutyEnvelopeV1(
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

    blank = resolve_balancing_point_valve_product_search_criteria_v1(
        None, envelope
    )
    assert blank.ready is True
    assert blank.rows[0].criteria_state_id == PRODUCT_SEARCH_CRITERIA_PENDING
    assert blank.rows[0].criteria_available is False

    intent = BalancingPointValveProductSearchCriteriaIntentV1()
    intent.set_criteria(
        balancing_point_id=point_id,
        accepted_kvs_basis=10.0,
        catalog_id="generic-valve-catalog-v1",
        kv_tolerance_percent=5.0,
        valve_ref_contains="STAD",
        note_contains="commissioning ports",
    )
    resolved = resolve_balancing_point_valve_product_search_criteria_v1(
        intent, envelope
    )
    assert resolved.ready is True
    row = resolved.rows[0]
    assert row.criteria_state_id == PRODUCT_SEARCH_CRITERIA_AVAILABLE
    assert row.criteria_available is True
    assert row.catalog_id == "generic-valve-catalog-v1"
    assert row.kv_tolerance_percent == 5.0
    assert row.valve_ref_contains == "STAD"
    assert "search not executed" in row.status

    payload = balancing_point_valve_product_search_criteria_intent_to_dict_v1(
        intent
    )
    restored = balancing_point_valve_product_search_criteria_intent_from_dict_v1(
        payload
    )
    assert restored.criteria_by_point_id[point_id].note_contains == (
        "commissioning ports"
    )

    stale_envelope = BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=True,
        rows=(BalancingPointValveProductSearchDutyEnvelopeRowV1(
            balancing_point_id=point_id,
            ready=True,
            envelope_state_id=PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
            product_search_required=True,
            envelope_available=True,
            approved_for_product_search=True,
            accepted_kvs=6.3,
        ),),
    )
    stale = resolve_balancing_point_valve_product_search_criteria_v1(
        intent, stale_envelope
    )
    assert stale.ready is False
    assert "stale" in stale.rows[0].status.lower()

    bad = balancing_point_valve_product_search_criteria_intent_from_dict_v1({
        "criteria_by_point_id": {
            "bad": {
                "accepted_kvs_basis": 0.0,
                "catalog_id": "",
                "kv_tolerance_percent": 101.0,
            }
        }
    })
    assert bad.criteria_by_point_id == {}
    assert restored.clear_criteria(point_id) is True
    assert restored.clear_criteria(point_id) is False

    project = ProjectState(project_id="hs49b", name="H-S49-B")
    project.hydronic_point_valve_product_search_criteria_intent = intent
    project_restored = ProjectState.from_dict(project.to_dict())
    project_intent = (
        project_restored.hydronic_point_valve_product_search_criteria_intent
    )
    assert project_intent is not None
    assert project_intent.criteria_by_point_id[point_id].catalog_id == (
        "generic-valve-catalog-v1"
    )
    empty_project = ProjectState.from_dict(
        ProjectState(project_id="empty", name="Empty").to_dict()
    )
    assert empty_project.hydronic_point_valve_product_search_criteria_intent is None

    assert "No product search executed" in resolved.exclusions
    assert "No catalogue queried" in resolved.exclusions
    assert "No valve product selected" in resolved.exclusions

    print("OK — H-S49-B manual valve product-search criteria intent passed.")


if __name__ == "__main__":
    main()
