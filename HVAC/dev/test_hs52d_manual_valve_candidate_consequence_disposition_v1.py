# ======================================================================
# H-S52-D — Manual accepted valve-candidate consequence disposition
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_consequence_disposition_intent_v1 import (
    APPROVED_FOR_LATER_VALVE_DESIGN,
    VALVE_CANDIDATE_REVISION_REQUIRED,
    BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1,
    balancing_point_accepted_valve_candidate_consequence_disposition_intent_from_dict_v1,
    resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_hydraulic_consequence_v1 import (
    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE,
    BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1,
    BalancingPointAcceptedValveCandidateHydraulicConsequenceV1,
)
from HVAC.project.project_state import ProjectState


POINT_ID = "balancing-point:subleg:test"
CATALOG_ID = "catalog-v1"
VALVE_REF = "VALVE-KV-10"


def consequence(
    *,
    catalog_id: str = CATALOG_ID,
    valve_ref: str = VALVE_REF,
    current_kv: float = 10.0,
) -> BalancingPointAcceptedValveCandidateHydraulicConsequenceV1:
    return BalancingPointAcceptedValveCandidateHydraulicConsequenceV1(
        ready=True,
        rows=(
            BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1(
                balancing_point_id=POINT_ID,
                ready=True,
                consequence_state_id=(
                    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE
                ),
                consequence_available=True,
                accepted=True,
                catalog_id=catalog_id,
                valve_ref=valve_ref,
                current_kv_m3_h=current_kv,
                flow_m3_h=1.0,
                controlled_circuit_dp_pa=99_000.0,
                implied_valve_dp_bar=0.01,
                implied_valve_dp_pa=1_000.0,
                implied_authority=0.01,
            ),
        ),
    )


def main() -> None:
    pending = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            None,
            consequence(),
        )
    )
    assert pending.ready is True
    assert pending.rows[0].disposition == ""
    assert "pending" in pending.rows[0].status.lower()

    intent = (
        BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1()
    )
    intent.set_disposition(
        balancing_point_id=POINT_ID,
        disposition=APPROVED_FOR_LATER_VALVE_DESIGN,
        catalog_id_basis=CATALOG_ID,
        valve_ref_basis=VALVE_REF,
        current_kv_m3_h_basis=10.0,
    )
    approved = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            intent,
            consequence(),
        )
    )
    assert approved.ready is True, approved.status
    row = approved.rows[0]
    assert row.approved_for_later_valve_design is True
    assert row.valve_candidate_revision_required is False
    assert "no valve size or setting committed" in row.status.lower()

    stale_catalogue = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            intent,
            consequence(catalog_id="replacement-catalog"),
        )
    )
    assert stale_catalogue.ready is False
    assert "stale" in stale_catalogue.blockers[0].lower()

    stale_reference = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            intent,
            consequence(valve_ref="VALVE-KV-6.3"),
        )
    )
    assert stale_reference.ready is False
    assert "stale" in stale_reference.blockers[0].lower()

    stale_kv = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            intent,
            consequence(current_kv=6.3),
        )
    )
    assert stale_kv.ready is False
    assert "stale" in stale_kv.blockers[0].lower()

    intent.set_disposition(
        balancing_point_id=POINT_ID,
        disposition=VALVE_CANDIDATE_REVISION_REQUIRED,
        catalog_id_basis=CATALOG_ID,
        valve_ref_basis=VALVE_REF,
        current_kv_m3_h_basis=10.0,
    )
    revision = (
        resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
            intent,
            consequence(),
        )
    )
    assert revision.ready is True
    assert revision.rows[0].valve_candidate_revision_required is True
    assert "no automatic change" in revision.rows[0].status.lower()

    project = ProjectState(project_id="hs52d", name="H-S52-D")
    project.hydronic_point_accepted_valve_candidate_consequence_disposition_intent = (
        intent
    )
    restored = ProjectState.from_dict(project.to_dict())
    restored_intent = (
        restored
        .hydronic_point_accepted_valve_candidate_consequence_disposition_intent
    )
    assert restored_intent is not None
    entry = restored_intent.disposition_by_point_id[POINT_ID]
    assert entry.disposition == VALVE_CANDIDATE_REVISION_REQUIRED
    assert entry.catalog_id_basis == CATALOG_ID
    assert entry.valve_ref_basis == VALVE_REF
    assert entry.current_kv_m3_h_basis == 10.0

    invalid = (
        balancing_point_accepted_valve_candidate_consequence_disposition_intent_from_dict_v1(
            {
                "disposition_by_point_id": {
                    POINT_ID: {
                        "disposition": APPROVED_FOR_LATER_VALVE_DESIGN,
                        "catalog_id_basis": CATALOG_ID,
                    },
                },
            }
        )
    )
    assert invalid.disposition_by_point_id == {}
    assert restored_intent.clear_disposition(POINT_ID) is True
    assert restored_intent.clear_disposition(POINT_ID) is False

    assert "No product-derived hydraulic mutation" in approved.exclusions
    assert "No committed valve product selection" in approved.exclusions
    assert "No final balancing" in approved.exclusions

    print(
        "OK — H-S52-D manual accepted valve-candidate consequence "
        "disposition intent passed."
    )


if __name__ == "__main__":
    main()
