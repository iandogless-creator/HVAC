from __future__ import annotations

from types import SimpleNamespace

from HVAC.core.opening_schedule_v1 import (
    OpeningScheduleItemV1,
    RoomOpeningScheduleV1,
)
from HVAC.heatloss.fabric.room_opening_schedule_thermal_projection_v1 import (
    resolve_room_opening_schedule_thermal_projection_v1,
)


def _opening(
    opening_type: str,
    profile_id: str,
    width_m: float,
    height_m: float,
    quantity: int,
    construction_id: str,
) -> OpeningScheduleItemV1:
    return OpeningScheduleItemV1(
        opening_type=opening_type,
        profile_id=profile_id,
        profile_name=profile_id.replace("_", " ").title(),
        width_m=width_m,
        height_m=height_m,
        quantity=quantity,
        construction_id=construction_id,
    )


def main() -> None:
    schedule = RoomOpeningScheduleV1(
        room_id="room-001",
        openings=[
            _opening("WINDOW", "STANDARD_WINDOW", 1.2, 1.2, 2, "w-a"),
            _opening("WINDOW", "SMALL_WINDOW", 0.6, 0.9, 1, "w-a"),
            _opening("WINDOW", "LARGE_WINDOW", 1.8, 1.2, 1, "w-b"),
            _opening("DOOR", "EXTERNAL_DOOR", 0.9, 2.1, 1, "d-a"),
            _opening("DOOR", "INTERNAL_DOOR", 0.9, 2.1, 1, "d-i"),
        ],
    )
    constructions = {
        "w-a": SimpleNamespace(name="Window A", u_value_W_m2K=1.4),
        "w-b": SimpleNamespace(name="Window B", u_value_W_m2K=1.1),
        "d-a": SimpleNamespace(name="Front Door", u_value_W_m2K=1.3),
        "d-i": SimpleNamespace(name="Internal Door", u_value_W_m2K=2.0),
    }

    result = resolve_room_opening_schedule_thermal_projection_v1(
        schedule=schedule,
        constructions=constructions,
        gross_external_wall_area_m2=20.0,
    )
    assert result.ready, result.blockers
    assert len(result.rows) == 3
    assert [row.opening_type for row in result.rows] == [
        "WINDOW", "WINDOW", "DOOR"
    ]
    rows = {(row.opening_type, row.construction_id): row for row in result.rows}
    assert abs(rows[("WINDOW", "w-a")].area_m2 - 3.42) < 1.0e-12
    assert abs(rows[("WINDOW", "w-b")].area_m2 - 2.16) < 1.0e-12
    assert abs(rows[("DOOR", "d-a")].area_m2 - 1.89) < 1.0e-12
    assert abs(result.external_opening_area_m2 - 7.47) < 1.0e-12
    assert abs(result.net_external_wall_area_m2 - 12.53) < 1.0e-12
    assert abs(result.excluded_internal_opening_area_m2 - 1.89) < 1.0e-12

    empty = resolve_room_opening_schedule_thermal_projection_v1(
        schedule=None,
        constructions=constructions,
        gross_external_wall_area_m2=20.0,
    )
    assert empty.ready and not empty.rows
    assert empty.net_external_wall_area_m2 == 20.0

    unavailable = resolve_room_opening_schedule_thermal_projection_v1(
        schedule=RoomOpeningScheduleV1(
            room_id="room-001",
            openings=[
                _opening("WINDOW", "SMALL_WINDOW", 0.6, 0.9, 1, "missing")
            ],
        ),
        constructions=constructions,
        gross_external_wall_area_m2=20.0,
    )
    assert not unavailable.ready
    assert "unavailable" in unavailable.blockers[0]

    excessive = resolve_room_opening_schedule_thermal_projection_v1(
        schedule=RoomOpeningScheduleV1(
            room_id="room-001",
            openings=[
                _opening("WINDOW", "LARGE_WINDOW", 10.0, 3.0, 1, "w-a")
            ],
        ),
        constructions=constructions,
        gross_external_wall_area_m2=20.0,
    )
    assert not excessive.ready
    assert excessive.net_external_wall_area_m2 == 0.0

    print(
        "OK — HL-S2A room-level external openings group by type and "
        "construction, resolve U-values and produce net wall area."
    )


if __name__ == "__main__":
    main()
