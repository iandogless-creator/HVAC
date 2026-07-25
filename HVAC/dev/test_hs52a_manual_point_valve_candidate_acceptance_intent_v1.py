from __future__ import annotations

from HVAC.hydronics.proportioning.balancing_point_valve_candidate_acceptance_intent_v1 import (
    BalancingPointValveCandidateAcceptanceIntentV1,
    balancing_point_valve_candidate_acceptance_intent_from_dict_v1,
    balancing_point_valve_candidate_acceptance_intent_to_dict_v1,
    resolve_balancing_point_valve_candidate_acceptance_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_catalogue_candidate_match_evidence_v1 import (
    CATALOGUE_MATCH_EVIDENCE_AVAILABLE,
    BalancingPointValveCatalogueCandidateMatchEvidenceV1,
    BalancingPointValveCatalogueCandidateMatchRowV1,
    ValveCatalogueCandidateMatchV1,
)
from HVAC.project.project_state import ProjectState


CATALOG_ID = "local-generic-valves-v1"
POINT_ID = "balancing-point:subleg:leg-001-primary-subleg"


def _evidence(
    *,
    catalog_id: str = CATALOG_ID,
    valve_ref: str = "LOCAL-GENERIC-KV-6.3",
) -> BalancingPointValveCatalogueCandidateMatchEvidenceV1:
    return BalancingPointValveCatalogueCandidateMatchEvidenceV1(
        ready=True,
        catalog_id=catalog_id,
        rows=(
            BalancingPointValveCatalogueCandidateMatchRowV1(
                balancing_point_id=POINT_ID,
                ready=True,
                match_state_id=CATALOGUE_MATCH_EVIDENCE_AVAILABLE,
                match_evidence_available=True,
                accepted_kvs_basis=6.3,
                catalog_id=catalog_id,
                candidates=(
                    ValveCatalogueCandidateMatchV1(
                        catalog_id=catalog_id,
                        valve_ref=valve_ref,
                        kv_m3_h=6.3,
                        kv_deviation_percent=0.0,
                        note="Current supplied catalogue evidence",
                    ),
                ),
                status="1 catalogue candidate match",
            ),
        ),
    )


def main() -> None:
    intent = BalancingPointValveCandidateAcceptanceIntentV1()
    intent.accept_candidate(
        balancing_point_id=POINT_ID,
        catalog_id=CATALOG_ID,
        valve_ref="LOCAL-GENERIC-KV-6.3",
    )
    entry = intent.accepted_by_point_id[POINT_ID]
    assert entry.catalog_id == CATALOG_ID
    assert entry.valve_ref == "LOCAL-GENERIC-KV-6.3"

    payload = balancing_point_valve_candidate_acceptance_intent_to_dict_v1(
        intent
    )
    assert payload["schema"] == (
        "balancing_point_valve_candidate_acceptance_intent_v1"
    )
    assert "kv_m3_h" not in payload["accepted_by_point_id"][POINT_ID]
    restored = balancing_point_valve_candidate_acceptance_intent_from_dict_v1(
        payload
    )
    assert restored.accepted_by_point_id[POINT_ID] == entry

    resolved = resolve_balancing_point_valve_candidate_acceptance_v1(
        restored,
        _evidence(),
    )
    assert resolved.ready is True, resolved.status
    row = resolved.rows[0]
    assert row.accepted is True
    assert row.current_kv_m3_h == 6.3
    assert row.current_note == "Current supplied catalogue evidence"
    assert "No automatic candidate acceptance" in resolved.exclusions
    assert "no product hydraulics committed" in row.status

    pending = resolve_balancing_point_valve_candidate_acceptance_v1(
        None,
        _evidence(),
    )
    assert pending.ready is True
    assert pending.rows[0].accepted is False
    assert "pending" in pending.rows[0].status

    wrong_catalog = resolve_balancing_point_valve_candidate_acceptance_v1(
        restored,
        _evidence(catalog_id="replacement-catalog-v1"),
    )
    assert wrong_catalog.ready is False
    assert "catalogue identity" in wrong_catalog.blockers[0]

    stale_ref = resolve_balancing_point_valve_candidate_acceptance_v1(
        restored,
        _evidence(valve_ref="LOCAL-GENERIC-KV-10"),
    )
    assert stale_ref.ready is False
    assert "not a current H-S50-A candidate" in stale_ref.blockers[0]

    orphan = BalancingPointValveCandidateAcceptanceIntentV1()
    orphan.accept_candidate(
        balancing_point_id="balancing-point:missing",
        catalog_id=CATALOG_ID,
        valve_ref="LOCAL-GENERIC-KV-6.3",
    )
    orphaned = resolve_balancing_point_valve_candidate_acceptance_v1(
        orphan,
        _evidence(),
    )
    assert orphaned.ready is False
    assert "no current point evidence" in orphaned.blockers[0]

    invalid = balancing_point_valve_candidate_acceptance_intent_from_dict_v1(
        {
            "accepted_by_point_id": {
                "missing-catalog": {
                    "valve_ref": "LOCAL-GENERIC-KV-6.3",
                },
                "missing-ref": {
                    "catalog_id": CATALOG_ID,
                },
            }
        }
    )
    assert invalid.accepted_by_point_id == {}

    project = ProjectState(project_id="hs52a", name="H-S52-A")
    project.hydronic_point_valve_candidate_acceptance_intent = intent
    project_restored = ProjectState.from_dict(project.to_dict())
    project_intent = (
        project_restored.hydronic_point_valve_candidate_acceptance_intent
    )
    assert project_intent is not None
    assert project_intent.accepted_by_point_id[POINT_ID] == entry

    blank = ProjectState.from_dict(
        ProjectState(project_id="blank", name="Blank").to_dict()
    )
    assert blank.hydronic_point_valve_candidate_acceptance_intent is None

    assert restored.clear_candidate(POINT_ID) is True
    assert restored.clear_candidate(POINT_ID) is False

    print(
        "OK — H-S52-A manual point valve-candidate acceptance intent "
        "passed."
    )


if __name__ == "__main__":
    main()
