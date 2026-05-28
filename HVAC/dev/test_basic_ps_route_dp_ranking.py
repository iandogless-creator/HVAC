# ======================================================================
# HVAC/dev/test_basic_ps_route_dp_ranking.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.sizing.basic_ps_pressure_preview_v1 import (
    BasicPSPressurePreviewProjectionV1,
    BasicPSPressurePreviewRowV1,
)
from HVAC.hydronics.sizing.basic_ps_route_dp_ranking_v1 import (
    BasicPSRoutePressureCandidateV1,
    build_basic_ps_route_dp_ranking_v1,
)


def _complete_preview(*, total_dp: float, length: float) -> BasicPSPressurePreviewProjectionV1:
    return BasicPSPressurePreviewProjectionV1(
        rows=(
            BasicPSPressurePreviewRowV1(
                section_id="section-001",
                order=1,
                from_label="Common main / leg entry",
                to_room_label="Terminal",
                pressure_gradient_Pa_per_m=total_dp / length,
                section_length_m=length,
                section_pressure_drop_Pa=total_dp,
                is_index_room=True,
                is_terminal=True,
                status="Preview only",
            ),
        ),
        total_pressure_drop_Pa=total_dp,
        status="Preview only",
    )


def _incomplete_preview() -> BasicPSPressurePreviewProjectionV1:
    return BasicPSPressurePreviewProjectionV1(
        rows=(
            BasicPSPressurePreviewRowV1(
                section_id="section-001",
                order=1,
                from_label="Common main / leg entry",
                to_room_label="Terminal",
                pressure_gradient_Pa_per_m=50.0,
                section_length_m=None,
                section_pressure_drop_Pa=None,
                is_index_room=True,
                is_terminal=True,
                status="Length not set",
            ),
        ),
        total_pressure_drop_Pa=None,
        status="Preview incomplete — section length missing",
    )


def main() -> None:
    candidates = [
        BasicPSRoutePressureCandidateV1(
            route_id="route-low",
            route_label="Low Δp route",
            leg_id="leg-001",
            subleg_id="subleg-low",
            pressure_preview=_complete_preview(total_dp=700.0, length=14.0),
        ),
        BasicPSRoutePressureCandidateV1(
            route_id="route-high",
            route_label="High Δp route",
            leg_id="leg-002",
            subleg_id="subleg-high",
            pressure_preview=_complete_preview(total_dp=1200.0, length=20.0),
        ),
        BasicPSRoutePressureCandidateV1(
            route_id="route-incomplete",
            route_label="Incomplete route",
            leg_id="leg-003",
            subleg_id="subleg-incomplete",
            pressure_preview=_incomplete_preview(),
        ),
    ]

    projection = build_basic_ps_route_dp_ranking_v1(candidates)

    print()
    print("==============================")
    print("Basic PS Route Δp Ranking Test")
    print("==============================")
    print()
    print(f"status: {projection.status}")
    print(f"controlling_route_id: {projection.controlling_route_id}")
    print()

    for row in projection.rows:
        total_dp = (
            "—"
            if row.total_pressure_drop_Pa is None
            else f"{row.total_pressure_drop_Pa:.1f} Pa"
        )
        total_length = (
            "—"
            if row.total_length_m is None
            else f"{row.total_length_m:.1f} m"
        )

        print(
            f"rank={row.rank} | "
            f"{row.route_id} | "
            f"{row.route_label} | "
            f"L={total_length} | "
            f"Δp={total_dp} | "
            f"controlling={row.is_controlling_index} | "
            f"complete={row.is_complete} | "
            f"status={row.status}"
        )

    assert projection.controlling_route_id == "route-high"

    assert projection.rows[0].route_id == "route-high"
    assert projection.rows[0].rank == 1
    assert projection.rows[0].is_controlling_index is True

    assert projection.rows[1].route_id == "route-low"
    assert projection.rows[1].rank == 2
    assert projection.rows[1].is_controlling_index is False

    assert projection.rows[2].route_id == "route-incomplete"
    assert projection.rows[2].rank is None
    assert projection.rows[2].is_complete is False

    print()
    print("PASS")


if __name__ == "__main__":
    main()