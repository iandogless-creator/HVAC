from HVAC.project.project_state import ProjectState

from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    REVERSE_RETURN,
)


def test_projectstate_round_trips_proportioned_basis_snapshot():
    project = ProjectState(
        project_id="hs26g-projectstate-test",
        name="H-S26-G ProjectState test",
    )

    project.hydronic_proportioned_basis_snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis=REVERSE_RETURN,
        return_arrangement_status=(
            "System return arrangement accepted: Reverse return"
        ),
        index_room_id="room-index",
        index_room_label="Index Room",
        terminal_room_id="room-index",
        terminal_room_label="Index Room",
        terminal_alignment_status="OK — index room is terminal",
        basis_mode="TOTAL_INDEX_LENGTH",
        total_index_length_label="42.0 m",
        nominal_gradient_label="150.0 Δp/m",
    )

    data = project.to_dict()
    restored = ProjectState.from_dict(data)

    snapshot = restored.hydronic_proportioned_basis_snapshot

    assert snapshot is not None
    assert snapshot.schema == "proportioned_basis_snapshot_v1"
    assert snapshot.status == "COMMITTED_BASIS_ONLY"
    assert snapshot.return_arrangement_basis == REVERSE_RETURN
    assert snapshot.index_room_id == "room-index"
    assert snapshot.terminal_alignment_status == "OK — index room is terminal"
    assert "no pump" in snapshot.note


if __name__ == "__main__":
    test_projectstate_round_trips_proportioned_basis_snapshot()

    print(
        "OK — H-S26-G ProjectState proportioned basis snapshot round-trip passed."
    )
