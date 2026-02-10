"""
example_pump_selection_v1.py
----------------------------

End-to-end:
Fabric → HydronicsPayloadV1 → Pipe sizing → Pressure drop → Pump selection
"""

from heatloss.factories.project_factory_v3 import (
    create_new_project,
    attach_space,
    attach_constructions,
    build_heatloss_if_ready,
)

from HVAC.geometry.opening_placement_v1 import OpeningPlacement

from HVAC.hydronics.hydronics_payload_v1 import build_from_fabric
from HVAC.hydronics.pipe_sizing_solver_v1 import size_pipe_for_hydronics, describe_pipe_sizing
from HVAC.hydronics.pressure_drop_solver_v1 import solve_pressure_drop_v1, describe_pressure_drop
from HVAC.hydronics.pump_selection_v1 import select_pump_v1, describe_pump_selection


def run():
    # ------------------------------------------------------------
    # 1) Fabric (same pattern as your prior examples)
    # ------------------------------------------------------------
    project = create_new_project("Pump Selection Test")

    attach_space(
        project,
        footprint=[
            (0.0, 0.0),
            (5.0, 0.0),
            (5.0, 4.0),
            (0.0, 4.0),
        ],
        height_m=2.4,
        orientation_deg=135.0,
    )

    project.space.openings.append(
        OpeningPlacement(
            edge_index=2,
            offset_m=1.0,
            width_m=1.5,
            opening_type="window",
        )
    )

    attach_constructions(
        project,
        wall_uvalues_by_facade={
            "N": 0.30, "NE": 0.30, "E": 0.30, "SE": 0.30,
            "S": 0.30, "SW": 0.30, "W": 0.30, "NW": 0.30,
        },
        opening_uvalues_by_type={
            "window": 1.4,
            "door": 1.8,
        },
    )

    build_heatloss_if_ready(project)

    # ------------------------------------------------------------
    # 2) Hydronics demand
    # ------------------------------------------------------------
    hydronics = build_from_fabric(project.heatloss_payload, design_delta_t_k=20.0)

    # ------------------------------------------------------------
    # 3) Pipe sizing
    # ------------------------------------------------------------
    sizing = size_pipe_for_hydronics(hydronics, max_velocity_m_s=0.8)
    print(describe_pipe_sizing(sizing))

    # ------------------------------------------------------------
    # 4) Pressure drop (major + optional minor)
    # ------------------------------------------------------------
    dp = solve_pressure_drop_v1(
        hydronics,
        sizing,
        length_m=12.0,
        roughness_m=0.00015,
        density_kg_m3=1000.0,
        kinematic_viscosity_m2_s=1.0e-6,
        k_values=[0.9, 0.9, 2.0],  # optional; set None for majors only
    )

    print()
    print(describe_pressure_drop(dp))

    # ------------------------------------------------------------
    # 5) Pump selection (duty point)
    # ------------------------------------------------------------
    sel = select_pump_v1(
        hydronics,
        dp,
        allow_variable_speed=True,
        min_head_margin_m=0.0,
    )

    print()
    print(describe_pump_selection(sel))


if __name__ == "__main__":
    run()
