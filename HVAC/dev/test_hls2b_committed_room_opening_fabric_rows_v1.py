from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.heatloss.dto.fabric_surface_row_v1 import FabricSurfaceRowV1
from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1
from HVAC.heatloss.fabric.room_fabric_rows_with_openings_v1 import (
    build_room_fabric_rows_with_openings_v1,
)


def _row(surface_id: str, element: str, area: float, u: float) -> FabricSurfaceRowV1:
    segment = None
    if element == "external_wall":
        segment = SimpleNamespace(
            boundary_kind="EXTERNAL",
            geometry_ref="wall",
        )
    return FabricSurfaceRowV1(
        surface_id=surface_id,
        room_id="ROOM-1",
        element=element,
        area_m2=area,
        u_value_W_m2K=u,
        delta_t_K=24.0,
        qf_W=area * u * 24.0,
        construction_id="WALL" if element == "external_wall" else "FLOOR",
        _segment=segment,
    )


def main() -> None:
    base_rows = [
        _row("wall-a", "external_wall", 10.0, 0.20),
        _row("wall-b", "external_wall", 20.0, 0.30),
        _row("floor", "floor", 12.0, 0.18),
    ]
    schedule = SimpleNamespace(
        openings=[
            SimpleNamespace(
                opening_type="WINDOW",
                profile_id="SMALL_WINDOW",
                width_m=1.0,
                height_m=1.0,
                quantity=2,
                construction_id="WINDOW-A",
            ),
            SimpleNamespace(
                opening_type="WINDOW",
                profile_id="LARGE_WINDOW",
                width_m=0.5,
                height_m=1.0,
                quantity=2,
                construction_id="WINDOW-A",
            ),
            SimpleNamespace(
                opening_type="DOOR",
                profile_id="EXTERNAL_DOOR",
                width_m=1.0,
                height_m=2.0,
                quantity=1,
                construction_id="DOOR-A",
            ),
            SimpleNamespace(
                opening_type="DOOR",
                profile_id="INTERNAL_DOOR",
                width_m=0.8,
                height_m=2.0,
                quantity=1,
                construction_id="DOOR-A",
            ),
        ]
    )
    project = SimpleNamespace(
        room_opening_schedules={"ROOM-1": schedule},
        constructions={
            "WINDOW-A": SimpleNamespace(
                name="Window A", u_value_W_m2K=1.40
            ),
            "DOOR-A": SimpleNamespace(
                name="Door A", u_value_W_m2K=1.60
            ),
        },
    )
    room = SimpleNamespace(room_id="ROOM-1")

    original = FabricFromSegmentsV1.build_rows_for_room
    FabricFromSegmentsV1.build_rows_for_room = staticmethod(
        lambda _project, _room: list(base_rows)
    )
    try:
        rows = build_room_fabric_rows_with_openings_v1(project, room)
    finally:
        FabricFromSegmentsV1.build_rows_for_room = staticmethod(original)

    wall_rows = [row for row in rows if row.element == "external_wall"]
    opening_rows = [
        row for row in rows if row.element in {"window", "external_door"}
    ]
    assert len(wall_rows) == 2
    assert abs(sum(row.area_m2 for row in wall_rows) - 25.0) < 1.0e-12
    assert abs(wall_rows[0].area_m2 - (10.0 * 25.0 / 30.0)) < 1.0e-12
    assert len(opening_rows) == 2
    assert [row.element for row in opening_rows] == ["window", "external_door"]
    assert [row.area_m2 for row in opening_rows] == [3.0, 2.0]
    assert abs(
        sum(row.area_m2 for row in wall_rows)
        + sum(row.area_m2 for row in opening_rows)
        - 30.0
    ) < 1.0e-12
    assert all(row.qf_W is not None for row in rows)

    root = Path(__file__).resolve().parents[2]
    snapshot_source = (
        root / "HVAC/heatloss/resolution/effective_snapshot_builder.py"
    ).read_text(encoding="utf-8")
    adapter_source = (
        root / "HVAC/gui_v3/adapters/heat_loss_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert "build_room_fabric_rows_with_openings_v1(project, room)" in snapshot_source
    assert "build_room_fabric_rows_with_openings_v1(ps, room)" in adapter_source

    print(
        "OK — HL-S2B net external-wall and grouped room-opening rows share "
        "one committed fabric source."
    )


if __name__ == "__main__":
    main()
