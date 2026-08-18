# ======================================================================
# H-S68-B1 — Room-centric paired-pipe length intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import math


SCHEMA_V1 = "room_paired_pipe_length_intent_v1"


@dataclass(frozen=True, slots=True)
class RoomPairedPipeLengthEntryV1:
    """Preliminary paired flow/return route distances for one room.

    Each value is the route distance in metres for the pipe pair, not the sum
    of the two physical pipe runs.  Branches, take-offs, committed hydraulic
    sections and calculated pipe heat loss are outside this intent.
    """

    room_id: str
    before_emitter_length_m: float | None = None
    after_emitter_length_m: float | None = None


@dataclass(slots=True)
class RoomPairedPipeLengthIntentV1:
    """Sparse room-level evidence for a simple single-emitter route model.

    Heat-source and terminal-room applicability depends on the current
    topology and is deliberately not baked into persisted data.  A later UI
    or calculation resolver must suppress the Heat Source room and the
    after-emitter value for each terminal room without inventing geometry.
    """

    schema: str = SCHEMA_V1
    lengths_by_room_id: dict[str, RoomPairedPipeLengthEntryV1] = field(
        default_factory=dict
    )

    def set_room_lengths(
            self,
            *,
            room_id: object,
            before_emitter_length_m: object = None,
            after_emitter_length_m: object = None,
    ) -> None:
        stable_room_id = _required_text_v1(room_id, "ProjectState room identity")
        before_m = _optional_length_m_v1(
            before_emitter_length_m,
            "Before-emitter paired-pipe length",
        )
        after_m = _optional_length_m_v1(
            after_emitter_length_m,
            "After-emitter paired-pipe length",
        )
        if before_m is None and after_m is None:
            self.lengths_by_room_id.pop(stable_room_id, None)
            return
        self.lengths_by_room_id[stable_room_id] = RoomPairedPipeLengthEntryV1(
            room_id=stable_room_id,
            before_emitter_length_m=before_m,
            after_emitter_length_m=after_m,
        )

    def clear_room(self, room_id: object) -> bool:
        stable_room_id = _required_text_v1(room_id, "ProjectState room identity")
        return self.lengths_by_room_id.pop(stable_room_id, None) is not None

    def clear_all(self) -> None:
        self.lengths_by_room_id.clear()

    def to_dict(self) -> dict:
        return room_paired_pipe_length_intent_to_dict_v1(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "RoomPairedPipeLengthIntentV1":
        return room_paired_pipe_length_intent_from_dict_v1(data)


def room_paired_pipe_length_intent_to_dict_v1(
        intent: RoomPairedPipeLengthIntentV1,
) -> dict:
    if not isinstance(intent, RoomPairedPipeLengthIntentV1):
        raise TypeError("RoomPairedPipeLengthIntentV1 required")
    return {
        "schema": SCHEMA_V1,
        "lengths_by_room_id": {
            room_id: {
                "room_id": entry.room_id,
                "before_emitter_length_m": entry.before_emitter_length_m,
                "after_emitter_length_m": entry.after_emitter_length_m,
            }
            for room_id, entry in sorted(intent.lengths_by_room_id.items())
        },
    }


def room_paired_pipe_length_intent_from_dict_v1(
        data: dict | None,
) -> RoomPairedPipeLengthIntentV1:
    if data is None:
        return RoomPairedPipeLengthIntentV1()
    if not isinstance(data, dict):
        raise TypeError("Room paired-pipe length intent payload must be a mapping")
    schema = str(data.get("schema", SCHEMA_V1) or "")
    if schema != SCHEMA_V1:
        raise ValueError(f"Unsupported room paired-pipe length schema: {schema!r}")

    raw_entries = data.get("lengths_by_room_id", {}) or {}
    if not isinstance(raw_entries, dict):
        raise TypeError("lengths_by_room_id must be a mapping")

    intent = RoomPairedPipeLengthIntentV1()
    for map_room_id, raw_entry in raw_entries.items():
        if not isinstance(raw_entry, dict):
            raise TypeError("Room paired-pipe length entry must be a mapping")
        stable_map_room_id = _required_text_v1(
            map_room_id,
            "Room paired-pipe mapping identity",
        )
        stable_entry_room_id = _required_text_v1(
            raw_entry.get("room_id", stable_map_room_id),
            "Room paired-pipe entry identity",
        )
        if stable_entry_room_id != stable_map_room_id:
            raise ValueError(
                "Room paired-pipe mapping identity does not match its entry"
            )
        intent.set_room_lengths(
            room_id=stable_entry_room_id,
            before_emitter_length_m=raw_entry.get(
                "before_emitter_length_m"
            ),
            after_emitter_length_m=raw_entry.get(
                "after_emitter_length_m"
            ),
        )
    return intent


def _required_text_v1(value: object, label: str) -> str:
    stable = str(value or "").strip()
    if not stable:
        raise ValueError(f"{label} is required")
    return stable


def _optional_length_m_v1(value: object, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite non-negative number")
    try:
        length_m = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{label} must be a finite non-negative number"
        ) from exc
    if not math.isfinite(length_m) or length_m < 0.0:
        raise ValueError(f"{label} must be a finite non-negative number")
    return length_m
