"""
example_pipe_sizing_v1.py
-------------------------

Hydronics v1 — pipe sizing engine proof.

No project
No geometry
No heat-loss
Pure hydronics physics.
"""

from HVAC_legacy.hydronics.pipe_sizing_solver_v1 import (
    size_pipe_for_flow_lps,
    describe_pipe_sizing,
)


def run():
    # Example design flow (litres per second)
    flow_lps = 0.20

    result = size_pipe_for_flow_lps(
        flow_lps=flow_lps,
        max_velocity_m_s=0.8,
    )

    print(describe_pipe_sizing(result))


if __name__ == "__main__":
    run()
