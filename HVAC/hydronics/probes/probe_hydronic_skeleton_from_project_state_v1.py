# ======================================================================
# HVAC/hydronics/probes/probe_hydronic_skeleton_from_project_state_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.dev.bootstrap_project_state import make_dev_bootstrap_project_state
from HVAC.heatloss.controller_v4_orchestrator import HeatLossControllerV4
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.builders.hydronic_skeleton_from_project_state_v1 import (
    build_hydronic_skeleton_from_project_state_v1,
    extract_room_loads_from_project_state_v1,
)


def main() -> None:
    print()
    print("Hydronics H-M2 — ProjectState skeleton builder probe")
    print()

    project = make_dev_bootstrap_project_state()

    controller = HeatLossControllerV4(project_state=project)
    controller.run(internal_design_temp_C=21.0)

    emitter_id = "emitter-test-room-001-001"

    project.emitters[emitter_id] = EmitterV1(
        emitter_id=emitter_id,
        room_id="room-001",
        name="Test radiator",
        emitter_type="radiator",
        design_output_W=500.0,
        flow_temp_C=70.0,
        return_temp_C=50.0,
        room_temp_C=21.0,
        notes="H-M2 ProjectState skeleton builder probe",
    )

    room_loads = extract_room_loads_from_project_state_v1(project)
    skeleton = build_hydronic_skeleton_from_project_state_v1(project)

    print(f"Heat-loss valid: {project.heatloss_valid}")
    print(f"Room loads:      {len(room_loads)}")
    print(f"Emitters:        {len(skeleton.emitters)}")
    print(f"Terminals:       {len(skeleton.terminals)}")
    print(f"Supply legs:     {len(skeleton.supply_legs)}")
    print(f"Return legs:     {len(skeleton.return_legs)}")
    print()

    for load in room_loads:
        print(
            f"{load.room_id} | "
            f"{load.room_name} | "
            f"{load.design_heat_loss_w:.1f} W"
        )

    print()

    for emitter in skeleton.emitters.values():
        print(
            f"{emitter.emitter_id} | "
            f"{emitter.room_id} | "
            f"{emitter.emitter_type} | "
            f"{emitter.design_output_W} W"
        )

    assert project.heatloss_valid is True
    assert len(room_loads) == 1
    assert len(skeleton.terminals) == 1
    assert len(skeleton.supply_legs) == 1
    assert len(skeleton.return_legs) == 1
    assert len(skeleton.emitters) == 1

    load = room_loads[0]
    assert load.room_id == "room-001"
    assert round(load.design_heat_loss_w, 3) == round(211.968, 3)

    print()
    print("OK — ProjectState hydronic skeleton builder passed.")
    print()


if __name__ == "__main__":
    main()
