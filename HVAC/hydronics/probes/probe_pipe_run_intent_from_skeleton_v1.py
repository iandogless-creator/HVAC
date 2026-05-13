# ======================================================================
# HVAC/hydronics/probes/probe_pipe_run_intent_from_skeleton_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.models.hydronic_skeleton_generator_v1 import (
    RoomLoadV1,
    generate_initial_hydronic_skeleton_v1,
)
from HVAC.hydronics.pipes.pipe_run_intent_builder_v1 import (
    build_pipe_run_intents_from_skeleton_v1,
)


def main() -> None:
    print()
    print("Hydronics H-N1 — pipe-run intent from skeleton probe")
    print()

    skeleton = generate_initial_hydronic_skeleton_v1(
        [
            RoomLoadV1(
                room_id="room-001",
                room_name="Kitchen",
                design_heat_loss_w=421.6,
            ),
            RoomLoadV1(
                room_id="room-002",
                room_name="Living Room",
                design_heat_loss_w=650.0,
            ),
        ]
    )

    pipe_runs = build_pipe_run_intents_from_skeleton_v1(skeleton)

    print(f"Terminals:     {len(skeleton.terminals)}")
    print(f"Supply legs:   {len(skeleton.supply_legs)}")
    print(f"Return legs:   {len(skeleton.return_legs)}")
    print(f"Pipe runs:     {len(pipe_runs)}")
    print()

    for pipe in pipe_runs:
        print(
            f"{pipe.pipe_run_id} | "
            f"{pipe.leg_id} | "
            f"{pipe.from_node_id} -> {pipe.to_node_id} | "
            f"{pipe.circuit_type} | "
            f"length={pipe.length_m}"
        )

    assert len(pipe_runs) == 4

    supply_count = sum(1 for pipe in pipe_runs if pipe.circuit_type == "supply")
    return_count = sum(1 for pipe in pipe_runs if pipe.circuit_type == "return")

    assert supply_count == 2
    assert return_count == 2

    print()
    print("OK — pipe-run intent from skeleton probe passed.")
    print()


if __name__ == "__main__":
    main()
