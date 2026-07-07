from __future__ import annotations

from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
    build_proportioned_basis_snapshot_v1,
    proportioned_basis_snapshot_from_dict_v1,
    proportioned_basis_snapshot_to_dict_v1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    ReturnArrangementIntentV1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis="F+RR",
        return_arrangement_status="Basis: F+RR / Reverse return",
    )

    assert snapshot.basis_only_output_ready is True
    assert "basis-only" in snapshot.basis_only_output_status
    assert "final hydraulics not included" in snapshot.basis_only_output_status

    payload = proportioned_basis_snapshot_to_dict_v1(snapshot)

    assert payload is not None
    assert payload["basis_only_output_ready"] is True
    assert "basis-only" in payload["basis_only_output_status"]
    assert "final hydraulics not included" in payload["basis_only_output_status"]

    restored = proportioned_basis_snapshot_from_dict_v1(payload)

    assert restored is not None
    assert restored.basis_only_output_ready is True
    assert restored.basis_only_output_status == payload["basis_only_output_status"]

    old_payload = dict(payload)
    old_payload.pop("basis_only_output_ready")
    old_payload.pop("basis_only_output_status")

    restored_old = proportioned_basis_snapshot_from_dict_v1(old_payload)

    assert restored_old is not None
    assert restored_old.basis_only_output_ready is True
    assert "basis-only" in restored_old.basis_only_output_status

    state = ProjectState(
        project_id="hs30f-basis-only-output",
        name="H-S30-F basis-only output readiness",
    )
    state.hydronic_proportioned_basis_snapshot = snapshot

    state_payload = state.to_dict()
    raw_snapshot = state_payload.get("hydronic_proportioned_basis_snapshot") or {}

    assert raw_snapshot.get("basis_only_output_ready") is True
    assert "basis-only" in raw_snapshot.get("basis_only_output_status", "")

    restored_state = ProjectState.from_dict(state_payload)
    restored_state_snapshot = restored_state.hydronic_proportioned_basis_snapshot

    assert restored_state_snapshot is not None
    assert restored_state_snapshot.basis_only_output_ready is True
    assert "final hydraulics not included" in (
        restored_state_snapshot.basis_only_output_status
    )

    build_state = ProjectState(
        project_id="hs30f-build",
        name="H-S30-F build snapshot",
    )
    build_state.hydronic_return_arrangement_intent = ReturnArrangementIntentV1(
        system_arrangement="REVERSE_RETURN",
    )

    build_result = build_proportioned_basis_snapshot_v1(build_state)

    assert build_result.ready is True, build_result.status
    assert build_result.snapshot is not None
    assert build_result.snapshot.basis_only_output_ready is True
    assert "basis-only" in build_result.snapshot.basis_only_output_status
    assert "final hydraulics not included" in (
        build_result.snapshot.basis_only_output_status
    )

    assert "no pump" in build_result.snapshot.note
    assert "valve" in build_result.snapshot.note
    assert "pipe resizing" in build_result.snapshot.note
    assert "final Proportioned result" in build_result.snapshot.note

    print("OK — H-S30-F basis-only output readiness flag passed.")


if __name__ == "__main__":
    main()
