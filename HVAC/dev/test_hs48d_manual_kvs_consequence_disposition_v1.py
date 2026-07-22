# ======================================================================
# H-S48-D — Manual accepted-Kvs consequence disposition
# ======================================================================

from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
    KVS_REVISION_REQUIRED,
    BalancingPointAcceptedKvsConsequenceDispositionIntentV1,
    resolve_balancing_point_accepted_kvs_consequence_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import (
    ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
    BalancingPointAcceptedKvsHydraulicConsequenceRowV1,
    BalancingPointAcceptedKvsHydraulicConsequenceV1,
)
from HVAC.project.project_state import ProjectState


def consequence(accepted_kvs: float = 10.0):
    return BalancingPointAcceptedKvsHydraulicConsequenceV1(
        ready=True,
        rows=(
            BalancingPointAcceptedKvsHydraulicConsequenceRowV1(
                balancing_point_id="point-1",
                ready=True,
                consequence_state_id=ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
                consequence_available=True,
                accepted=True,
                accepted_kvs=accepted_kvs,
                flow_m3_h=1.0,
                controlled_circuit_dp_pa=99_000.0,
                implied_valve_dp_bar=0.01,
                implied_valve_dp_pa=1_000.0,
                implied_authority=0.01,
            ),
        ),
    )


def main() -> None:
    pending = resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
        None,
        consequence(),
    )
    assert pending.ready is True
    assert pending.rows[0].disposition == ""
    assert "pending" in pending.rows[0].status.lower()

    intent = BalancingPointAcceptedKvsConsequenceDispositionIntentV1()
    intent.set_disposition(
        balancing_point_id="point-1",
        disposition=APPROVED_FOR_PRODUCT_SEARCH,
        accepted_kvs_basis=10.0,
    )
    approved = resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
        intent,
        consequence(),
    )
    assert approved.ready is True
    assert approved.rows[0].approved_for_product_search is True
    assert "search not started" in approved.rows[0].status.lower()

    stale = resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
        intent,
        consequence(6.3),
    )
    assert stale.ready is False
    assert stale.rows[0].approved_for_product_search is False
    assert any("stale" in value.lower() for value in stale.blockers)

    intent.set_disposition(
        balancing_point_id="point-1",
        disposition=KVS_REVISION_REQUIRED,
        accepted_kvs_basis=6.3,
    )
    revision = resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
        intent,
        consequence(6.3),
    )
    assert revision.ready is True
    assert revision.rows[0].kvs_revision_required is True
    assert "no automatic change" in revision.rows[0].status.lower()

    project = ProjectState(project_id="hs48d", name="H-S48-D")
    project.hydronic_point_accepted_kvs_consequence_disposition_intent = intent
    restored = ProjectState.from_dict(project.to_dict())
    restored_intent = (
        restored.hydronic_point_accepted_kvs_consequence_disposition_intent
    )
    assert restored_intent is not None
    assert restored_intent.disposition_by_point_id["point-1"].disposition == (
        KVS_REVISION_REQUIRED
    )
    assert restored_intent.clear_disposition("point-1") is True

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()
    assert adapter_source.count(
        "    def set_balancing_point_kvs_candidate_acceptance("
    ) == 1
    assert "set_accepted_kvs_consequence_disposition" in adapter_source
    assert "resolve_balancing_point_accepted_kvs_consequence_disposition_v1(" in adapter_source
    assert "Approve preview for later product search" in panel_source
    assert "Require Kvs revision" in panel_source
    assert "Apply consequence disposition" in panel_source
    assert '"Consequence disposition"' in panel_source

    print("OK — H-S48-D manual accepted-Kvs consequence disposition passed.")


if __name__ == "__main__":
    main()
