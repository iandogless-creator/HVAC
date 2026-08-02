# ======================================================================
# H-S62-D — Exact catalogue-candidate acceptance freshness
# ======================================================================

from dataclasses import replace
from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_hydraulic_consequence_v1 import (
    build_balancing_point_accepted_valve_candidate_hydraulic_consequence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_candidate_acceptance_intent_v1 import (
    BalancingPointValveCandidateAcceptanceIntentV1,
    balancing_point_valve_candidate_acceptance_intent_from_dict_v1,
    balancing_point_valve_candidate_acceptance_intent_to_dict_v1,
    build_valve_candidate_match_fingerprint_v1,
    resolve_balancing_point_valve_candidate_acceptance_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_catalogue_candidate_match_evidence_v1 import (
    CATALOGUE_MATCH_EVIDENCE_AVAILABLE,
    BalancingPointValveCatalogueCandidateMatchEvidenceV1,
    BalancingPointValveCatalogueCandidateMatchRowV1,
    ValveCatalogueCandidateMatchV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
    BalancingPointValveProductSearchDutyEnvelopeRowV1,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)


POINT_ID = "balancing-point:subleg:hs62d"
CATALOG_ID = "catalog-v1"
VALVE_REF = "STAD-1"


def _candidate(
    *,
    kv_m3_h: float = 1.0,
    deviation: float = 0.0,
    note: str = "Commissioning ports",
) -> ValveCatalogueCandidateMatchV1:
    return ValveCatalogueCandidateMatchV1(
        catalog_id=CATALOG_ID,
        valve_ref=VALVE_REF,
        kv_m3_h=kv_m3_h,
        kv_deviation_percent=deviation,
        note=note,
    )


def _row(
    candidate: ValveCatalogueCandidateMatchV1 | None = None,
    *,
    accepted_kvs_basis: float = 1.0,
) -> BalancingPointValveCatalogueCandidateMatchRowV1:
    return BalancingPointValveCatalogueCandidateMatchRowV1(
        balancing_point_id=POINT_ID,
        ready=True,
        match_state_id=CATALOGUE_MATCH_EVIDENCE_AVAILABLE,
        match_evidence_available=True,
        accepted_kvs_basis=accepted_kvs_basis,
        catalog_id=CATALOG_ID,
        kv_tolerance_percent=5.0,
        valve_ref_contains="STAD",
        note_contains="ports",
        candidates=(candidate or _candidate(),),
        status="1 catalogue candidate match",
    )


def _evidence(row):
    return BalancingPointValveCatalogueCandidateMatchEvidenceV1(
        ready=True,
        status="Ready",
        catalog_id=CATALOG_ID,
        rows=(row,),
    )


def _duty_envelopes():
    return BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=True,
        status="Ready",
        rows=(BalancingPointValveProductSearchDutyEnvelopeRowV1(
            balancing_point_id=POINT_ID,
            ready=True,
            envelope_state_id=PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
            product_search_required=True,
            envelope_available=True,
            approved_for_product_search=True,
            flow_m3_h=0.4509,
            controlled_circuit_dp_pa=12600.0,
        ),),
    )


def main() -> None:
    row = _row()
    candidate = row.candidates[0]
    fingerprint = build_valve_candidate_match_fingerprint_v1(
        row,
        candidate,
    )
    assert len(fingerprint) == 64

    legacy = BalancingPointValveCandidateAcceptanceIntentV1()
    legacy.accept_candidate(
        balancing_point_id=POINT_ID,
        catalog_id=CATALOG_ID,
        valve_ref=VALVE_REF,
    )
    compatible = resolve_balancing_point_valve_candidate_acceptance_v1(
        legacy,
        _evidence(row),
    )
    assert compatible.ready is True
    assert compatible.rows[0].accepted is True

    post_resize_legacy = resolve_balancing_point_valve_candidate_acceptance_v1(
        legacy,
        _evidence(row),
        require_match_fingerprint=True,
    )
    assert post_resize_legacy.ready is False
    assert post_resize_legacy.rows[0].accepted is False
    assert "predates exact post-resize" in post_resize_legacy.status

    intent = BalancingPointValveCandidateAcceptanceIntentV1()
    intent.accept_candidate(
        balancing_point_id=POINT_ID,
        catalog_id=CATALOG_ID,
        valve_ref=VALVE_REF,
        match_fingerprint=fingerprint,
    )
    current = resolve_balancing_point_valve_candidate_acceptance_v1(
        intent,
        _evidence(row),
        require_match_fingerprint=True,
    )
    assert current.ready is True
    assert current.rows[0].accepted is True

    # The same catalogue/reference identity must not revive when its current
    # Kv evidence changes.
    changed_candidate = _candidate(
        kv_m3_h=1.02,
        deviation=2.0,
    )
    stale_kv = resolve_balancing_point_valve_candidate_acceptance_v1(
        intent,
        _evidence(_row(changed_candidate)),
        require_match_fingerprint=True,
    )
    assert stale_kv.ready is False
    assert stale_kv.rows[0].accepted is False
    assert "fingerprint does not match" in stale_kv.status

    # A freshly reviewed upstream duty/criteria context also requires fresh
    # candidate acceptance even when the identity and current Kv are equal.
    changed_basis = resolve_balancing_point_valve_candidate_acceptance_v1(
        intent,
        _evidence(_row(accepted_kvs_basis=1.02)),
        require_match_fingerprint=True,
    )
    assert changed_basis.ready is False

    changed_note = resolve_balancing_point_valve_candidate_acceptance_v1(
        intent,
        _evidence(_row(_candidate(note="Revised catalogue description"))),
        require_match_fingerprint=True,
    )
    assert changed_note.ready is False

    payload = balancing_point_valve_candidate_acceptance_intent_to_dict_v1(
        intent
    )
    assert payload["accepted_by_point_id"][POINT_ID][
        "match_fingerprint"
    ] == fingerprint
    restored = balancing_point_valve_candidate_acceptance_intent_from_dict_v1(
        payload
    )
    assert restored.accepted_by_point_id[
        POINT_ID
    ].match_fingerprint == fingerprint

    consequence = (
        build_balancing_point_accepted_valve_candidate_hydraulic_consequence_v1(
            _duty_envelopes(),
            stale_kv,
        )
    )
    assert consequence.ready is False
    assert "H-S52-A" in consequence.status

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert "build_valve_candidate_match_fingerprint_v1(" in adapter_source
    assert "require_match_fingerprint=(" in adapter_source
    assert (
        "Current exact H-S50-A candidate-match evidence is"
        in adapter_source
    )

    print(
        "OK — H-S62-D exact catalogue-candidate acceptance freshness "
        "passed."
    )


if __name__ == "__main__":
    main()
