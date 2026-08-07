# ======================================================================
# H-S66-N3B — Committed pipe-section to room mapping intent
# ======================================================================

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    build_committed_pipe_schedule_thermal_fingerprint_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


SCHEMA_V1 = "committed_pipe_section_room_mapping_intent_v1"
ENVIRONMENT_AMBIENT_SCOPE_V1 = "environment"
ROOM_AMBIENT_SCOPE_V1 = "room"


@dataclass(frozen=True, slots=True)
class CommittedPipeSectionRoomMappingEntryV1:
    section_id: str
    room_id: str


@dataclass(slots=True)
class CommittedPipeSectionRoomMappingIntentV1:
    """Sparse exact-section room mappings for one committed schedule.

    Absence is meaningful: an unmapped section retains the Environment local-
    ambient fallback. Current v1 maps only to ProjectState room identities;
    non-room spaces remain on that fallback until a wider space authority
    exists. No temperature or heat-loss result is stored here.
    """

    schema: str = SCHEMA_V1
    committed_schedule_fingerprint: str = ""
    mapping_by_section_id: dict[
        str, CommittedPipeSectionRoomMappingEntryV1
    ] = field(default_factory=dict)

    def set_section_room(
            self,
            *,
            section_id: object,
            room_id: object,
            committed_schedule_fingerprint: object,
    ) -> None:
        stable_section_id = _text_v1(section_id)
        stable_room_id = _text_v1(room_id)
        fingerprint = _text_v1(committed_schedule_fingerprint)
        if not stable_section_id:
            raise ValueError("Committed pipe section identity is required")
        if not stable_room_id:
            raise ValueError("ProjectState room identity is required")
        if not fingerprint:
            raise ValueError("Committed pipe schedule fingerprint is required")
        if (
            self.committed_schedule_fingerprint
            and self.committed_schedule_fingerprint != fingerprint
        ):
            raise ValueError(
                "Persisted pipe-section room mappings are stale; clear them "
                "before recording a different committed schedule"
            )
        self.committed_schedule_fingerprint = fingerprint
        self.mapping_by_section_id[stable_section_id] = (
            CommittedPipeSectionRoomMappingEntryV1(
                section_id=stable_section_id,
                room_id=stable_room_id,
            )
        )

    def clear_section_room(self, section_id: object) -> bool:
        removed = self.mapping_by_section_id.pop(_text_v1(section_id), None)
        if not self.mapping_by_section_id:
            self.committed_schedule_fingerprint = ""
        return removed is not None

    def clear_all(self) -> None:
        self.mapping_by_section_id.clear()
        self.committed_schedule_fingerprint = ""

    def to_dict(self) -> dict:
        return committed_pipe_section_room_mapping_intent_to_dict_v1(self)

    @classmethod
    def from_dict(
            cls, data: dict | None
    ) -> "CommittedPipeSectionRoomMappingIntentV1":
        return committed_pipe_section_room_mapping_intent_from_dict_v1(data)


@dataclass(frozen=True, slots=True)
class EffectiveCommittedPipeSectionRoomMappingV1:
    section_id: str
    ambient_scope: str
    room_id: str | None
    explicitly_mapped: bool
    source: str
    status: str


def build_committed_pipe_section_room_mapping_fingerprint_v1(
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
) -> str:
    return build_committed_pipe_schedule_thermal_fingerprint_v1(
        committed_authority
    )


def set_current_committed_pipe_section_room_mapping_v1(
        *,
        intent: CommittedPipeSectionRoomMappingIntentV1,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        available_room_ids: Iterable[str],
        section_id: object,
        room_id: object,
) -> None:
    """Record one reviewed room location for one exact committed section."""

    if not isinstance(intent, CommittedPipeSectionRoomMappingIntentV1):
        raise TypeError("CommittedPipeSectionRoomMappingIntentV1 required")
    stable_section_id = _exact_section_id_v1(
        committed_authority, section_id
    )
    room_ids = _available_room_ids_v1(available_room_ids)
    stable_room_id = _text_v1(room_id)
    if stable_room_id not in room_ids:
        raise ValueError("Exact current ProjectState room identity is required")
    intent.set_section_room(
        section_id=stable_section_id,
        room_id=stable_room_id,
        committed_schedule_fingerprint=(
            build_committed_pipe_section_room_mapping_fingerprint_v1(
                committed_authority
            )
        ),
    )


def resolve_effective_committed_pipe_section_room_mapping_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        available_room_ids: Iterable[str],
        intent: CommittedPipeSectionRoomMappingIntentV1 | None,
        section_id: object,
) -> EffectiveCommittedPipeSectionRoomMappingV1:
    """Resolve exact room mapping or the explicit Environment fallback."""

    stable_section_id = _exact_section_id_v1(
        committed_authority, section_id
    )
    current_section_ids = _committed_section_ids_v1(committed_authority)
    room_ids = _available_room_ids_v1(available_room_ids)
    source_intent = (
        intent
        if isinstance(intent, CommittedPipeSectionRoomMappingIntentV1)
        else CommittedPipeSectionRoomMappingIntentV1()
    )
    if source_intent.mapping_by_section_id:
        expected = build_committed_pipe_section_room_mapping_fingerprint_v1(
            committed_authority
        )
        if source_intent.committed_schedule_fingerprint != expected:
            raise ValueError(
                "Persisted pipe-section room mappings are stale for the "
                "current committed schedule"
            )
        unknown_sections = set(source_intent.mapping_by_section_id) - set(
            current_section_ids
        )
        if unknown_sections:
            raise ValueError(
                "Persisted pipe-section room mapping has no exact current "
                "committed section"
            )
        unknown_rooms = {
            entry.room_id
            for entry in source_intent.mapping_by_section_id.values()
            if entry.room_id not in room_ids
        }
        if unknown_rooms:
            raise ValueError(
                "Persisted pipe-section room mapping refers to a missing "
                "ProjectState room"
            )

    local = source_intent.mapping_by_section_id.get(stable_section_id)
    if local is None:
        return EffectiveCommittedPipeSectionRoomMappingV1(
            section_id=stable_section_id,
            ambient_scope=ENVIRONMENT_AMBIENT_SCOPE_V1,
            room_id=None,
            explicitly_mapped=False,
            source="Explicit unmapped-section Environment ambient fallback",
            status="Ready — Environment ambient fallback retained",
        )
    return EffectiveCommittedPipeSectionRoomMappingV1(
        section_id=stable_section_id,
        ambient_scope=ROOM_AMBIENT_SCOPE_V1,
        room_id=local.room_id,
        explicitly_mapped=True,
        source="Persisted exact committed-section room mapping intent",
        status="Ready — exact committed-section room mapping resolved",
    )


def committed_pipe_section_room_mapping_intent_to_dict_v1(
        intent: CommittedPipeSectionRoomMappingIntentV1 | None,
) -> dict:
    source = (
        intent
        if isinstance(intent, CommittedPipeSectionRoomMappingIntentV1)
        else CommittedPipeSectionRoomMappingIntentV1()
    )
    return {
        "schema": source.schema,
        "committed_schedule_fingerprint": (
            source.committed_schedule_fingerprint
        ),
        "mapping_by_section_id": {
            section_id: {
                "section_id": entry.section_id,
                "room_id": entry.room_id,
            }
            for section_id, entry in sorted(
                source.mapping_by_section_id.items()
            )
        },
    }


def committed_pipe_section_room_mapping_intent_from_dict_v1(
        data: dict | None,
) -> CommittedPipeSectionRoomMappingIntentV1:
    empty = CommittedPipeSectionRoomMappingIntentV1()
    if not isinstance(data, dict):
        return empty
    if _text_v1(data.get("schema") or SCHEMA_V1) != SCHEMA_V1:
        return empty
    fingerprint = _text_v1(data.get("committed_schedule_fingerprint"))
    raw_entries = data.get("mapping_by_section_id", {})
    if not isinstance(raw_entries, dict):
        return empty
    if raw_entries and not fingerprint:
        return empty
    parsed = CommittedPipeSectionRoomMappingIntentV1()
    try:
        for raw_section_id, raw_entry in sorted(
            raw_entries.items(), key=lambda item: str(item[0])
        ):
            if not isinstance(raw_entry, dict):
                return empty
            section_id = _text_v1(raw_entry.get("section_id"))
            room_id = _text_v1(raw_entry.get("room_id"))
            if not section_id or section_id != _text_v1(raw_section_id):
                return empty
            if not room_id:
                return empty
            parsed.set_section_room(
                section_id=section_id,
                room_id=room_id,
                committed_schedule_fingerprint=fingerprint,
            )
    except (TypeError, ValueError):
        return empty
    return parsed


def _exact_section_id_v1(
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        section_id: object,
) -> str:
    stable_section_id = _text_v1(section_id)
    matches = tuple(
        value
        for value in _committed_section_ids_v1(committed_authority)
        if value == stable_section_id
    )
    if len(matches) != 1:
        raise ValueError("Exact committed pipe section identity is required")
    return matches[0]


def _committed_section_ids_v1(
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
) -> tuple[str, ...]:
    if not isinstance(
        committed_authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ) or not committed_authority.ready:
        raise ValueError(
            "Ready committed proportioning hydraulic-input authority required"
        )
    section_ids = tuple(
        _text_v1(getattr(row, "section_id", ""))
        for row in tuple(committed_authority.sections or ())
    )
    if not section_ids or any(not value for value in section_ids):
        raise ValueError("Every committed pipe section requires section_id")
    if len(set(section_ids)) != len(section_ids):
        raise ValueError("Committed pipe section identities must be unique")
    return section_ids


def _available_room_ids_v1(values: Iterable[str]) -> frozenset[str]:
    try:
        raw_values = tuple(values)
    except TypeError:
        raise ValueError("Current ProjectState room identities are required") from None
    room_ids = tuple(_text_v1(value) for value in raw_values)
    if not room_ids or any(not value for value in room_ids):
        raise ValueError("Current ProjectState room identities are required")
    if len(set(room_ids)) != len(room_ids):
        raise ValueError("ProjectState room identities must be unique")
    return frozenset(room_ids)


def _text_v1(value: object) -> str:
    return str(value or "").strip()
