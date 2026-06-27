from HVAC.project.project_state import ProjectState

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    REVERSE_RETURN,
    ReturnArrangementIntentV1,
)


def test_projectstate_round_trips_return_arrangement_intent():
    project = ProjectState(
        project_id="hs26d-test",
        name="H-S26-D test",
    )

    project.hydronic_return_arrangement_intent = ReturnArrangementIntentV1(
        system_arrangement=REVERSE_RETURN,
        leg_arrangements={
            "leg-001": DIRECT_RETURN,
        },
        subleg_arrangements={
            "leg-001-subleg-b": REVERSE_RETURN,
        },
    )

    data = project.to_dict()
    restored = ProjectState.from_dict(data)

    intent = restored.hydronic_return_arrangement_intent

    assert intent is not None
    assert intent.system_arrangement == REVERSE_RETURN
    assert intent.leg_arrangements["leg-001"] == DIRECT_RETURN
    assert intent.subleg_arrangements["leg-001-subleg-b"] == REVERSE_RETURN

    print("OK — H-S26-D ProjectState return arrangement intent round-trip passed.")


if __name__ == "__main__":
    test_projectstate_round_trips_return_arrangement_intent()
