from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
    INHERIT,
    ReturnArrangementIntentV1,
    return_arrangement_intent_to_dict_v1,
    return_arrangement_intent_from_dict_v1,
    resolve_system_return_arrangement_v1,
    resolve_leg_return_arrangement_v1,
    resolve_subleg_return_arrangement_v1,
)


def test_round_trip_system_direct_leg_reverse_subleg_direct():
    original = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
        leg_arrangements={
            "leg-001": REVERSE_RETURN,
            "leg-002": INHERIT,
        },
        subleg_arrangements={
            "leg-001-primary-subleg": DIRECT_RETURN,
            "leg-001-subleg-b": INHERIT,
        },
    )

    data = return_arrangement_intent_to_dict_v1(original)
    restored = return_arrangement_intent_from_dict_v1(data)

    assert restored.system_arrangement == DIRECT_RETURN
    assert restored.leg_arrangements["leg-001"] == REVERSE_RETURN
    assert restored.leg_arrangements["leg-002"] == INHERIT
    assert restored.subleg_arrangements["leg-001-primary-subleg"] == DIRECT_RETURN
    assert restored.subleg_arrangements["leg-001-subleg-b"] == INHERIT

    system = resolve_system_return_arrangement_v1(restored)
    leg = resolve_leg_return_arrangement_v1(
        restored,
        leg_id="leg-001",
    )
    subleg = resolve_subleg_return_arrangement_v1(
        restored,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
    )

    assert system.resolved_arrangement == DIRECT_RETURN
    assert system.accepted is True

    assert leg.resolved_arrangement == REVERSE_RETURN
    assert leg.accepted is True

    assert subleg.resolved_arrangement == DIRECT_RETURN
    assert subleg.accepted is True


def test_missing_or_bad_data_restores_safe_default():
    restored = return_arrangement_intent_from_dict_v1(
        {
            "system_arrangement": "nonsense",
            "leg_arrangements": {
                "leg-001": "also bad",
            },
            "subleg_arrangements": {
                "subleg-001": "bad again",
            },
        }
    )

    assert restored.system_arrangement == UNDECIDED
    assert restored.leg_arrangements["leg-001"] == INHERIT
    assert restored.subleg_arrangements["subleg-001"] == INHERIT


def test_none_restores_default_undecided():
    restored = return_arrangement_intent_from_dict_v1(None)

    assert restored.system_arrangement == UNDECIDED
    assert restored.leg_arrangements == {}
    assert restored.subleg_arrangements == {}


if __name__ == "__main__":
    test_round_trip_system_direct_leg_reverse_subleg_direct()
    test_missing_or_bad_data_restores_safe_default()
    test_none_restores_default_undecided()

    print("OK — H-S26-D return arrangement intent persistence helpers are ready.")
