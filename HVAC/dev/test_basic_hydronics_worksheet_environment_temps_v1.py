# ======================================================================
# HVAC/dev/test_basic_hydronics_worksheet_environment_temps_v1.py
# H-S22-A — Worksheet uses Environment hydronic flow/return basis
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.worksheets.basic_hydronics_worksheet_v1 import (
    build_basic_hydronics_worksheet_v1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    project = ProjectState(
        project_id="dev-worksheet-environment-temps",
        name="DEV Worksheet Environment Temps",
    )

    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
        design_flow_temp_c=75.0,
        design_return_temp_c=65.0,
    )

    project.rooms["room-001"] = RoomStateV1(
        room_id="room-001",
        name="Kitchen",
        room_ref="R1",
    )

    # Hydronics consumes committed heat-loss demand; it does not calculate it.
    project.heatloss_results = {
        "fabric": {},
        "ventilation": {},
        "room_totals": {
            "room-001": {
                "q_fabric_W": 700.0,
                "q_ventilation_W": 300.0,
                "q_total_W": 1000.0,
            },
        },
    }
    project.mark_heatloss_valid()

    # Legacy emitter temps deliberately differ: Environment must win.
    project.emitters["emitter-001"] = EmitterV1(
        emitter_id="emitter-001",
        room_id="room-001",
        name="Radiator — R1 Kitchen",
        emitter_type="radiator",
        design_output_W=1200.0,
        flow_temp_C=70.0,
        return_temp_C=50.0,
    )

    worksheet = build_basic_hydronics_worksheet_v1(project)

    assert len(worksheet.rows) == 1

    row = worksheet.rows[0]

    expected_delta_t_K = 10.0
    expected_flow_kg_s = 1000.0 / (4180.0 * expected_delta_t_K)

    print("\n======================================")
    print("Basic Hydronics Worksheet Environment Temps")
    print("======================================")
    print(f"heat_load_W = {row.heat_load_W}")
    print(f"flow_temp_C = {row.flow_temp_C}")
    print(f"return_temp_C = {row.return_temp_C}")
    print(f"water_delta_t_K = {row.water_delta_t_K}")
    print(f"mass_flow_kg_s = {row.mass_flow_kg_s:.6f}")
    print(f"expected_flow_kg_s = {expected_flow_kg_s:.6f}")

    assert row.heat_load_W == 1000.0
    assert row.flow_temp_C == 75.0
    assert row.return_temp_C == 65.0
    assert row.water_delta_t_K == expected_delta_t_K
    assert abs(row.mass_flow_kg_s - expected_flow_kg_s) < 1e-12

    print("\nOK — worksheet uses Environment hydronic temperatures.")


if __name__ == "__main__":
    main()
