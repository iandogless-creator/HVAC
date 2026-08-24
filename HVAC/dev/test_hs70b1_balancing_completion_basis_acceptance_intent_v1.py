from __future__ import annotations

from dataclasses import replace

from HVAC.dev.test_hs70a_balancing_completion_readiness_v1 import (
    POINT_CONTROL,
    POINT_DUTY,
    _snapshot,
    _topology,
)
from HVAC.hydronics.proportioning.balancing_completion_basis_acceptance_intent_v1 import (
    BalancingCompletionBasisAcceptanceIntentV1,
    balancing_completion_basis_acceptance_intent_from_dict_v1,
    balancing_completion_basis_acceptance_intent_to_dict_v1,
    build_balancing_completion_basis_fingerprint_v1,
    resolve_balancing_completion_basis_acceptance_v1,
)
from HVAC.hydronics.proportioning.balancing_completion_readiness_v1 import (
    build_balancing_completion_readiness_v1,
)
from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.project.project_state import ProjectState


def _ready_inputs():
    snapshot = _snapshot()
    topology = _topology()
    readiness = build_balancing_completion_readiness_v1(
        snapshot=snapshot,
        topology=topology,
    )
    assert readiness.ready is True, readiness.status
    return snapshot, readiness


def _accepted_intent(snapshot, readiness):
    fingerprint = build_balancing_completion_basis_fingerprint_v1(
        readiness=readiness,
        snapshot=snapshot,
    )
    intent = BalancingCompletionBasisAcceptanceIntentV1()
    intent.accept_point_basis(
        balancing_point_id=POINT_DUTY,
        accepted_method_id=PROPORTIONAL_ADDED_RESISTANCE,
        accepted_kvs_basis=1.6,
        basis_fingerprint=fingerprint,
    )
    intent.accept_point_basis(
        balancing_point_id=POINT_CONTROL,
        accepted_method_id=NONE_REQUIRED,
        accepted_kvs_basis=None,
        basis_fingerprint=fingerprint,
    )
    return intent


def main() -> None:
    snapshot, readiness = _ready_inputs()
    before_snapshot = repr(snapshot)
    before_readiness = repr(readiness)
    intent = _accepted_intent(snapshot, readiness)

    result = resolve_balancing_completion_basis_acceptance_v1(
        intent=intent,
        readiness=readiness,
        snapshot=snapshot,
    )
    repeated = resolve_balancing_completion_basis_acceptance_v1(
        intent=intent,
        readiness=readiness,
        snapshot=snapshot,
    )
    assert result == repeated
    assert result.ready is True, result.status
    assert len(result.basis_fingerprint) == 64
    rows = {row.balancing_point_id: row for row in result.rows}
    assert rows[POINT_DUTY].required_method_id == (
        PROPORTIONAL_ADDED_RESISTANCE
    )
    assert rows[POINT_DUTY].accepted_kvs_basis == 1.6
    assert rows[POINT_CONTROL].required_method_id == NONE_REQUIRED
    assert rows[POINT_CONTROL].accepted_kvs_basis is None
    assert repr(snapshot) == before_snapshot
    assert repr(readiness) == before_readiness

    missing = BalancingCompletionBasisAcceptanceIntentV1()
    missing_result = resolve_balancing_completion_basis_acceptance_v1(
        intent=missing,
        readiness=readiness,
        snapshot=snapshot,
    )
    assert missing_result.ready is False
    assert "Explicit balancing basis acceptance required" in (
        missing_result.status
    )

    changed_basis = replace(
        snapshot.committed_point_valve_bases[0],
        accepted_kvs_basis=2.5,
    )
    changed_snapshot = replace(
        snapshot,
        committed_point_valve_bases=(changed_basis,),
    )
    changed_readiness = build_balancing_completion_readiness_v1(
        snapshot=changed_snapshot,
        topology=_topology(),
    )
    assert changed_readiness.ready is True, changed_readiness.status
    stale = resolve_balancing_completion_basis_acceptance_v1(
        intent=intent,
        readiness=changed_readiness,
        snapshot=changed_snapshot,
    )
    assert stale.ready is False
    assert "stale for current committed duty" in stale.status
    assert "must match committed generic-Kvs basis" in stale.status

    payload = balancing_completion_basis_acceptance_intent_to_dict_v1(intent)
    restored = balancing_completion_basis_acceptance_intent_from_dict_v1(
        payload
    )
    assert restored.accepted_by_point_id == intent.accepted_by_point_id
    assert restored.clear_point_basis(POINT_CONTROL) is True
    assert restored.clear_point_basis(POINT_CONTROL) is False

    project = ProjectState(project_id="hs70b1", name="H-S70-B1")
    project.hydronic_balancing_completion_basis_acceptance_intent = intent
    project_payload = project.to_dict()
    assert project_payload[
        "hydronic_balancing_completion_basis_acceptance_intent"
    ]["accepted_by_point_id"][POINT_DUTY]["accepted_kvs_basis"] == 1.6
    restored_project = ProjectState.from_dict(project_payload)
    restored_intent = (
        restored_project.hydronic_balancing_completion_basis_acceptance_intent
    )
    assert restored_intent is not None
    assert restored_intent.accepted_by_point_id == intent.accepted_by_point_id

    blank = ProjectState.from_dict(
        ProjectState(project_id="blank", name="Blank").to_dict()
    )
    assert (
        blank.hydronic_balancing_completion_basis_acceptance_intent is None
    )
    assert "No new Kv or Kvs selection" in result.exclusions
    assert "No valve product, size or setting selected" in result.exclusions
    assert "No final balancing schedule committed" in result.exclusions
    assert "No pump duty or pump selection" in result.exclusions

    print(
        "OK — H-S70-B1 persists explicit point balancing-method and exact "
        "committed generic-Kvs basis acceptance, rejects stale duties and "
        "introduces no valve-product or pump authority."
    )


if __name__ == "__main__":
    main()
