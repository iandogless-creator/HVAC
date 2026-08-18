from __future__ import annotations

from HVAC.heatloss.physics.room_paired_pipe_length_intent_v1 import (
    RoomPairedPipeLengthIntentV1,
    room_paired_pipe_length_intent_from_dict_v1,
)
from HVAC.project.project_state import ProjectState


def _expect_value_error(action) -> None:
    try:
        action()
    except ValueError:
        return
    raise AssertionError("Expected ValueError")


def main() -> None:
    intent = RoomPairedPipeLengthIntentV1()
    intent.set_room_lengths(
        room_id="room-001",
        before_emitter_length_m=3.25,
        after_emitter_length_m=1.5,
    )
    intent.set_room_lengths(
        room_id="room-terminal",
        before_emitter_length_m=2.0,
    )

    assert intent.lengths_by_room_id["room-001"].before_emitter_length_m == 3.25
    assert intent.lengths_by_room_id["room-001"].after_emitter_length_m == 1.5
    assert intent.lengths_by_room_id["room-terminal"].after_emitter_length_m is None

    payload = intent.to_dict()
    assert list(payload["lengths_by_room_id"]) == [
        "room-001",
        "room-terminal",
    ]
    restored = room_paired_pipe_length_intent_from_dict_v1(payload)
    assert restored.to_dict() == payload

    restored.set_room_lengths(room_id="room-001")
    assert "room-001" not in restored.lengths_by_room_id
    assert restored.clear_room("room-terminal") is True
    assert restored.clear_room("room-terminal") is False

    _expect_value_error(
        lambda: intent.set_room_lengths(
            room_id="room-bad",
            before_emitter_length_m=-0.01,
        )
    )
    _expect_value_error(
        lambda: intent.set_room_lengths(
            room_id="room-bad",
            after_emitter_length_m=float("nan"),
        )
    )
    _expect_value_error(
        lambda: intent.set_room_lengths(
            room_id="",
            before_emitter_length_m=1.0,
        )
    )

    project = ProjectState(project_id="hs68b1", name="H-S68-B1")
    project.hydronic_room_paired_pipe_length_intent = intent
    project_payload = project.to_dict()
    persisted_payload = project_payload[
        "hydronic_room_paired_pipe_length_intent"
    ]
    assert persisted_payload == payload

    loaded = ProjectState.from_dict(project_payload)
    loaded_intent = loaded.hydronic_room_paired_pipe_length_intent
    assert loaded_intent is not None
    assert loaded_intent.to_dict() == payload

    legacy_payload = ProjectState(
        project_id="hs68b1-legacy",
        name="H-S68-B1 legacy",
    ).to_dict()
    legacy_payload.pop("hydronic_room_paired_pipe_length_intent", None)
    legacy_loaded = ProjectState.from_dict(legacy_payload)
    assert legacy_loaded.hydronic_room_paired_pipe_length_intent is None

    print(
        "OK — H-S68-B1 sparse room-centric paired-pipe lengths survive "
        "ProjectState round-trip; legacy projects remain unset and no "
        "hydraulic section, topology or heat-loss authority is invented."
    )


if __name__ == "__main__":
    main()
