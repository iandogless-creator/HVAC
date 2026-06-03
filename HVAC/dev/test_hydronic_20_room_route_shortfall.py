# HVAC/dev/test_hydronic_20_room_route_shortfall.py
#
# H-S18 proof:
# Route Δp shortfall to controlling route candidate.

from __future__ import annotations

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)

from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    build_route_pressure_accumulator_v1,
)

from HVAC.hydronics.proportioning.route_proportioning_shortfall_preview_v1 import (
    build_route_proportioning_shortfall_preview_v1,
)


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}"


def main() -> None:
    project_state = build_hydronic_20_room_multileg_project_v1()

    route_pressure_projection = build_route_pressure_accumulator_v1(
        project_state
    )

    preview = build_route_proportioning_shortfall_preview_v1(
        route_pressure_projection
    )

    print("H-S18 Route shortfall preview")
    print(f"Status: {preview.status}")
    print(f"Controlling route: {preview.controlling_route_key}")
    print(f"Controlling Δp: {_fmt(preview.controlling_dp_Pa)} Pa")
    print(f"Routes: {len(preview.rows)}")
    print()

    for row in preview.rows:
        print(
            f"{row.rank} "
            f"{row.route_key} "
            f"{row.route_label} "
            f"route_dp={_fmt(row.route_dp_Pa)} Pa "
            f"controlling_dp={_fmt(row.controlling_dp_Pa)} Pa "
            f"shortfall={_fmt(row.shortfall_dp_Pa)} Pa "
            f"complete={row.complete} "
            f"controlling={row.controlling} "
            f"{row.status}"
        )


if __name__ == "__main__":
    main()