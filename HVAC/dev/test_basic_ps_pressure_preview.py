# ======================================================================
# HVAC/dev/test_basic_ps_pressure_preview.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    BasicPSPipeSizingResultV1,
)
from HVAC.hydronics.sizing.basic_ps_pressure_preview_v1 import (
    build_basic_ps_pressure_preview_v1,
)


def _result(
    *,
    section_id: str,
    order: int,
    from_label: str,
    to_room_label: str,
    pressure_gradient_Pa_per_m: float,
    is_index_room: bool = False,
    is_terminal: bool = False,
) -> BasicPSPipeSizingResultV1:
    return BasicPSPipeSizingResultV1(
        section_id=section_id,
        order=order,
        from_label=from_label,
        to_room_label=to_room_label,
        carried_heat_W=1000.0,
        carried_flow_kg_s=0.012,
        pipe_size_label="15 mm",
        internal_diameter_m=0.0136,
        velocity_m_s=0.15,
        reynolds_number=2000.0,
        friction_factor=0.03,
        pressure_gradient_Pa_per_m=pressure_gradient_Pa_per_m,
        is_index_room=is_index_room,
        is_terminal=is_terminal,
        status="First-pass Haaland estimate",
    )


def main() -> None:
    results = [
        _result(
            section_id="section-001",
            order=1,
            from_label="Common main / leg entry",
            to_room_label="Hall",
            pressure_gradient_Pa_per_m=50.0,
        ),
        _result(
            section_id="section-002",
            order=2,
            from_label="Hall",
            to_room_label="Kitchen",
            pressure_gradient_Pa_per_m=40.0,
        ),
        _result(
            section_id="section-003",
            order=3,
            from_label="Kitchen",
            to_room_label="Lounge",
            pressure_gradient_Pa_per_m=30.0,
            is_index_room=True,
            is_terminal=True,
        ),
    ]

    print()
    print("==============================")
    print("Basic PS Pressure Preview Test")
    print("==============================")
    print()

    incomplete = build_basic_ps_pressure_preview_v1(results)

    print("--- INCOMPLETE LENGTHS ---")
    print(f"status: {incomplete.status}")
    print(f"total_pressure_drop_Pa: {incomplete.total_pressure_drop_Pa}")

    for row in incomplete.rows:
        print(
            f"{row.order:>2} | "
            f"{row.from_label} -> {row.to_room_label} | "
            f"Δp/m={row.pressure_gradient_Pa_per_m:.1f} | "
            f"L={row.section_length_m} | "
            f"dp={row.section_pressure_drop_Pa} | "
            f"status={row.status}"
        )

    assert incomplete.total_pressure_drop_Pa is None
    assert all(row.section_pressure_drop_Pa is None for row in incomplete.rows)

    print()

    complete = build_basic_ps_pressure_preview_v1(
        results,
        section_lengths_m={
            "section-001": 10.0,
            "section-002": 8.0,
            "section-003": 6.0,
        },
    )

    print("--- COMPLETE LENGTHS ---")
    print(f"status: {complete.status}")
    print(f"total_pressure_drop_Pa: {complete.total_pressure_drop_Pa:.1f}")

    for row in complete.rows:
        print(
            f"{row.order:>2} | "
            f"{row.from_label} -> {row.to_room_label} | "
            f"Δp/m={row.pressure_gradient_Pa_per_m:.1f} | "
            f"L={row.section_length_m:.1f} m | "
            f"dp={row.section_pressure_drop_Pa:.1f} Pa | "
            f"index={row.is_index_room} | "
            f"terminal={row.is_terminal} | "
            f"status={row.status}"
        )

    expected_total = (50.0 * 10.0) + (40.0 * 8.0) + (30.0 * 6.0)

    assert complete.total_pressure_drop_Pa == expected_total
    assert complete.rows[-1].is_index_room is True
    assert complete.rows[-1].is_terminal is True

    print()
    print("PASS")


if __name__ == "__main__":
    main()