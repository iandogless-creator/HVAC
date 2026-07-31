# ======================================================================
# H-S62-A — Exact point-duty-bound generic-Kvs acceptance freshness
# ======================================================================

from dataclasses import replace
from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_acceptance_intent_v1 import (
    BalancingPointKvsCandidateAcceptanceIntentV1,
    balancing_point_kvs_candidate_acceptance_intent_from_dict_v1,
    balancing_point_kvs_candidate_acceptance_intent_to_dict_v1,
    build_balancing_point_kvs_acceptance_duty_fingerprint_v1,
    resolve_balancing_point_kvs_candidate_acceptance_v1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_evidence_v1 import (
    GENERIC_PREFERRED_KVS_SERIES_ID_V1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_utilisation_evidence_v1 import (
    BalancingPointKvsCandidateUtilisationEvidenceRowV1,
    BalancingPointKvsCandidateUtilisationEvidenceV1,
)


POINT_ID = "balancing-point:subleg:hs62a"


def _row():
    return BalancingPointKvsCandidateUtilisationEvidenceRowV1(
        balancing_point_id=POINT_ID,
        label="H-S62-A point",
        point_scope="subleg",
        point_role="downstream",
        parent_balancing_point_id="balancing-point:main:hs62a",
        anchor_section_id="section-hs62a",
        downstream_route_ids=("route-hs62a",),
        is_shared=False,
        is_route_exclusive=True,
        balancing_method_id="manual_balancing_valve_candidate",
        balancing_method_label="Manual balancing valve candidate",
        authority_band_id="manual_review",
        authority_label="Manual review",
        candidate_resistance_pa_per_kg_s2=153600.0,
        ready=True,
        point_flow_kg_s=0.125,
        design_valve_dp_pa=2400.0,
        controlled_circuit_dp_pa=12600.0,
        flow_m3_h=0.4509018036072144,
        required_kv=0.9204302343192468,
        fluid_density_kg_m3=998.0,
        fluid_density_basis_id="hydronic_water_density_998_kg_m3",
        kvs_series_id=GENERIC_PREFERRED_KVS_SERIES_ID_V1,
        kvs_candidates=(1.0, 1.6, 2.5),
        kvs_candidates_available=True,
        kvs_utilisation_available=True,
    )


def _evidence(row):
    return BalancingPointKvsCandidateUtilisationEvidenceV1(
        ready=True,
        status="Ready",
        rows=(row,),
    )


def main() -> None:
    row = _row()
    fingerprint = (
        build_balancing_point_kvs_acceptance_duty_fingerprint_v1(row)
    )
    assert len(fingerprint) == 64

    legacy = BalancingPointKvsCandidateAcceptanceIntentV1()
    legacy.accept_candidate(
        balancing_point_id=POINT_ID,
        accepted_kvs=1.0,
    )
    compatible = resolve_balancing_point_kvs_candidate_acceptance_v1(
        legacy,
        _evidence(row),
    )
    assert compatible.ready is True
    assert compatible.rows[0].accepted is True

    post_resize_legacy = resolve_balancing_point_kvs_candidate_acceptance_v1(
        legacy,
        _evidence(row),
        require_duty_fingerprint=True,
    )
    assert post_resize_legacy.ready is False
    assert post_resize_legacy.rows[0].accepted is False
    assert "predates exact point-duty evidence" in post_resize_legacy.status

    intent = BalancingPointKvsCandidateAcceptanceIntentV1()
    intent.accept_candidate(
        balancing_point_id=POINT_ID,
        accepted_kvs=1.0,
        duty_fingerprint=fingerprint,
    )
    current = resolve_balancing_point_kvs_candidate_acceptance_v1(
        intent,
        _evidence(row),
        require_duty_fingerprint=True,
    )
    assert current.ready is True
    assert current.rows[0].accepted is True

    changed = replace(
        row,
        controlled_circuit_dp_pa=13200.0,
    )
    stale = resolve_balancing_point_kvs_candidate_acceptance_v1(
        intent,
        _evidence(changed),
        require_duty_fingerprint=True,
    )
    assert stale.ready is False
    assert stale.rows[0].accepted is False
    assert "duty fingerprint does not match" in stale.status
    assert intent.accepted_by_point_id[POINT_ID].accepted_kvs == 1.0

    payload = balancing_point_kvs_candidate_acceptance_intent_to_dict_v1(
        intent
    )
    assert payload["accepted_by_point_id"][POINT_ID][
        "duty_fingerprint"
    ] == fingerprint
    restored = balancing_point_kvs_candidate_acceptance_intent_from_dict_v1(
        payload
    )
    assert restored.accepted_by_point_id[POINT_ID].duty_fingerprint == (
        fingerprint
    )

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert (
        "build_balancing_point_kvs_acceptance_duty_fingerprint_v1("
        in adapter_source
    )
    assert "require_duty_fingerprint=(" in adapter_source
    assert "COMMITTED_RESIZED_HYDRAULICS" in adapter_source
    assert "Current exact H-S47-C point duty is unavailable" in adapter_source

    print(
        "OK — H-S62-A exact point-duty-bound generic-Kvs acceptance "
        "freshness passed."
    )


if __name__ == "__main__":
    main()
