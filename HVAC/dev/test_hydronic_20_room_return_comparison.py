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

    # H-S51-D: this legacy fixture has no common-main / leg-entry lengths.
    # Treat the incomplete result as explicit evidence, never a silent pass.
    assert projection.rows
    assert all(
        row.missing_upstream_length_section_ids
        for row in projection.rows
    )
    assert all(row.direct_total_dp_Pa is None for row in projection.rows)
    assert all(
        row.reverse_return_total_dp_Pa is None
        for row in projection.rows
    )
    assert all(
        "upstream physical length missing" in row.status
        for row in projection.rows
    )

    print("H-S19-A Circuit return path comparison")
    print(f"Status: {projection.status}")
    print(f"Rows: {len(projection.rows)}")
    print()

    for row in projection.rows:
        flow = ",".join(row.flow_section_ids) if row.flow_section_ids else "-"
        direct = (
            ",".join(row.direct_return_section_ids)
            if row.direct_return_section_ids
            else "-"
        )
        reverse = (
            ",".join(row.reverse_return_section_ids)
            if row.reverse_return_section_ids
            else "-"
        )

        print(
            f"{row.route_id} "
            f"{row.route_label} "
            f"room={row.room_id} "
            f"emitter={row.emitter_id or '-'} "
            f"flow={flow} "
            f"direct={direct} "
            f"reverse={reverse} "
            f"rr_code={row.rr_suitability_code} "
            f"rr_status={row.rr_suitability_status} "
            f"direct_total={row.direct_total_dp_Pa} "
            f"reverse_total={row.reverse_return_total_dp_Pa} "
            f"direct_rank={row.direct_rank or '-'} "
            f"rr_rank={row.reverse_return_rank or '-'} "
            f"direct_ctrl={row.controlling_direct} "
            f"rr_ctrl={row.controlling_reverse_return} "
            f"{row.status}"
        )


if __name__ == "__main__":
    main()