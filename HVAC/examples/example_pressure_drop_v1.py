"""
example_pressure_drop_v1.py
---------------------------

End-to-end:
Fabric → HydronicsPayloadV1 → Pipe sizing → Pressure drop (major+minor)
"""

from heatloss.factories.project_factory_v3 import (
    create_new_project,
    attach_space,
    attach_constructions,
    build_heatloss_if_ready,
)

from HVAC.geometry.opening_placement_v1 import OpeningPlacement
from HVAC.hydronics.hydronics_payload_v1 import build_from_fabric
from HVAC.hydronics.pipe_sizing_solver_v1 import (
    size_pipe_for_hydronics,
    describe_pipe_sizing,
)
from HVAC.hydronics.pressure_drop_solver_v1 import (
    solve_pressure_drop_v1,
    describe_pressure_drop,
)


def run():
    # ------------------------------------------------------------
    # 1) Build a simple one-room project (same pattern as before)
    # ------------------------------------------------------------
    project = create_new_project("Pressure Drop Test")

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
    # 2) Hydronics payload (fabric-driven)
    # ------------------------------------------------------------
    hydronics = build_from_fabric(
        project.heatloss_payload,
        design_delta_t_k=5.0,
    )

    # ------------------------------------------------------------
    # 3) Pipe sizing (velocity rule)
    # ------------------------------------------------------------
    sizing = size_pipe_for_hydronics(
        hydronics,
        max_velocity_m_s=0.8,
    )
    print(describe_pipe_sizing(sizing))

    # ------------------------------------------------------------
    # 4) Pressure drop (major + optional minors)
    # ------------------------------------------------------------
    # Example: 12 m of pipe, plus a couple of fittings.
    # (K values are illustrative; you can replace with your library later.)
    k_values = [
        0.9,   # 90° elbow (example)
        0.9,   # 90° elbow
        2.0,   # TRV / valve (example lumped K)
    ]

    dp = solve_pressure_drop_v1(
        hydronics,
        sizing,
        length_m=12.0,
        roughness_m=0.00015,               # steel-ish
        density_kg_m3=1000.0,
        kinematic_viscosity_m2_s=1.0e-6,
        k_values=k_values,                 # optional (can set None)
    )

    print()
    print(describe_pressure_drop(dp))


if __name__ == "__main__":
    run()
