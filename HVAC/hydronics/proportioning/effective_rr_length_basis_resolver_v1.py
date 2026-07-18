# ======================================================================
# HVAC/hydronics/proportioning/effective_rr_length_basis_resolver_v1.py
# H-S38-A1 — Effective scoped RR added-length basis resolver
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    INHERIT,
    ReturnArrangementIntentV1,
    _normalise_rr_added_length_basis_mode_v1,
    _normalise_rr_added_length_m_v1,
)


SYSTEM_SCOPE = "SYSTEM"
LEG_SCOPE = "LEG"
COMMON_SUBLEG_SCOPE = "COMMON_SUBLEG"
BRANCH_SUBLEG_SCOPE = "BRANCH_SUBLEG"

PHYSICAL_LOOP_ZERO_EXTRA = "physical_loop_zero_extra"
DOWNSTREAM_PROXY = "downstream_proxy"
MANUAL_ALLOWANCE = "manual_allowance"


@dataclass(frozen=True, slots=True)
class EffectiveRRAddedLengthBasisV1:
    """One most-specific RR added-length intent basis.

    ``effective_added_length_m`` is the configured numeric allowance attached
    to the effective scope. It is consumed only by ``manual_allowance``;
    downstream-proxy length remains a later route calculation.
    """

    scope: str
    leg_id: str = ""
    subleg_id: str = ""
    parent_subleg_id: str = ""

    explicit_basis_mode: str = INHERIT
    explicit_added_length_m: float | None = None

    effective_basis_mode: str = PHYSICAL_LOOP_ZERO_EXTRA
    effective_added_length_m: float = 0.0

    source: str = "system"
    inherited_from: str = ""
    status: str = ""

    @property
    def manual_allowance_active(self) -> bool:
        return self.effective_basis_mode == MANUAL_ALLOWANCE


def resolve_system_rr_added_length_basis_v1(
    intent: ReturnArrangementIntentV1 | None,
) -> EffectiveRRAddedLengthBasisV1:
    if intent is None:
        intent = ReturnArrangementIntentV1()

    mode = _normalise_rr_added_length_basis_mode_v1(
        getattr(intent, "rr_added_length_basis_mode", None)
    )
    added_length_m = _normalise_rr_added_length_m_v1(
        getattr(intent, "rr_added_length_m", 0.0)
    )

    return EffectiveRRAddedLengthBasisV1(
        scope=SYSTEM_SCOPE,
        explicit_basis_mode=mode,
        explicit_added_length_m=added_length_m,
        effective_basis_mode=mode,
        effective_added_length_m=added_length_m,
        source="system",
        inherited_from="",
        status="System RR added-length basis applied.",
    )


def resolve_leg_rr_added_length_basis_v1(
    intent: ReturnArrangementIntentV1 | None,
    *,
    leg_id: str,
) -> EffectiveRRAddedLengthBasisV1:
    if intent is None:
        intent = ReturnArrangementIntentV1()

    key = _required_scope_id_v1(leg_id, label="leg_id")
    modes = dict(
        getattr(intent, "leg_rr_added_length_basis_modes", {}) or {}
    )
    lengths = dict(getattr(intent, "leg_rr_added_lengths_m", {}) or {})

    if key in modes:
        mode = _normalise_rr_added_length_basis_mode_v1(modes.get(key))
        added_length_m = _normalise_rr_added_length_m_v1(lengths.get(key))
        return EffectiveRRAddedLengthBasisV1(
            scope=LEG_SCOPE,
            leg_id=key,
            explicit_basis_mode=mode,
            explicit_added_length_m=added_length_m,
            effective_basis_mode=mode,
            effective_added_length_m=added_length_m,
            source="leg override",
            inherited_from="",
            status="Leg RR added-length override applied.",
        )

    parent = resolve_system_rr_added_length_basis_v1(intent)
    return EffectiveRRAddedLengthBasisV1(
        scope=LEG_SCOPE,
        leg_id=key,
        explicit_basis_mode=INHERIT,
        explicit_added_length_m=None,
        effective_basis_mode=parent.effective_basis_mode,
        effective_added_length_m=parent.effective_added_length_m,
        source="inherit system",
        inherited_from="system",
        status="Leg inherits System RR added-length basis.",
    )


def resolve_subleg_rr_added_length_basis_v1(
    intent: ReturnArrangementIntentV1 | None,
    *,
    leg_id: str,
    subleg_id: str,
    parent_subleg_id: str = "",
) -> EffectiveRRAddedLengthBasisV1:
    if intent is None:
        intent = ReturnArrangementIntentV1()

    leg_key = _required_scope_id_v1(leg_id, label="leg_id")
    subleg_key = _required_scope_id_v1(subleg_id, label="subleg_id")
    parent_key = str(parent_subleg_id or "").strip()

    modes = dict(
        getattr(intent, "subleg_rr_added_length_basis_modes", {}) or {}
    )
    lengths = dict(getattr(intent, "subleg_rr_added_lengths_m", {}) or {})

    scope = BRANCH_SUBLEG_SCOPE if parent_key else COMMON_SUBLEG_SCOPE

    if subleg_key in modes:
        mode = _normalise_rr_added_length_basis_mode_v1(
            modes.get(subleg_key)
        )
        added_length_m = _normalise_rr_added_length_m_v1(
            lengths.get(subleg_key)
        )
        return EffectiveRRAddedLengthBasisV1(
            scope=scope,
            leg_id=leg_key,
            subleg_id=subleg_key,
            parent_subleg_id=parent_key,
            explicit_basis_mode=mode,
            explicit_added_length_m=added_length_m,
            effective_basis_mode=mode,
            effective_added_length_m=added_length_m,
            source="subleg override",
            inherited_from="",
            status="Subleg RR added-length override applied.",
        )

    if parent_key:
        parent = resolve_subleg_rr_added_length_basis_v1(
            intent,
            leg_id=leg_key,
            subleg_id=parent_key,
        )
        inherited_from = parent_key
        source = "inherit parent subleg"
        status = "Branch subleg inherits parent RR added-length basis."
    else:
        parent = resolve_leg_rr_added_length_basis_v1(
            intent,
            leg_id=leg_key,
        )
        inherited_from = leg_key
        source = "inherit leg"
        status = "Common subleg inherits Leg RR added-length basis."

    return EffectiveRRAddedLengthBasisV1(
        scope=scope,
        leg_id=leg_key,
        subleg_id=subleg_key,
        parent_subleg_id=parent_key,
        explicit_basis_mode=INHERIT,
        explicit_added_length_m=None,
        effective_basis_mode=parent.effective_basis_mode,
        effective_added_length_m=parent.effective_added_length_m,
        source=source,
        inherited_from=inherited_from,
        status=status,
    )


def resolve_effective_rr_added_length_basis_v1(
    intent: ReturnArrangementIntentV1 | None,
    *,
    scope: str,
    leg_id: str = "",
    subleg_id: str = "",
    parent_subleg_id: str = "",
) -> EffectiveRRAddedLengthBasisV1:
    """Dispatch System/Leg/Common/Branch RR length-basis resolution."""
    scope_key = str(scope or "").strip().upper()

    if scope_key == SYSTEM_SCOPE:
        return resolve_system_rr_added_length_basis_v1(intent)
    if scope_key == LEG_SCOPE:
        return resolve_leg_rr_added_length_basis_v1(intent, leg_id=leg_id)
    if scope_key in {COMMON_SUBLEG_SCOPE, BRANCH_SUBLEG_SCOPE}:
        return resolve_subleg_rr_added_length_basis_v1(
            intent,
            leg_id=leg_id,
            subleg_id=subleg_id,
            parent_subleg_id=(
                parent_subleg_id
                if scope_key == BRANCH_SUBLEG_SCOPE
                else ""
            ),
        )

    raise ValueError(f"Unknown RR added-length scope: {scope}")


def _required_scope_id_v1(value: object, *, label: str) -> str:
    key = str(value or "").strip()
    if not key:
        raise ValueError(f"{label} is required")
    return key
