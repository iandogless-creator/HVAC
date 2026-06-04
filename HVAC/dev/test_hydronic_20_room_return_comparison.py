# HVAC/dev/test_hydronic_20_room_return_comparison.py
#
# H-S19-A proof:
# Direct return vs reverse return comparison shell.

from __future__ import annotations

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)

from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    build_circuit_return_path_comparison_v1,
)


def main() -> None:
    project_state = build_hydronic_20_room_multileg_project_v1()

    projection = build_circuit_return_path_comparison_v1(project_state)

    print("H-S19-A Circuit return path comparison")
    print(f"Status: {projection.status}")
    print(f"Rows: {len(projection.rows)}")
    print()

    for row in projection.rows:
        print(
            f"{row.route_id} "
            f"{row.route_label} "
            f"room={row.room_id} "
            f"emitter={row.emitter_id or '-'} "
            f"direct_total={row.direct_total_dp_Pa} "
            f"reverse_total={row.reverse_return_total_dp_Pa} "
            f"{row.status}"
        )


if __name__ == "__main__":
    main()