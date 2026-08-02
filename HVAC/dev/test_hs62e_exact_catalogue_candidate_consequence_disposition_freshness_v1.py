# ======================================================================
# H-S62-E — Exact accepted catalogue-candidate consequence-disposition
# freshness
# ======================================================================

from dataclasses import replace
from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_consequence_disposition_intent_v1 import (
    APPROVED_FOR_LATER_VALVE_DESIGN,
    BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1,
    balancing_point_accepted_valve_candidate_consequence_disposition_intent_from_dict_v1,
    balancing_point_accepted_valve_candidate_consequence_disposition_intent_to_dict_v1,
    build_accepted_valve_candidate_consequence_fingerprint_v1,
    resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_hydraulic_consequence_v1 import (
    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE,
    BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1,
    BalancingPointAcceptedValveCandidateHydraulicConsequenceV1,
)
from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    build_balancing_point_approved_valve_candidate_design_duty_envelope_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    BalancingPointValveProductSearchDutyEnvelopeRowV1,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)


POINT_ID = "balancing-point:subleg:hs62e"
CATALOG_ID = "catalog-v1"
VALVE_REF = "VALVE-KV-10"


def _row():
    return BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1(
        balancing_point_id=POINT_ID,
        ready=True,
        consequence_state_id=(
            ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE
        ),
        consequence_available=True,
        accepted=True,
        catalog_id=CATALOG_ID,
        valve_ref=VALVE_REF,
        current_kv_m3_h=10.0,
        flow_m3_h=0.6471,
        controlled_circuit_dp_pa=34_605.0,
        implied_valve_dp_bar=0.004188,
        implied_valve_dp_pa=418.8,
        implied_authority=0.012,
        status="Accepted catalogue valve-candidate consequence available",
    )


def _evidence(row):
    return BalancingPointAcceptedValveCandidateHydraulicConsequenceV1(
        ready=True,
        status="Ready",
        rows=(row,),
    )


def _product_duties():
    return BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=True,
        rows=(
            BalancingPointValveProductSearchDutyEnvelopeRowV1(
                balancing_point_id=POINT_ID,
                point_scope="subleg",
                point_role="common_route_downstream",
                label="H-S62-E downstream point",
                topology="Route-exclusive",
                governed_route_ids=("route-1",),
                ready=True,
                product_search_required=True,
                envelope_available=True,
                approved_for_product_search=True,
                point_flow_kg_s=0.1794,
                flow_m3_h=0.6471,
                required_kv=6.092,
                accepted_kvs=10.0,
                implied_valve_dp_pa=418.8,
                controlled_circuit_dp_pa=34_605.0,
                implied_authority=0.012,
                design_valve_dp_pa=2257.3,
                design_authority=0.061,
            ),
        ),
    )


def main() -> None:
    row = _row()
    fingerprint = (
        build_accepted_valve_candidate_consequence_fingerprint_v1(row)
    )
    assert len(fingerprint) == 64

    legacy = (
        BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1()
    )
    legacy.set_disposition(
        balancing_point_id=POINT_ID,
        disposition=APPROVED_FOR_LATER_VALVE_DESIGN,
        catalog_id_basis=CATALOG_ID,
        valve_ref_basis=VALVE_REF,
        current_kv_m3_h_basis=10.0,
    )
    compatible = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            legacy,
            _evidence(row),
        )
    )
    assert compatible.ready is True
    assert compatible.rows[0].approved_for_later_valve_design is True

    post_resize_legacy = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            legacy,
            _evidence(row),
            require_consequence_fingerprint=True,
        )
    )
    assert post_resize_legacy.ready is False
    assert "predates exact post-resize evidence" in post_resize_legacy.status

    intent = (
        BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1()
    )
    intent.set_disposition(
        balancing_point_id=POINT_ID,
        disposition=APPROVED_FOR_LATER_VALVE_DESIGN,
        catalog_id_basis=CATALOG_ID,
        valve_ref_basis=VALVE_REF,
        current_kv_m3_h_basis=10.0,
        consequence_fingerprint=fingerprint,
    )
    current = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            intent,
            _evidence(row),
            require_consequence_fingerprint=True,
        )
    )
    assert current.ready is True, current.status
    assert current.rows[0].approved_for_later_valve_design is True

    # Same catalogue identity and Kv must not revive a disposition after the
    # controlled duty and its hydraulic consequence have changed.
    changed_duty = replace(
        row,
        controlled_circuit_dp_pa=36_000.0,
        implied_authority=418.8 / (418.8 + 36_000.0),
    )
    stale = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            intent,
            _evidence(changed_duty),
            require_consequence_fingerprint=True,
        )
    )
    assert stale.ready is False
    assert stale.rows[0].approved_for_later_valve_design is False
    assert "fingerprint does not match" in stale.status
    assert intent.disposition_by_point_id[POINT_ID].valve_ref_basis == (
        VALVE_REF
    )

    changed_flow = replace(
        row,
        flow_m3_h=0.7,
        implied_valve_dp_bar=0.0049,
        implied_valve_dp_pa=490.0,
        implied_authority=490.0 / (490.0 + 34_605.0),
    )
    stale_flow = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            intent,
            _evidence(changed_flow),
            require_consequence_fingerprint=True,
        )
    )
    assert stale_flow.ready is False

    downstream = (
        build_balancing_point_approved_valve_candidate_design_duty_envelope_v1(
            _product_duties(),
            _evidence(changed_duty),
            stale,
        )
    )
    assert downstream.ready is False
    assert any("H-S52-D" in blocker for blocker in downstream.blockers)

    payload = (
        balancing_point_accepted_valve_candidate_consequence_disposition_intent_to_dict_v1(
            intent
        )
    )
    assert payload["disposition_by_point_id"][POINT_ID][
        "consequence_fingerprint"
    ] == fingerprint
    restored = (
        balancing_point_accepted_valve_candidate_consequence_disposition_intent_from_dict_v1(
            payload
        )
    )
    assert restored.disposition_by_point_id[
        POINT_ID
    ].consequence_fingerprint == fingerprint

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert (
        "build_accepted_valve_candidate_consequence_fingerprint_v1("
        in adapter_source
    )
    assert "require_consequence_fingerprint=(" in adapter_source
    assert "Current exact H-S52-C consequence is unavailable" in (
        adapter_source
    )

    print(
        "OK — H-S62-E exact accepted catalogue-candidate consequence-"
        "disposition freshness passed."
    )


if __name__ == "__main__":
    main()
