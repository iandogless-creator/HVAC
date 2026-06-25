# ======================================================================
# HVAC/dev/test_hs26a_return_arrangement_acceptance_intent_v1.py
# H-S26-A — Return arrangement acceptance intent
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    INHERIT,
    REVERSE_RETURN,
    UNDECIDED,
    ReturnArrangementIntentV1,
    resolve_leg_return_arrangement_v1,
    resolve_subleg_return_arrangement_v1,
    resolve_system_return_arrangement_v1,
)


def main() -> None:
    print()
    print("H-S26-A — Return arrangement acceptance intent")
    print("=============================================")

    # --------------------------------------------------
    # 1. Default system is undecided.
    # --------------------------------------------------
    default_intent = ReturnArrangementIntentV1()

    system_default = resolve_system_return_arrangement_v1(default_intent)

    print("default system:", system_default.resolved_arrangement, system_default.status)

    assert system_default.resolved_arrangement == UNDECIDED
    assert system_default.accepted is False

    # --------------------------------------------------
    # 2. System direct return can be accepted.
    # --------------------------------------------------
    system_direct_intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
    )

    system_direct = resolve_system_return_arrangement_v1(system_direct_intent)
    leg_inherited = resolve_leg_return_arrangement_v1(
        system_direct_intent,
        leg_id="leg-001",
    )
    primary_subleg_inherited = resolve_subleg_return_arrangement_v1(
        system_direct_intent,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
    )

    print("system direct:", system_direct.resolved_arrangement, system_direct.status)
    print("leg inherited:", leg_inherited.resolved_arrangement, leg_inherited.status)
    print(
        "primary subleg inherited:",
        primary_subleg_inherited.resolved_arrangement,
        primary_subleg_inherited.status,
    )

    assert system_direct.resolved_arrangement == DIRECT_RETURN
    assert system_direct.accepted is True

    assert leg_inherited.arrangement == INHERIT
    assert leg_inherited.resolved_arrangement == DIRECT_RETURN
    assert leg_inherited.inherited_from == "system"

    assert primary_subleg_inherited.arrangement == INHERIT
    assert primary_subleg_inherited.resolved_arrangement == DIRECT_RETURN
    assert primary_subleg_inherited.inherited_from == "leg-001"

    # --------------------------------------------------
    # 3. Leg can override system.
    # --------------------------------------------------
    leg_override_intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
        leg_arrangements={
            "leg-001": REVERSE_RETURN,
        },
    )

    leg_override = resolve_leg_return_arrangement_v1(
        leg_override_intent,
        leg_id="leg-001",
    )
    subleg_from_leg_override = resolve_subleg_return_arrangement_v1(
        leg_override_intent,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
    )

    print("leg override:", leg_override.resolved_arrangement, leg_override.status)
    print(
        "subleg from leg override:",
        subleg_from_leg_override.resolved_arrangement,
        subleg_from_leg_override.status,
    )

    assert leg_override.resolved_arrangement == REVERSE_RETURN
    assert leg_override.accepted is True
    assert leg_override.source == "user"

    assert subleg_from_leg_override.resolved_arrangement == REVERSE_RETURN
    assert subleg_from_leg_override.source == "inherited"

    # --------------------------------------------------
    # 4. Branch / secondary subleg inherits parent subleg by default.
    # --------------------------------------------------
    branch_inherit_intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
        subleg_arrangements={
            "leg-001-primary-subleg": REVERSE_RETURN,
            # branch is deliberately omitted: default must inherit parent
        },
    )

    branch_basis = resolve_subleg_return_arrangement_v1(
        branch_inherit_intent,
        leg_id="leg-001",
        subleg_id="leg-001-subleg-b",
        parent_subleg_id="leg-001-primary-subleg",
    )

    print("branch inherited:", branch_basis.resolved_arrangement, branch_basis.status)

    assert branch_basis.arrangement == INHERIT
    assert branch_basis.resolved_arrangement == REVERSE_RETURN
    assert branch_basis.inherited_from == "leg-001-primary-subleg"

    # --------------------------------------------------
    # 5. Branch / secondary subleg can explicitly override parent.
    # --------------------------------------------------
    branch_override_intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
        subleg_arrangements={
            "leg-001-primary-subleg": REVERSE_RETURN,
            "leg-001-subleg-b": DIRECT_RETURN,
        },
    )

    branch_override = resolve_subleg_return_arrangement_v1(
        branch_override_intent,
        leg_id="leg-001",
        subleg_id="leg-001-subleg-b",
        parent_subleg_id="leg-001-primary-subleg",
    )

    print("branch override:", branch_override.resolved_arrangement, branch_override.status)

    assert branch_override.resolved_arrangement == DIRECT_RETURN
    assert branch_override.accepted is True
    assert branch_override.source == "user"

    print()
    print("OK — H-S26-A return arrangement hierarchy is resolved correctly.")


if __name__ == "__main__":
    main()
