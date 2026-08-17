from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.core.opening_schedule_v1 import (
    OpeningScheduleItemV1,
    RoomOpeningScheduleV1,
)
from HVAC.core.room_state import RoomStateV1
from HVAC.project.project_state import ProjectState
from HVAC.project_v3.persistence.checksum import compute_checksum
from HVAC.project_v3.persistence.loader import load
from HVAC.project_v3.persistence.saver import save


def _opening(
    opening_type: str,
    profile_id: str,
    profile_name: str,
    width_m: float,
    height_m: float,
    quantity: int,
    construction_id: str,
) -> OpeningScheduleItemV1:
    return OpeningScheduleItemV1(
        opening_type=opening_type,
        profile_id=profile_id,
        profile_name=profile_name,
        width_m=width_m,
        height_m=height_m,
        quantity=quantity,
        construction_id=construction_id,
    )


def main() -> None:
    project = ProjectState(project_id="hls2c2", name="Opening persistence")
    project.rooms["room-a"] = RoomStateV1(room_id="room-a", name="Kitchen")
    project.rooms["room-b"] = RoomStateV1(room_id="room-b", name="Hall")
    project.room_opening_schedules = {
        "room-a": RoomOpeningScheduleV1(
            room_id="room-a",
            openings=[
                _opening(
                    "WINDOW",
                    "STANDARD_WINDOW",
                    "Standard Window",
                    1.2,
                    1.2,
                    2,
                    "USR-DECLARED-WINDOW-W1-A1",
                ),
                _opening(
                    "DOOR",
                    "EXTERNAL_DOOR",
                    "External Door",
                    0.9,
                    2.1,
                    1,
                    "USR-DECLARED-DOOR-D1-B2",
                ),
                _opening(
                    "DOOR",
                    "INTERNAL_DOOR",
                    "Internal Door",
                    0.8,
                    2.0,
                    1,
                    "USR-DECLARED-DOOR-D2-C3",
                ),
            ],
        ),
        "room-b": RoomOpeningScheduleV1(room_id="room-b"),
    }

    with TemporaryDirectory(prefix="hls2c2-") as temporary_directory:
        root = Path(temporary_directory)
        current_dir = root / "current"
        legacy_dir = root / "legacy"

        save(project, current_dir)
        restored = load(current_dir)

        assert set(restored.room_opening_schedules) == {"room-a", "room-b"}
        restored_a = restored.room_opening_schedules["room-a"]
        restored_b = restored.room_opening_schedules["room-b"]
        assert isinstance(restored_a, RoomOpeningScheduleV1)
        assert restored_a.room_id == "room-a"
        assert restored_b.room_id == "room-b"
        assert restored_b.openings == []
        assert len(restored_a.openings) == 3
        assert all(
            isinstance(item, OpeningScheduleItemV1)
            for item in restored_a.openings
        )

        window, external_door, internal_door = restored_a.openings
        assert window.opening_type == "WINDOW"
        assert window.profile_id == "STANDARD_WINDOW"
        assert window.profile_name == "Standard Window"
        assert window.width_m == 1.2
        assert window.height_m == 1.2
        assert window.quantity == 2
        assert window.construction_id == "USR-DECLARED-WINDOW-W1-A1"
        assert external_door.opening_type == "DOOR"
        assert external_door.profile_id == "EXTERNAL_DOOR"
        assert external_door.construction_id == "USR-DECLARED-DOOR-D1-B2"
        assert internal_door.profile_id == "INTERNAL_DOOR"
        assert internal_door.construction_id == "USR-DECLARED-DOOR-D2-C3"
        assert abs(restored_a.total_opening_area_m2 - 6.37) < 1.0e-12

        wrapper = json.loads(
            (current_dir / "project.json").read_text(encoding="utf-8")
        )
        assert wrapper["schema_version"] == 4
        payload = wrapper["payload"]
        assert payload["schema_version"] == 4
        assert payload["openings"] == {}
        saved_schedules = payload["room_opening_schedules"]
        assert set(saved_schedules) == {"room-a", "room-b"}
        assert saved_schedules["room-a"]["room_id"] == "room-a"
        for item_payload in saved_schedules["room-a"]["openings"]:
            assert "u_value_W_m2K" not in item_payload
            assert "surface_id" not in item_payload

        mismatched = project.room_opening_schedules["room-a"].to_dict()
        mismatched["room_id"] = "room-other"
        try:
            RoomOpeningScheduleV1.from_dict(
                mismatched,
                expected_room_id="room-a",
            )
        except ValueError as exc:
            assert "identity mismatch" in str(exc)
        else:
            raise AssertionError("Expected room-opening schedule identity mismatch")

        legacy_payload = project.to_dict()
        legacy_payload.pop("room_opening_schedules")
        legacy_wrapper = {
            "schema_version": 4,
            "checksum": compute_checksum(legacy_payload),
            "payload": legacy_payload,
        }
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "project.json").write_text(
            json.dumps(legacy_wrapper, indent=4, sort_keys=True),
            encoding="utf-8",
        )
        legacy = load(legacy_dir)
        assert legacy.room_opening_schedules == {}

    print(
        "OK — HL-S2C2 room-level opening schedules survive checksummed "
        "project save/load with stable room and construction identity; "
        "legacy projects load empty, with no wall placement or stored U-values."
    )


if __name__ == "__main__":
    main()
