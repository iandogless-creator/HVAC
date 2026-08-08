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
NOT_SET_AMBIENT_SCOPE_V1 = "not_set"


@dataclass(frozen=True, slots=True)
class CommittedPipeSectionRoomMappingEntryV1:
    section_id: str
    room_id: str | None
    ambient_scope: str = ROOM_AMBIENT_SCOPE_V1


@dataclass(slots=True)
class CommittedPipeSectionRoomMappingIntentV1:
    """Sparse explicit ambient-location choices for one committed schedule.

    Absence means Not set and is calculation-blocking.  A stored entry chooses
    either an exact ProjectState room or Environment / general space.  No
    temperature or heat-loss result is stored here.  V1 applies one location
    to the whole committed section; user-entered or adjacency-derived
    length-fraction allocation is explicitly deferred.
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
                ambient_scope=ROOM_AMBIENT_SCOPE_V1,
            )
        )

    def set_section_environment(
            self,
            *,
            section_id: object,
            committed_schedule_fingerprint: object,
    ) -> None:
        stable_section_id = _text_v1(section_id)
        fingerprint = _text_v1(committed_schedule_fingerprint)
        if not stable_section_id:
            raise ValueError("Committed pipe section identity is required")
        if not fingerprint:
            raise ValueError("Committed pipe schedule fingerprint is required")
        if (
            self.committed_schedule_fingerprint
            and self.committed_schedule_fingerprint != fingerprint
        ):
            raise ValueError(
                "Persisted pipe-section ambient locations are stale; clear "
                "them before recording a different committed schedule"
            )
        self.committed_schedule_fingerprint = fingerprint
        self.mapping_by_section_id[stable_section_id] = (
            CommittedPipeSectionRoomMappingEntryV1(
                section_id=stable_section_id,
                room_id=None,
                ambient_scope=ENVIRONMENT_AMBIENT_SCOPE_V1,
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
    explicitly_set: bool
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


def set_current_committed_pipe_section_environment_location_v1(
        *,
        intent: CommittedPipeSectionRoomMappingIntentV1,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        section_id: object,
) -> None:
    """Record an explicit Environment / general-space location."""

    if not isinstance(intent, CommittedPipeSectionRoomMappingIntentV1):
        raise TypeError("CommittedPipeSectionRoomMappingIntentV1 required")
    stable_section_id = _exact_section_id_v1(
        committed_authority, section_id
    )
    intent.set_section_environment(
        section_id=stable_section_id,
        committed_schedule_fingerprint=(
            build_committed_pipe_section_room_mapping_fingerprint_v1(
                committed_authority
            )
        ),
    )


def set_all_unset_committed_pipe_section_ambient_locations_v1(
        *,
        intent: CommittedPipeSectionRoomMappingIntentV1,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        available_room_ids: Iterable[str],
        ambient_scope: object,
        room_id: object = None,
) -> int:
    """Atomically apply one explicit location to every currently unset section."""

    if not isinstance(intent, CommittedPipeSectionRoomMappingIntentV1):
        raise TypeError("CommittedPipeSectionRoomMappingIntentV1 required")
    section_ids = _committed_section_ids_v1(committed_authority)
    if not section_ids:
        raise ValueError("Committed pipe sections are required")
    fingerprint = build_committed_pipe_section_room_mapping_fingerprint_v1(
        committed_authority
    )
    if (
        intent.mapping_by_section_id
        and intent.committed_schedule_fingerprint != fingerprint
    ):
        raise ValueError(
            "Persisted pipe-section ambient locations are stale; clear them "
            "before recording the current committed schedule"
        )
    scope = _text_v1(ambient_scope)
    stable_room_id: str | None = None
    if scope == ROOM_AMBIENT_SCOPE_V1:
        stable_room_id = _text_v1(room_id)
        if stable_room_id not in _available_room_ids_v1(available_room_ids):
            raise ValueError("Exact current ProjectState room identity is required")
    elif scope != ENVIRONMENT_AMBIENT_SCOPE_V1:
        raise ValueError(
            "Choose Environment / general space or one exact room"
        )

    pending = dict(intent.mapping_by_section_id)
    unset = [section_id for section_id in section_ids if section_id not in pending]
    for section_id in unset:
        pending[section_id] = CommittedPipeSectionRoomMappingEntryV1(
            section_id=section_id,
            room_id=stable_room_id,
            ambient_scope=scope,
        )
    if unset:
        intent.mapping_by_section_id = pending
        intent.committed_schedule_fingerprint = fingerprint
    return len(unset)


def resolve_effective_committed_pipe_section_room_mapping_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        available_room_ids: Iterable[str],
        intent: CommittedPipeSectionRoomMappingIntentV1 | None,
        section_id: object,
) -> EffectiveCommittedPipeSectionRoomMappingV1:
    """Resolve explicit room/Environment location or calculation-blocking Not set."""

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
        invalid_scopes = {
            entry.ambient_scope
            for entry in source_intent.mapping_by_section_id.values()
            if entry.ambient_scope not in {
                ROOM_AMBIENT_SCOPE_V1,
                ENVIRONMENT_AMBIENT_SCOPE_V1,
            }
        }
        if invalid_scopes:
            raise ValueError(
                "Persisted pipe-section ambient location is unsupported"
            )
        unknown_rooms = {
            entry.room_id
            for entry in source_intent.mapping_by_section_id.values()
            if entry.ambient_scope == ROOM_AMBIENT_SCOPE_V1
            and entry.room_id not in room_ids
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
            ambient_scope=NOT_SET_AMBIENT_SCOPE_V1,
            room_id=None,
            explicitly_mapped=False,
            explicitly_set=False,
            source="No committed ambient-location disposition",
            status=(
                "Blocked — ambient location is Not set; explicitly choose "
                "Environment / general space or an exact room"
            ),
        )
    if local.ambient_scope == ENVIRONMENT_AMBIENT_SCOPE_V1:
        return EffectiveCommittedPipeSectionRoomMappingV1(
            section_id=stable_section_id,
            ambient_scope=ENVIRONMENT_AMBIENT_SCOPE_V1,
            room_id=None,
            explicitly_mapped=False,
            explicitly_set=True,
            source="Persisted explicit Environment / general-space intent",
            status="Ready — explicit Environment / general-space location resolved",
        )
    return EffectiveCommittedPipeSectionRoomMappingV1(
        section_id=stable_section_id,
        ambient_scope=ROOM_AMBIENT_SCOPE_V1,
        room_id=local.room_id,
        explicitly_mapped=True,
        explicitly_set=True,
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
                "ambient_scope": entry.ambient_scope,
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
            ambient_scope = _text_v1(
                raw_entry.get("ambient_scope") or ROOM_AMBIENT_SCOPE_V1
            )
            room_id = _text_v1(raw_entry.get("room_id"))
            if not section_id or section_id != _text_v1(raw_section_id):
                return empty
            if ambient_scope == ROOM_AMBIENT_SCOPE_V1 and not room_id:
                return empty
            if ambient_scope == ROOM_AMBIENT_SCOPE_V1:
                parsed.set_section_room(
                    section_id=section_id,
                    room_id=room_id,
                    committed_schedule_fingerprint=fingerprint,
                )
            elif ambient_scope == ENVIRONMENT_AMBIENT_SCOPE_V1 and not room_id:
                parsed.set_section_environment(
                    section_id=section_id,
                    committed_schedule_fingerprint=fingerprint,
                )
            else:
                return empty
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
