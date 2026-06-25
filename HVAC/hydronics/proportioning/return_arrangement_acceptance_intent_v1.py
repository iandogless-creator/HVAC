# ======================================================================
# HVAC/hydronics/proportioning/return_arrangement_acceptance_intent_v1.py
# H-S26-A — Return arrangement acceptance intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field


# ----------------------------------------------------------------------
# Canonical v1 return-arrangement values
# ----------------------------------------------------------------------

DIRECT_RETURN = "DIRECT_RETURN"
REVERSE_RETURN = "REVERSE_RETURN"
UNDECIDED = "UNDECIDED"
INHERIT = "INHERIT"

_RESOLVED_VALUES = {
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
}

_EXPLICIT_VALUES = {
    DIRECT_RETURN,
    REVERSE_RETURN,
}

_INTENT_VALUES = {
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
    INHERIT,
}


@dataclass(slots=True)
class ReturnArrangementIntentV1:
    """
    User/design intent for return-arrangement acceptance.

    H-S26-A boundary:
    - no balancing
    - no valve selection
    - no pump sizing
    - no pipe resizing
    - no ProjectState mutation by this helper

    Hierarchy:
    - system: Direct / Reverse / Undecided
    - leg: Direct / Reverse / Inherit system
    - subleg: Direct / Reverse / Inherit parent

    v1 rule:
    Branch/secondary sublegs inherit parent arrangement unless explicitly
    accepted otherwise.
    """

    system_arrangement: str = UNDECIDED

    # leg_id -> DIRECT_RETURN / REVERSE_RETURN / INHERIT
    leg_arrangements: dict[str, str] = field(default_factory=dict)

    # subleg_id -> DIRECT_RETURN / REVERSE_RETURN / INHERIT
    subleg_arrangements: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ResolvedReturnArrangementV1:
    """
    Resolved effective return arrangement for a scope.
    """

    scope: str = ""
    leg_id: str = ""
    subleg_id: str = ""
    parent_subleg_id: str = ""

    arrangement: str = INHERIT
    resolved_arrangement: str = UNDECIDED

    accepted: bool = False
    source: str = "default"
    inherited_from: str = ""

    status: str = ""


def _normalise_intent(value: object, *, default: str = INHERIT) -> str:
    text = str(value or "").strip().upper()

    aliases = {
        "DIRECT": DIRECT_RETURN,
        "DIRECT RETURN": DIRECT_RETURN,
        "F+R": DIRECT_RETURN,
        "FR": DIRECT_RETURN,
        "REVERSE": REVERSE_RETURN,
        "REVERSE RETURN": REVERSE_RETURN,
        "F+RR": REVERSE_RETURN,
        "FRR": REVERSE_RETURN,
        "RR": REVERSE_RETURN,
        "UNDECIDED": UNDECIDED,
        "UNKNOWN": UNDECIDED,
        "INHERIT": INHERIT,
        "INHERIT_PARENT": INHERIT,
        "INHERIT SYSTEM": INHERIT,
        "INHERIT PARENT": INHERIT,
    }

    text = aliases.get(text, text)

    if text in _INTENT_VALUES:
        return text

    return default


def _arrangement_label(value: str) -> str:
    if value == DIRECT_RETURN:
        return "Direct return"
    if value == REVERSE_RETURN:
        return "Reverse return"
    if value == UNDECIDED:
        return "Undecided"
    if value == INHERIT:
        return "Inherit"
    return str(value or "—")


def resolve_system_return_arrangement_v1(
    intent: ReturnArrangementIntentV1 | None,
) -> ResolvedReturnArrangementV1:
    arrangement = _normalise_intent(
        intent.system_arrangement if intent else UNDECIDED,
        default=UNDECIDED,
    )

    if arrangement == INHERIT:
        arrangement = UNDECIDED

    accepted = arrangement in _EXPLICIT_VALUES

    return ResolvedReturnArrangementV1(
        scope="system",
        arrangement=arrangement,
        resolved_arrangement=arrangement,
        accepted=accepted,
        source="user" if accepted else "default",
        inherited_from="",
        status=(
            f"System return arrangement accepted: {_arrangement_label(arrangement)}"
            if accepted
            else "System return arrangement undecided"
        ),
    )


def resolve_leg_return_arrangement_v1(
    intent: ReturnArrangementIntentV1 | None,
    *,
    leg_id: str,
) -> ResolvedReturnArrangementV1:
    if intent is None:
        intent = ReturnArrangementIntentV1()

    arrangement = _normalise_intent(
        intent.leg_arrangements.get(leg_id, INHERIT),
        default=INHERIT,
    )

    if arrangement in _EXPLICIT_VALUES:
        return ResolvedReturnArrangementV1(
            scope="leg",
            leg_id=leg_id,
            arrangement=arrangement,
            resolved_arrangement=arrangement,
            accepted=True,
            source="user",
            inherited_from="",
            status=(
                f"Leg return arrangement accepted: "
                f"{_arrangement_label(arrangement)}"
            ),
        )

    system_basis = resolve_system_return_arrangement_v1(intent)

    return ResolvedReturnArrangementV1(
        scope="leg",
        leg_id=leg_id,
        arrangement=INHERIT,
        resolved_arrangement=system_basis.resolved_arrangement,
        accepted=system_basis.accepted,
        source="inherited",
        inherited_from="system",
        status=(
            f"Leg inherits system return arrangement: "
            f"{_arrangement_label(system_basis.resolved_arrangement)}"
        ),
    )


def resolve_subleg_return_arrangement_v1(
    intent: ReturnArrangementIntentV1 | None,
    *,
    leg_id: str,
    subleg_id: str,
    parent_subleg_id: str = "",
) -> ResolvedReturnArrangementV1:
    if intent is None:
        intent = ReturnArrangementIntentV1()

    arrangement = _normalise_intent(
        intent.subleg_arrangements.get(subleg_id, INHERIT),
        default=INHERIT,
    )

    if arrangement in _EXPLICIT_VALUES:
        return ResolvedReturnArrangementV1(
            scope="subleg",
            leg_id=leg_id,
            subleg_id=subleg_id,
            parent_subleg_id=parent_subleg_id,
            arrangement=arrangement,
            resolved_arrangement=arrangement,
            accepted=True,
            source="user",
            inherited_from="",
            status=(
                f"Subleg return arrangement accepted: "
                f"{_arrangement_label(arrangement)}"
            ),
        )

    if parent_subleg_id:
        parent_basis = resolve_subleg_return_arrangement_v1(
            intent,
            leg_id=leg_id,
            subleg_id=parent_subleg_id,
            parent_subleg_id="",
        )

        return ResolvedReturnArrangementV1(
            scope="subleg",
            leg_id=leg_id,
            subleg_id=subleg_id,
            parent_subleg_id=parent_subleg_id,
            arrangement=INHERIT,
            resolved_arrangement=parent_basis.resolved_arrangement,
            accepted=parent_basis.accepted,
            source="inherited",
            inherited_from=parent_subleg_id,
            status=(
                f"Subleg inherits parent return arrangement: "
                f"{_arrangement_label(parent_basis.resolved_arrangement)}"
            ),
        )

    leg_basis = resolve_leg_return_arrangement_v1(
        intent,
        leg_id=leg_id,
    )

    return ResolvedReturnArrangementV1(
        scope="subleg",
        leg_id=leg_id,
        subleg_id=subleg_id,
        parent_subleg_id="",
        arrangement=INHERIT,
        resolved_arrangement=leg_basis.resolved_arrangement,
        accepted=leg_basis.accepted,
        source="inherited",
        inherited_from=leg_id,
        status=(
            f"Subleg inherits leg return arrangement: "
            f"{_arrangement_label(leg_basis.resolved_arrangement)}"
        ),
    )
