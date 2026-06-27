from HVAC.project.project_state import ProjectState

from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    build_proportioned_basis_snapshot_v1,
    proportioned_basis_snapshot_from_dict_v1,
    proportioned_basis_snapshot_to_dict_v1,
)

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
    ReturnArrangementIntentV1,
)


def _project_with_return_basis(basis: str) -> ProjectState:
    project = ProjectState(
        project_id="hs26g-test",
        name="H-S26-G test",
    )

    project.hydronic_return_arrangement_intent = ReturnArrangementIntentV1(
        system_arrangement=basis,
    )

    return project


def test_undecided_basis_blocks_snapshot_commit():
    project = _project_with_return_basis(UNDECIDED)

    result = build_proportioned_basis_snapshot_v1(project)

    assert result.ready is False
    assert result.snapshot is None
    assert "Accepted return arrangement basis required" in result.blockers


def test_direct_return_basis_creates_snapshot():
    project = _project_with_return_basis(DIRECT_RETURN)

    result = build_proportioned_basis_snapshot_v1(project)

    assert result.ready is True
    assert result.snapshot is not None
    assert result.snapshot.return_arrangement_basis == DIRECT_RETURN
    assert result.snapshot.status == "COMMITTED_BASIS_ONLY"
    assert "no pump" in result.snapshot.note


def test_reverse_return_basis_creates_snapshot():
    project = _project_with_return_basis(REVERSE_RETURN)

    result = build_proportioned_basis_snapshot_v1(project)

    assert result.ready is True
    assert result.snapshot is not None
    assert result.snapshot.return_arrangement_basis == REVERSE_RETURN
    assert result.snapshot.status == "COMMITTED_BASIS_ONLY"
    assert "final Proportioned result" in result.snapshot.note


def test_snapshot_dict_round_trip():
    project = _project_with_return_basis(REVERSE_RETURN)

    result = build_proportioned_basis_snapshot_v1(project)
    data = proportioned_basis_snapshot_to_dict_v1(result.snapshot)
    restored = proportioned_basis_snapshot_from_dict_v1(data)

    assert restored is not None
    assert restored.return_arrangement_basis == REVERSE_RETURN
    assert restored.status == "COMMITTED_BASIS_ONLY"
    assert restored.schema == "proportioned_basis_snapshot_v1"


if __name__ == "__main__":
    test_undecided_basis_blocks_snapshot_commit()
    test_direct_return_basis_creates_snapshot()
    test_reverse_return_basis_creates_snapshot()
    test_snapshot_dict_round_trip()

    print("OK — H-S26-G proportioned basis snapshot backend is ready.")
