# ======================================================================
# HVAC/dev/test_hs22b_environment_flow_basis_v1.py
# H-S22-B — Pipe / branch summaries use Environment hydronic ΔT basis
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.pipes.pipe_authority_summary_v1 import (
    _room_emitter_mass_flow_kg_s,
    _sum_emitter_mass_flow_kg_s,
)
from HVAC.hydronics.proportioning.branch_proportioning_summary_v1 import (
    build_branch_proportioning_summary_v1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    project = ProjectState(
        project_id="dev-hs22b-environment-flow-basis",
        name="DEV H-S22-B Environment Flow Basis",
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

    project.rooms["room-002"] = RoomStateV1(
        room_id="room-002",
        name="Bedroom",
        room_ref="R2",
    )

    # Legacy emitter temperatures deliberately differ.
    # If emitter 70/50 were used, ΔT would be 20 K.
    # H-S22-B should use Environment 75/65, ΔT 10 K.
    project.emitters["emitter-001"] = EmitterV1(
        emitter_id="emitter-001",
        room_id="room-001",
        name="Radiator — R1 Kitchen",
        emitter_type="radiator",
        design_output_W=1000.0,
        flow_temp_C=70.0,
        return_temp_C=50.0,
    )

    project.emitters["emitter-002"] = EmitterV1(
        emitter_id="emitter-002",
        room_id="room-002",
        name="Radiator — R2 Bedroom",
        emitter_type="radiator",
        design_output_W=500.0,
        flow_temp_C=70.0,
        return_temp_C=50.0,
    )

    expected_room_1_flow = 1000.0 / (4180.0 * 10.0)
    expected_total_flow = 1500.0 / (4180.0 * 10.0)

    room_1_flow = _room_emitter_mass_flow_kg_s(project, "room-001")
    total_flow = _sum_emitter_mass_flow_kg_s(project)

    print("\n======================================")
    print("H-S22-B Environment Flow Basis")
    print("======================================")
    print(f"pipe room-001 flow = {room_1_flow:.6f} kg/s")
    print(f"pipe total flow    = {total_flow:.6f} kg/s")
    print(f"expected room-001  = {expected_room_1_flow:.6f} kg/s")
    print(f"expected total     = {expected_total_flow:.6f} kg/s")

    assert abs(room_1_flow - expected_room_1_flow) < 1e-12
    assert abs(total_flow - expected_total_flow) < 1e-12

    rows = build_branch_proportioning_summary_v1(project)

    common_main = next(
        row for row in rows
        if row.group == "Common/main" and row.role == "Common main"
    )

    expected_label = f"{expected_total_flow:.4f} kg/s"

    print(f"branch common-main flow label = {common_main.flow_label}")
    print(f"expected branch label         = {expected_label}")

    assert common_main.flow_label == expected_label

    print("\nOK — pipe and branch summaries use Environment ΔT basis.")


if __name__ == "__main__":
    main()
