# ======================================================================
# H-S66-N2B1 — Persisted committed pipe-pair vertical-order intent
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    FLOW_PIPE_V1,
    NOT_SET_UPPER_PIPE_ROLE_V1,
    RETURN_PIPE_V1,
)
from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
)
from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    build_committed_pipe_schedule_thermal_fingerprint_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


SCHEMA_V1 = "committed_pipe_pair_vertical_order_intent_v1"


@dataclass(frozen=True, slots=True)
class CommittedPipePairVerticalOrderOverrideEntryV1:
    section_id: str
    upper_pipe_role: str


@dataclass(slots=True)
class CommittedPipePairVerticalOrderIntentV1:
    """Project default plus sparse exact-section overrides.

    The project-wide choice remains valid if the committed schedule changes.
    Exact-section overrides are bound to one schedule fingerprint and must be
    cleared before they can be applied to a different committed schedule.
    """

    schema: str = SCHEMA_V1
    project_upper_pipe_role: str = NOT_SET_UPPER_PIPE_ROLE_V1
    committed_schedule_fingerprint: str = ""
    override_by_section_id: dict[
        str, CommittedPipePairVerticalOrderOverrideEntryV1
    ] = field(default_factory=dict)

    def set_project_upper_pipe_role(self, upper_pipe_role: object) -> None:
        self.project_upper_pipe_role = _project_pipe_role_v1(upper_pipe_role)

    def set_section_override(
            self,
            *,
            section_id: object,
            committed_schedule_fingerprint: object,
            upper_pipe_role: object,
    ) -> None:
        stable_section_id = _text_v1(section_id)
        fingerprint = _text_v1(committed_schedule_fingerprint)
        role = _resolved_pipe_role_v1(upper_pipe_role)
        if not stable_section_id:
            raise ValueError("Committed pipe section identity is required")
        if not fingerprint:
            raise ValueError("Committed pipe schedule fingerprint is required")
        if (
            self.committed_schedule_fingerprint
            and self.committed_schedule_fingerprint != fingerprint
        ):
            raise ValueError(
                "Persisted pipe-pair vertical-order overrides are stale; "
                "clear them before recording a different committed schedule"
            )
        self.committed_schedule_fingerprint = fingerprint
        self.override_by_section_id[stable_section_id] = (
            CommittedPipePairVerticalOrderOverrideEntryV1(
                section_id=stable_section_id,
                upper_pipe_role=role,
            )
        )

    def clear_section_override(self, section_id: object) -> bool:
        removed = self.override_by_section_id.pop(_text_v1(section_id), None)
        if not self.override_by_section_id:
            self.committed_schedule_fingerprint = ""
        return removed is not None

    def clear_all_section_overrides(self) -> None:
        self.override_by_section_id.clear()
        self.committed_schedule_fingerprint = ""

    def to_dict(self) -> dict:
        return committed_pipe_pair_vertical_order_intent_to_dict_v1(self)

    @classmethod
    def from_dict(
            cls,
            data: dict | None,
    ) -> "CommittedPipePairVerticalOrderIntentV1":
        return committed_pipe_pair_vertical_order_intent_from_dict_v1(data)


@dataclass(frozen=True, slots=True)
class EffectiveCommittedPipePairVerticalOrderV1:
    section_id: str
    external_arrangement: str
    project_upper_pipe_role: str
    effective_upper_pipe_role: str
    locally_overridden: bool
    resolved: bool
    source: str
    status: str


def build_committed_pipe_pair_vertical_order_fingerprint_v1(
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
) -> str:
    return build_committed_pipe_schedule_thermal_fingerprint_v1(
        committed_authority
    )


def set_current_committed_section_pipe_pair_vertical_order_override_v1(
        *,
        intent: CommittedPipePairVerticalOrderIntentV1,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        external_arrangement_by_section_id: Mapping[str, str],
        section_id: object,
        upper_pipe_role: object,
) -> None:
    """Record one reviewed exact-section override for stacked pipework only."""

    if not isinstance(intent, CommittedPipePairVerticalOrderIntentV1):
        raise TypeError("CommittedPipePairVerticalOrderIntentV1 required")
    _, arrangement = _resolve_exact_section_and_arrangement_v1(
        committed_authority=committed_authority,
        external_arrangement_by_section_id=external_arrangement_by_section_id,
        section_id=section_id,
    )
    if arrangement != STACKED_FLOW_RETURN_PAIR_V1:
        raise ValueError(
            "Pipe-pair vertical-order override applies only to a stacked "
            "flow/return pair"
        )
    intent.set_section_override(
        section_id=section_id,
        committed_schedule_fingerprint=(
            build_committed_pipe_pair_vertical_order_fingerprint_v1(
                committed_authority
            )
        ),
        upper_pipe_role=upper_pipe_role,
    )


def resolve_effective_committed_pipe_pair_vertical_order_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        external_arrangement_by_section_id: Mapping[str, str],
        intent: CommittedPipePairVerticalOrderIntentV1 | None,
        section_id: object,
) -> EffectiveCommittedPipePairVerticalOrderV1 | None:
    """Resolve local-over-project intent; separate RR remains dormant."""

    _, arrangement = _resolve_exact_section_and_arrangement_v1(
        committed_authority=committed_authority,
        external_arrangement_by_section_id=external_arrangement_by_section_id,
        section_id=section_id,
    )
    if arrangement == SEPARATE_PIPE_V1:
        return None

    source_intent = (
        intent
        if isinstance(intent, CommittedPipePairVerticalOrderIntentV1)
        else CommittedPipePairVerticalOrderIntentV1()
    )
    project_role = _project_pipe_role_v1(
        source_intent.project_upper_pipe_role
    )
    if source_intent.override_by_section_id:
        expected = build_committed_pipe_pair_vertical_order_fingerprint_v1(
            committed_authority
        )
        if source_intent.committed_schedule_fingerprint != expected:
            raise ValueError(
                "Persisted pipe-pair vertical-order overrides are stale for "
                "the current committed schedule"
            )

    local = source_intent.override_by_section_id.get(_text_v1(section_id))
    if local is not None:
        effective_role = _resolved_pipe_role_v1(local.upper_pipe_role)
        return EffectiveCommittedPipePairVerticalOrderV1(
            section_id=_text_v1(section_id),
            external_arrangement=arrangement,
            project_upper_pipe_role=project_role,
            effective_upper_pipe_role=effective_role,
            locally_overridden=True,
            resolved=True,
            source="Persisted exact committed-section upper-pipe role override",
            status="Ready — local committed-section vertical order resolved",
        )

    resolved = project_role in {FLOW_PIPE_V1, RETURN_PIPE_V1}
    return EffectiveCommittedPipePairVerticalOrderV1(
        section_id=_text_v1(section_id),
        external_arrangement=arrangement,
        project_upper_pipe_role=project_role,
        effective_upper_pipe_role=project_role,
        locally_overridden=False,
        resolved=resolved,
        source="Persisted project-wide upper-pipe role intent",
        status=(
            "Ready — project-wide vertical order inherited"
            if resolved
            else "Blocked — project-wide upper-pipe role is not set"
        ),
    )


def committed_pipe_pair_vertical_order_intent_to_dict_v1(
        intent: CommittedPipePairVerticalOrderIntentV1 | None,
) -> dict:
    source = (
        intent
        if isinstance(intent, CommittedPipePairVerticalOrderIntentV1)
        else CommittedPipePairVerticalOrderIntentV1()
    )
    return {
        "schema": source.schema,
        "project_upper_pipe_role": _project_pipe_role_v1(
            source.project_upper_pipe_role
        ),
        "committed_schedule_fingerprint": (
            source.committed_schedule_fingerprint
        ),
        "override_by_section_id": {
            section_id: {
                "section_id": entry.section_id,
                "upper_pipe_role": entry.upper_pipe_role,
            }
            for section_id, entry in sorted(
                source.override_by_section_id.items()
            )
        },
    }


def committed_pipe_pair_vertical_order_intent_from_dict_v1(
        data: dict | None,
) -> CommittedPipePairVerticalOrderIntentV1:
    empty = CommittedPipePairVerticalOrderIntentV1()
    if not isinstance(data, dict):
        return empty
    if _text_v1(data.get("schema") or SCHEMA_V1) != SCHEMA_V1:
        return empty
    try:
        project_role = _project_pipe_role_v1(
            data.get("project_upper_pipe_role", NOT_SET_UPPER_PIPE_ROLE_V1)
        )
    except ValueError:
        return empty
    fingerprint = _text_v1(data.get("committed_schedule_fingerprint"))
    raw_entries = data.get("override_by_section_id", {})
    if not isinstance(raw_entries, dict):
        return empty
    if raw_entries and not fingerprint:
        return empty

    parsed = CommittedPipePairVerticalOrderIntentV1(
        project_upper_pipe_role=project_role
    )
    try:
        for raw_section_id, raw_entry in sorted(
            raw_entries.items(), key=lambda item: str(item[0])
        ):
            if not isinstance(raw_entry, dict):
                return empty
            section_id = _text_v1(raw_entry.get("section_id"))
            if not section_id or section_id != _text_v1(raw_section_id):
                return empty
            parsed.set_section_override(
                section_id=section_id,
                committed_schedule_fingerprint=fingerprint,
                upper_pipe_role=raw_entry.get("upper_pipe_role"),
            )
    except (TypeError, ValueError):
        return empty
    return parsed


def _resolve_exact_section_and_arrangement_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        external_arrangement_by_section_id: Mapping[str, str],
        section_id: object,
) -> tuple[object, str]:
    if not isinstance(
        committed_authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ) or not committed_authority.ready:
        raise ValueError(
            "Ready committed proportioning hydraulic-input authority required"
        )
    stable_section_id = _text_v1(section_id)
    matches = tuple(
        row
        for row in tuple(committed_authority.sections or ())
        if _text_v1(getattr(row, "section_id", "")) == stable_section_id
    )
    if len(matches) != 1:
        raise ValueError("Exact committed pipe section identity is required")
    if not isinstance(external_arrangement_by_section_id, Mapping):
        raise ValueError("Committed external-arrangement mapping is required")
    arrangement = _text_v1(
        external_arrangement_by_section_id.get(stable_section_id)
    )
    if arrangement not in {
        STACKED_FLOW_RETURN_PAIR_V1,
        SEPARATE_PIPE_V1,
    }:
        raise ValueError("Current committed pipe external arrangement is required")
    return matches[0], arrangement


def _project_pipe_role_v1(value: object) -> str:
    role = _text_v1(value).lower()
    if role in {
        NOT_SET_UPPER_PIPE_ROLE_V1,
        FLOW_PIPE_V1,
        RETURN_PIPE_V1,
    }:
        return role
    raise ValueError("Project upper-pipe role must be not_set, flow or return")


def _resolved_pipe_role_v1(value: object) -> str:
    role = _text_v1(value).lower()
    if role in {FLOW_PIPE_V1, RETURN_PIPE_V1}:
        return role
    raise ValueError("Section upper-pipe role must be flow or return")


def _text_v1(value: object) -> str:
    return str(value or "").strip()
