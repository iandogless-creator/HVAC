# ======================================================================
# H-S62-B — Exact accepted-Kvs consequence-disposition freshness
# ======================================================================

from dataclasses import replace
from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
    BalancingPointAcceptedKvsConsequenceDispositionIntentV1,
    balancing_point_accepted_kvs_consequence_disposition_intent_from_dict_v1,
    balancing_point_accepted_kvs_consequence_disposition_intent_to_dict_v1,
    build_accepted_kvs_consequence_fingerprint_v1,
    resolve_balancing_point_accepted_kvs_consequence_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import (
    ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
    BalancingPointAcceptedKvsHydraulicConsequenceRowV1,
    BalancingPointAcceptedKvsHydraulicConsequenceV1,
)
from HVAC.hydronics.proportioning.balancing_point_proportioning_commit_readiness_v1 import (
    build_point_proportioning_commit_readiness_v1,
)


POINT_ID = "balancing-point:subleg:hs62b"


def _row():
    return BalancingPointAcceptedKvsHydraulicConsequenceRowV1(
        balancing_point_id=POINT_ID,
        ready=True,
        consequence_state_id=ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
        consequence_available=True,
        accepted=True,
        accepted_kvs=1.0,
        flow_m3_h=0.45,
        controlled_circuit_dp_pa=12600.0,
        implied_valve_dp_bar=0.2025,
        implied_valve_dp_pa=20250.0,
        implied_authority=20250.0 / (20250.0 + 12600.0),
        status="Accepted generic Kvs hydraulic consequence available",
    )


def _evidence(row):
    return BalancingPointAcceptedKvsHydraulicConsequenceV1(
        ready=True,
        status="Ready",
        rows=(row,),
    )


def main() -> None:
    row = _row()
    fingerprint = build_accepted_kvs_consequence_fingerprint_v1(row)
    assert len(fingerprint) == 64

    legacy = BalancingPointAcceptedKvsConsequenceDispositionIntentV1()
    legacy.set_disposition(
        balancing_point_id=POINT_ID,
        disposition=APPROVED_FOR_PRODUCT_SEARCH,
        accepted_kvs_basis=1.0,
    )
    compatible = (
        resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
            legacy,
            _evidence(row),
        )
    )
    assert compatible.ready is True
    assert compatible.rows[0].approved_for_product_search is True

    post_resize_legacy = (
        resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
            legacy,
            _evidence(row),
            require_consequence_fingerprint=True,
        )
    )
    assert post_resize_legacy.ready is False
    assert "predates exact post-resize evidence" in post_resize_legacy.status

    intent = BalancingPointAcceptedKvsConsequenceDispositionIntentV1()
    intent.set_disposition(
        balancing_point_id=POINT_ID,
        disposition=APPROVED_FOR_PRODUCT_SEARCH,
        accepted_kvs_basis=1.0,
        consequence_fingerprint=fingerprint,
    )
    current = resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
        intent,
        _evidence(row),
        require_consequence_fingerprint=True,
    )
    assert current.ready is True
    assert current.rows[0].approved_for_product_search is True

    # Re-accepting the same numerical Kvs under changed circuit duty must not
    # revive the old manual consequence disposition.
    changed = replace(
        row,
        controlled_circuit_dp_pa=13200.0,
        implied_authority=20250.0 / (20250.0 + 13200.0),
    )
    stale = resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
        intent,
        _evidence(changed),
        require_consequence_fingerprint=True,
    )
    assert stale.ready is False
    assert stale.rows[0].approved_for_product_search is False
    assert "fingerprint does not match" in stale.status
    assert intent.disposition_by_point_id[POINT_ID].accepted_kvs_basis == 1.0
    commit_readiness = build_point_proportioning_commit_readiness_v1(stale)
    assert commit_readiness.ready is False

    changed_flow = replace(
        row,
        flow_m3_h=0.48,
        implied_valve_dp_bar=0.2304,
        implied_valve_dp_pa=23040.0,
        implied_authority=23040.0 / (23040.0 + 12600.0),
    )
    stale_flow = (
        resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
            intent,
            _evidence(changed_flow),
            require_consequence_fingerprint=True,
        )
    )
    assert stale_flow.ready is False

    payload = (
        balancing_point_accepted_kvs_consequence_disposition_intent_to_dict_v1(
            intent
        )
    )
    assert payload["disposition_by_point_id"][POINT_ID][
        "consequence_fingerprint"
    ] == fingerprint
    restored = (
        balancing_point_accepted_kvs_consequence_disposition_intent_from_dict_v1(
            payload
        )
    )
    assert restored.disposition_by_point_id[
        POINT_ID
    ].consequence_fingerprint == fingerprint

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "build_accepted_kvs_consequence_fingerprint_v1(" in adapter_source
    assert "require_consequence_fingerprint=(" in adapter_source
    assert "Current exact H-S48-C consequence is unavailable" in adapter_source

    print(
        "OK — H-S62-B exact accepted-Kvs consequence-disposition "
        "freshness passed."
    )


if __name__ == "__main__":
    main()
