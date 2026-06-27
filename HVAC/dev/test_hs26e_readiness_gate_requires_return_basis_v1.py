from HVAC.project.project_state import ProjectState

from HVAC.hydronics.proportioning.proportioning_readiness_v1 import (
    build_proportioning_readiness_v1,
)

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
    ReturnArrangementIntentV1,
)


def _project_with_return_basis(basis: str) -> ProjectState:
    project = ProjectState(
        project_id="hs26e-test",
        name="H-S26-E test",
    )

    project.hydronic_return_arrangement_intent = ReturnArrangementIntentV1(
        system_arrangement=basis,
    )

    return project


def test_undecided_return_basis_blocks_readiness_gate():
    project = _project_with_return_basis(UNDECIDED)

    readiness = build_proportioning_readiness_v1(project)

    assert readiness.return_arrangement_basis_ready is False
    assert readiness.return_arrangement_basis_label == UNDECIDED
    assert "Accepted return arrangement basis required" in (
        readiness.proportioning_status
    )


def test_direct_return_basis_passes_readiness_gate():
    project = _project_with_return_basis(DIRECT_RETURN)

    readiness = build_proportioning_readiness_v1(project)

    assert readiness.return_arrangement_basis_ready is True
    assert readiness.return_arrangement_basis_label == DIRECT_RETURN
    assert "accepted return arrangement basis available" in (
        readiness.proportioning_status
    )


def test_reverse_return_basis_passes_readiness_gate():
    project = _project_with_return_basis(REVERSE_RETURN)

    readiness = build_proportioning_readiness_v1(project)

    assert readiness.return_arrangement_basis_ready is True
    assert readiness.return_arrangement_basis_label == REVERSE_RETURN
    assert "accepted return arrangement basis available" in (
        readiness.proportioning_status
    )


if __name__ == "__main__":
    test_undecided_return_basis_blocks_readiness_gate()
    test_direct_return_basis_passes_readiness_gate()
    test_reverse_return_basis_passes_readiness_gate()

    print("OK — H-S26-E readiness gate includes accepted return basis.")
