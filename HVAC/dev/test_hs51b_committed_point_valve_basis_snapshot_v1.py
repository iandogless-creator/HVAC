from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
)
from HVAC.hydronics.proportioning.balancing_point_proportioning_commit_readiness_v1 import (
    GENERIC_KVS_BASIS_APPROVED,
    NO_VALVE_POINT_READY,
    PointProportioningCommitReadinessRowV1,
    PointProportioningCommitReadinessV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    build_proportioned_basis_snapshot_v1,
    proportioned_basis_snapshot_from_dict_v1,
    proportioned_basis_snapshot_to_dict_v1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    ReturnArrangementIntentV1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    project = ProjectState(project_id="hs51b", name="H-S51-B")
    project.hydronic_return_arrangement_intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
    )
    point_readiness = PointProportioningCommitReadinessV1(
        ready=True,
        rows=(
            PointProportioningCommitReadinessRowV1(
                balancing_point_id="point:no-valve",
                readiness_state_id=NO_VALVE_POINT_READY,
                ready=True,
                valve_duty_required=False,
            ),
            PointProportioningCommitReadinessRowV1(
                balancing_point_id="point:main",
                readiness_state_id=GENERIC_KVS_BASIS_APPROVED,
                ready=True,
                valve_duty_required=True,
                accepted_kvs_basis=6.3,
                disposition=APPROVED_FOR_PRODUCT_SEARCH,
            ),
            PointProportioningCommitReadinessRowV1(
                balancing_point_id="point:subleg",
                readiness_state_id=GENERIC_KVS_BASIS_APPROVED,
                ready=True,
                valve_duty_required=True,
                accepted_kvs_basis=10.0,
                disposition=APPROVED_FOR_PRODUCT_SEARCH,
            ),
        ),
    )
    result = build_proportioned_basis_snapshot_v1(
        project,
        point_commit_readiness=point_readiness,
    )
    assert result.ready is True, result.status
    snapshot = result.snapshot
    assert snapshot is not None
    assert [row.balancing_point_id for row in snapshot.committed_point_valve_bases] == [
        "point:main",
        "point:subleg",
    ]
    assert [row.accepted_kvs_basis for row in snapshot.committed_point_valve_bases] == [
        6.3,
        10.0,
    ]
    assert "2 manually approved" in snapshot.point_valve_basis_status

    payload = proportioned_basis_snapshot_to_dict_v1(snapshot)
    assert payload is not None
    assert len(payload["committed_point_valve_bases"]) == 2
    assert "catalog_id" not in payload["committed_point_valve_bases"][0]
    assert "valve_ref" not in payload["committed_point_valve_bases"][0]
    restored = proportioned_basis_snapshot_from_dict_v1(payload)
    assert restored is not None
    assert restored.committed_point_valve_bases == snapshot.committed_point_valve_bases

    project.hydronic_proportioned_basis_snapshot = snapshot
    restored_project = ProjectState.from_dict(project.to_dict())
    restored_snapshot = restored_project.hydronic_proportioned_basis_snapshot
    assert restored_snapshot is not None
    assert restored_snapshot.committed_point_valve_bases == snapshot.committed_point_valve_bases

    old_payload = dict(payload)
    old_payload.pop("committed_point_valve_bases")
    old_payload.pop("point_valve_basis_status")
    restored_old = proportioned_basis_snapshot_from_dict_v1(old_payload)
    assert restored_old is not None
    assert restored_old.committed_point_valve_bases == ()

    blocked = build_proportioned_basis_snapshot_v1(
        project,
        point_commit_readiness=PointProportioningCommitReadinessV1(
            ready=False,
            blockers=("Manual point approval required",),
        ),
    )
    assert blocked.ready is False
    assert blocked.snapshot is None

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "point_commit_readiness=point_commit_readiness" in adapter_source
    assert '"item": "Committed point-valve basis"' in adapter_source

    print("OK — H-S51-B committed point-valve basis snapshot evidence passed.")


if __name__ == "__main__":
    main()
