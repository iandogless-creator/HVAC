from __future__ import annotations

from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_acceptance_intent_v1 import (
    BalancingPointKvsCandidateAcceptanceIntentV1,
    balancing_point_kvs_candidate_acceptance_intent_from_dict_v1,
    balancing_point_kvs_candidate_acceptance_intent_to_dict_v1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_evidence_v1 import (
    GENERIC_PREFERRED_KVS_SERIES_ID_V1,
)
from HVAC.project.project_state import ProjectState


def main():
    intent = BalancingPointKvsCandidateAcceptanceIntentV1()
    intent.accept_candidate(
        balancing_point_id="balancing-point:main:leg-002",
        accepted_kvs=6.3,
    )
    intent.accept_candidate(
        balancing_point_id="balancing-point:subleg:leg-001-primary",
        accepted_kvs=10.0,
    )
    assert len(intent.accepted_by_point_id) == 2
    assert intent.accepted_by_point_id[
        "balancing-point:main:leg-002"
    ].accepted_kvs == 6.3

    payload = balancing_point_kvs_candidate_acceptance_intent_to_dict_v1(
        intent
    )
    assert payload["schema"] == (
        "balancing_point_kvs_candidate_acceptance_intent_v1"
    )
    restored = balancing_point_kvs_candidate_acceptance_intent_from_dict_v1(
        payload
    )
    restored_entry = restored.accepted_by_point_id[
        "balancing-point:main:leg-002"
    ]
    assert restored_entry.accepted_kvs == 6.3
    assert restored_entry.kvs_series_id == GENERIC_PREFERRED_KVS_SERIES_ID_V1

    assert restored.clear_candidate("balancing-point:main:leg-002") is True
    assert "balancing-point:main:leg-002" not in restored.accepted_by_point_id
    assert restored.clear_candidate("missing") is False

    bad = balancing_point_kvs_candidate_acceptance_intent_from_dict_v1(
        {
            "accepted_by_point_id": {
                "bad-zero": {
                    "accepted_kvs": 0.0,
                    "kvs_series_id": GENERIC_PREFERRED_KVS_SERIES_ID_V1,
                },
                "bad-series": {
                    "accepted_kvs": 6.3,
                    "kvs_series_id": "",
                },
            }
        }
    )
    assert bad.accepted_by_point_id == {}

    project = ProjectState(project_id="hs48a", name="H-S48-A")
    project.hydronic_point_kvs_candidate_acceptance_intent = intent
    project_payload = project.to_dict()
    raw = project_payload[
        "hydronic_point_kvs_candidate_acceptance_intent"
    ]
    assert raw["accepted_by_point_id"][
        "balancing-point:main:leg-002"
    ]["accepted_kvs"] == 6.3

    project_restored = ProjectState.from_dict(project_payload)
    project_intent = (
        project_restored.hydronic_point_kvs_candidate_acceptance_intent
    )
    assert project_intent is not None
    assert project_intent.accepted_by_point_id[
        "balancing-point:subleg:leg-001-primary"
    ].accepted_kvs == 10.0

    blank = ProjectState.from_dict(
        ProjectState(project_id="blank", name="Blank").to_dict()
    )
    assert blank.hydronic_point_kvs_candidate_acceptance_intent is None

    print("OK — H-S48-A manual point Kvs acceptance intent passed.")


if __name__ == "__main__":
    main()
