# ======================================================================
# HVAC/dev/test_hydronic_20_room_route_pressure.py
# ======================================================================

from __future__ import annotations

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    build_route_pressure_accumulator_v1,
)


def main() -> None:
    project = build_hydronic_20_room_multileg_project_v1()

    projection = build_route_pressure_accumulator_v1(project)

    print("Routes:", len(projection.rows))

    for row in projection.rows:
        print(
            row.rank,
            row.route_id,
            row.route_label,
            "sections=",
            row.section_count,
            "route_dp=",
            row.route_pressure_drop_total_Pa,
            "complete=",
            row.complete,
            "controlling=",
            row.is_controlling_candidate,
            row.status,
        )


if __name__ == "__main__":
    main()