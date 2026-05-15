# ======================================================================
# HVAC/dev/probe_room_identity_roundtrip_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.core.room_state import RoomStateV1
from HVAC.core.room_geometry import RoomGeometryV1


def main() -> None:
    print()
    print("S-A — room identity round-trip probe")
    print()

    room = RoomStateV1(
        room_id="room-001",
        name="Airing Cupboard",
        room_ref="R1",
        storey_index=1,
        storey_label="First Floor",
        geometry=RoomGeometryV1(
            length_m=1.2,
            width_m=0.8,
            height_m=2.4,
        ),
        internal_temp_override_C=21.0,
        ach_override=0.5,
    )

    data = room.to_dict()
    restored = RoomStateV1.from_dict("room-001", data)

    print(f"Room ID:       {restored.room_id}")
    print(f"Room ref:      {restored.room_ref}")
    print(f"Name:          {restored.name}")
    print(f"Storey label:  {restored.storey_label}")
    print(f"Storey index:  {restored.storey_index}")
    print(f"Length:        {restored.geometry.length_m} m")
    print(f"Width:         {restored.geometry.width_m} m")
    print(f"Height:        {restored.geometry.height_m} m")

    assert restored.room_id == "room-001"
    assert restored.room_ref == "R1"
    assert restored.name == "Airing Cupboard"
    assert restored.storey_label == "First Floor"
    assert restored.storey_index == 1
    assert restored.geometry.length_m == 1.2
    assert restored.geometry.width_m == 0.8
    assert restored.geometry.height_m == 2.4

    # Old project compatibility: room_ref absent.
    old_data = {
        "name": "Kitchen",
        "storey_index": 0,
        "storey_label": "Ground Floor",
        "geometry": {
            "length_m": 4.0,
            "width_m": 3.0,
            "height_m": 2.4,
        },
    }

    old_restored = RoomStateV1.from_dict("room-002", old_data)

    assert old_restored.room_ref == ""
    assert old_restored.name == "Kitchen"
    assert old_restored.storey_index == 0
    assert old_restored.storey_label == "Ground Floor"

    print()
    print("OK — room identity round-trip passed.")
    print()


if __name__ == "__main__":
    main()