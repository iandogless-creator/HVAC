# ======================================================================
# HVAC/dev/test_hs38a1_scoped_rr_length_intent_resolver_v1.py
# H-S38-A1 — Scoped RR length intent persistence and resolution
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.effective_rr_length_basis_resolver_v1 import (
    BRANCH_SUBLEG_SCOPE,
    COMMON_SUBLEG_SCOPE,
    DOWNSTREAM_PROXY,
    LEG_SCOPE,
    MANUAL_ALLOWANCE,
    PHYSICAL_LOOP_ZERO_EXTRA,
    SYSTEM_SCOPE,
    resolve_effective_rr_added_length_basis_v1,
    resolve_leg_rr_added_length_basis_v1,
    resolve_subleg_rr_added_length_basis_v1,
    resolve_system_rr_added_length_basis_v1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    INHERIT,
    ReturnArrangementIntentV1,
    return_arrangement_intent_from_dict_v1,
    return_arrangement_intent_to_dict_v1,
)


LEG_ID = "leg-001"
COMMON_ID = "leg-001-primary-subleg"
BRANCH_ID = "leg-001-subleg-b"


def main() -> None:
    # Existing/global fields remain the System authority for old project data.
    legacy = return_arrangement_intent_from_dict_v1(
        {
            "rr_added_length_basis_mode": MANUAL_ALLOWANCE,
            "rr_added_length_m": 12.0,
        }
    )
    assert legacy.leg_rr_added_length_basis_modes == {}
    assert legacy.subleg_rr_added_length_basis_modes == {}

    system = resolve_system_rr_added_length_basis_v1(legacy)
    assert system.scope == SYSTEM_SCOPE
    assert system.effective_basis_mode == MANUAL_ALLOWANCE
    assert system.effective_added_length_m == 12.0

    inherited_leg = resolve_leg_rr_added_length_basis_v1(
        legacy,
        leg_id=LEG_ID,
    )
    assert inherited_leg.scope == LEG_SCOPE
    assert inherited_leg.explicit_basis_mode == INHERIT
    assert inherited_leg.effective_basis_mode == MANUAL_ALLOWANCE
    assert inherited_leg.effective_added_length_m == 12.0

    # Leg override supersedes System; it is not added to System.
    legacy.set_leg_rr_added_length_override(
        LEG_ID,
        DOWNSTREAM_PROXY,
        20.0,
    )
    leg = resolve_leg_rr_added_length_basis_v1(legacy, leg_id=LEG_ID)
    assert leg.effective_basis_mode == DOWNSTREAM_PROXY
    assert leg.effective_added_length_m == 20.0
    assert leg.source == "leg override"

    common_inherits_leg = resolve_subleg_rr_added_length_basis_v1(
        legacy,
        leg_id=LEG_ID,
        subleg_id=COMMON_ID,
    )
    assert common_inherits_leg.scope == COMMON_SUBLEG_SCOPE
    assert common_inherits_leg.effective_basis_mode == DOWNSTREAM_PROXY
    assert common_inherits_leg.effective_added_length_m == 20.0

    # Common subleg override becomes the branch parent authority.
    legacy.set_subleg_rr_added_length_override(
        COMMON_ID,
        MANUAL_ALLOWANCE,
        9.0,
    )
    branch_inherits_common = resolve_subleg_rr_added_length_basis_v1(
        legacy,
        leg_id=LEG_ID,
        subleg_id=BRANCH_ID,
        parent_subleg_id=COMMON_ID,
    )
    assert branch_inherits_common.scope == BRANCH_SUBLEG_SCOPE
    assert branch_inherits_common.effective_basis_mode == MANUAL_ALLOWANCE
    assert branch_inherits_common.effective_added_length_m == 9.0
    assert branch_inherits_common.inherited_from == COMMON_ID

    # Branch override is the one effective value: no 12 + 20 + 9 + 4 sum.
    legacy.set_subleg_rr_added_length_override(
        BRANCH_ID,
        MANUAL_ALLOWANCE,
        4.0,
    )
    branch = resolve_effective_rr_added_length_basis_v1(
        legacy,
        scope=BRANCH_SUBLEG_SCOPE,
        leg_id=LEG_ID,
        subleg_id=BRANCH_ID,
        parent_subleg_id=COMMON_ID,
    )
    assert branch.effective_added_length_m == 4.0
    assert branch.manual_allowance_active is True
    assert branch.source == "subleg override"

    payload = return_arrangement_intent_to_dict_v1(legacy)
    assert payload["rr_added_length_basis_mode"] == MANUAL_ALLOWANCE
    assert payload["rr_added_length_m"] == 12.0
    assert payload["leg_rr_added_length_basis_modes"][LEG_ID] == DOWNSTREAM_PROXY
    assert payload["subleg_rr_added_lengths_m"][COMMON_ID] == 9.0
    assert payload["subleg_rr_added_lengths_m"][BRANCH_ID] == 4.0

    restored = return_arrangement_intent_from_dict_v1(payload)
    restored_branch = resolve_subleg_rr_added_length_basis_v1(
        restored,
        leg_id=LEG_ID,
        subleg_id=BRANCH_ID,
        parent_subleg_id=COMMON_ID,
    )
    assert restored_branch.effective_added_length_m == 4.0

    restored.clear_subleg_rr_added_length_override(BRANCH_ID)
    cleared_branch = resolve_subleg_rr_added_length_basis_v1(
        restored,
        leg_id=LEG_ID,
        subleg_id=BRANCH_ID,
        parent_subleg_id=COMMON_ID,
    )
    assert cleared_branch.effective_added_length_m == 9.0
    assert cleared_branch.source == "inherit parent subleg"

    restored.clear_subleg_rr_added_length_override(COMMON_ID)
    common_after_clear = resolve_effective_rr_added_length_basis_v1(
        restored,
        scope=COMMON_SUBLEG_SCOPE,
        leg_id=LEG_ID,
        subleg_id=COMMON_ID,
    )
    assert common_after_clear.effective_basis_mode == DOWNSTREAM_PROXY
    assert common_after_clear.effective_added_length_m == 20.0

    restored.clear_leg_rr_added_length_override(LEG_ID)
    leg_after_clear = resolve_effective_rr_added_length_basis_v1(
        restored,
        scope=LEG_SCOPE,
        leg_id=LEG_ID,
    )
    assert leg_after_clear.effective_basis_mode == MANUAL_ALLOWANCE
    assert leg_after_clear.effective_added_length_m == 12.0

    default_system = resolve_effective_rr_added_length_basis_v1(
        ReturnArrangementIntentV1(),
        scope=SYSTEM_SCOPE,
    )
    assert default_system.effective_basis_mode == PHYSICAL_LOOP_ZERO_EXTRA
    assert default_system.effective_added_length_m == 0.0

    try:
        restored.set_leg_rr_added_length_override(LEG_ID, "not-a-mode")
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown scoped RR basis mode was not rejected")

    print(
        "OK — H-S38-A1 scoped RR added-length intent/resolution passed."
    )


if __name__ == "__main__":
    main()
