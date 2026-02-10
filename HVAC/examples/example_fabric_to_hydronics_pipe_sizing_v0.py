"""
example_fabric_to_hydronics_pipe_sizing_v0.py
-------------------------

End-to-end test:
• Fabric → Hydronics → Pipe sizing
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


def run():
    # ------------------------------------------------------------
    # Project + fabric (same as before)
    # ------------------------------------------------------------
    project = create_new_project("Pipe Sizing Test")

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
    # Hydronics payload
    # ------------------------------------------------------------
    hydronics = build_from_fabric(
        project.heatloss_payload,
        design_delta_t_k=20.0,
    )

    # ------------------------------------------------------------
    # Pipe sizing
    # ------------------------------------------------------------
    result = size_pipe_for_hydronics(
        hydronics,
        max_velocity_m_s=0.8,
    )

    print(describe_pipe_sizing(result))


if __name__ == "__main__":
    run()
