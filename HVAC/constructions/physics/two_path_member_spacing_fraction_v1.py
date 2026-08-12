from __future__ import annotations

from dataclasses import dataclass, replace
import math


CALCULATED_REPEATING_MEMBER_FRACTION = "calculated_repeating_member_fraction"
DECLARED_EFFECTIVE_MEMBER_FRACTION = "declared_effective_member_fraction"
MEMBER_FRACTION_BASES = frozenset({
    CALCULATED_REPEATING_MEMBER_FRACTION,
    DECLARED_EFFECTIVE_MEMBER_FRACTION,
})


@dataclass(frozen=True, slots=True)
class TwoPathMemberSpacingIntentV1:
    member_path_id: str
    clear_path_id: str
    member_label: str
    member_width_m: float
    member_centres_m: float
    controlling_basis: str = CALCULATED_REPEATING_MEMBER_FRACTION
    declared_effective_member_fraction: float | None = None
    source_note: str = ""


@dataclass(frozen=True, slots=True)
class TwoPathMemberSpacingFractionV1:
    ready: bool
    intent: TwoPathMemberSpacingIntentV1 | None = None
    calculated_repeating_member_fraction: float | None = None
    controlling_member_fraction: float | None = None
    controlling_clear_fraction: float | None = None
    blockers: tuple[str, ...] = ()
    status: str = "Two-path member fraction not resolved"


def resolve_two_path_member_spacing_fraction_v1(
    intent: TwoPathMemberSpacingIntentV1,
) -> TwoPathMemberSpacingFractionV1:
    blockers: list[str] = []
    width = _positive(intent.member_width_m, "Member width", blockers)
    centres = _positive(intent.member_centres_m, "Member centres", blockers)
    if width is not None and centres is not None and width >= centres:
        blockers.append("Member width must be less than member centres")
    basis = str(intent.controlling_basis or "")
    if basis not in MEMBER_FRACTION_BASES:
        blockers.append("Recognised member-fraction basis is required")
    if not str(intent.member_path_id or "").strip():
        blockers.append("Member path identity is required")
    if not str(intent.clear_path_id or "").strip():
        blockers.append("Clear path identity is required")
    if intent.member_path_id == intent.clear_path_id:
        blockers.append("Member and clear paths must be different")

    calculated = None if width is None or centres is None else width / centres
    declared = None
    if intent.declared_effective_member_fraction is not None:
        declared = _fraction(
            intent.declared_effective_member_fraction,
            "Declared effective member fraction",
            blockers,
        )
    if basis == DECLARED_EFFECTIVE_MEMBER_FRACTION and declared is None:
        blockers.append("Declared effective member fraction is required by the selected basis")
    if blockers:
        return TwoPathMemberSpacingFractionV1(
            ready=False,
            intent=intent,
            calculated_repeating_member_fraction=calculated,
            blockers=tuple(dict.fromkeys(blockers)),
            status="Blocked — two-path member-spacing evidence is incomplete",
        )
    controlling = calculated if basis == CALCULATED_REPEATING_MEMBER_FRACTION else declared
    return TwoPathMemberSpacingFractionV1(
        ready=True,
        intent=intent,
        calculated_repeating_member_fraction=calculated,
        controlling_member_fraction=controlling,
        controlling_clear_fraction=1.0 - controlling,
        status="Ready — two-path member fraction resolved from explicit geometry/basis",
    )


def _positive(value: object, label: str, blockers: list[str]) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        blockers.append(f"{label} must be numeric")
        return None
    if not math.isfinite(result) or result <= 0.0:
        blockers.append(f"{label} must be finite and positive")
        return None
    return result


def _fraction(value: object, label: str, blockers: list[str]) -> float | None:
    result = _positive(value, label, blockers)
    if result is not None and result >= 1.0:
        blockers.append(f"{label} must be less than 1")
        return None
    return result


@dataclass(frozen=True, slots=True)
class TwoPathMemberSpacingCandidateUpdateV1:
    ready: bool
    evidence: object | None = None
    fraction: TwoPathMemberSpacingFractionV1 | None = None
    blockers: tuple[str, ...] = ()
    status: str = "Two-path member-spacing candidate not updated"


def apply_two_path_member_spacing_fraction_v1(evidence, intent):
    """Apply one resolved member fraction to both candidate paths atomically."""

    from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
        validate_shared_construction_layer_path_evidence_v1,
    )

    fraction = resolve_two_path_member_spacing_fraction_v1(intent)
    if not fraction.ready:
        return TwoPathMemberSpacingCandidateUpdateV1(
            ready=False,
            evidence=evidence,
            fraction=fraction,
            blockers=fraction.blockers,
            status=fraction.status,
        )
    if evidence is None:
        blockers = ("Construction candidate evidence is required",)
        return TwoPathMemberSpacingCandidateUpdateV1(
            ready=False,
            fraction=fraction,
            blockers=blockers,
            status="Blocked — construction candidate evidence is required",
        )
    path_ids = {path.path_id for path in evidence.paths}
    required = {intent.member_path_id, intent.clear_path_id}
    if len(evidence.paths) != 2 or path_ids != required:
        blockers = (
            "Member-spacing control requires exactly the declared member and clear paths",
        )
        return TwoPathMemberSpacingCandidateUpdateV1(
            ready=False,
            evidence=evidence,
            fraction=fraction,
            blockers=blockers,
            status="Blocked — candidate paths do not match member-spacing intent",
        )
    updated = replace(
        evidence,
        paths=tuple(
            replace(
                path,
                area_fraction=(
                    fraction.controlling_member_fraction
                    if path.path_id == intent.member_path_id
                    else fraction.controlling_clear_fraction
                ),
            )
            for path in evidence.paths
        ),
    )
    validation = validate_shared_construction_layer_path_evidence_v1(updated)
    if not validation.ready:
        return TwoPathMemberSpacingCandidateUpdateV1(
            ready=False,
            evidence=evidence,
            fraction=fraction,
            blockers=validation.blockers,
            status="Blocked — updated two-path candidate is invalid",
        )
    return TwoPathMemberSpacingCandidateUpdateV1(
        ready=True,
        evidence=updated,
        fraction=fraction,
        status="Ready — both candidate path fractions updated atomically",
    )
