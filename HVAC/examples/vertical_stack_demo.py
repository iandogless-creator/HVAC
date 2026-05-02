# ======================================================================
# HVACgooee — Vertical Stack Demo (EURIKA v1)
# ======================================================================

"""
Demonstrates:

• Topology-driven fabric generation
• Vertical adjacency (3-room stack)
• Deterministic ΔT resolution
• Fabric heat loss (Qf = A × U × ΔT)

This is a headless, non-GUI example.
"""

from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1

from HVAC.dev.bootstrap_vertical_3room import (
    build_vertical_stack_project_state
)

from HVAC.fabric.generate_fabric_from_topology import (
    generate_fabric_from_topology
)


# ======================================================================
# Helpers
# ======================================================================

def print_room_results(project: ProjectState, room_id: str) -> None:
    room = project.rooms[room_id]

    print("\n--- ROOM:", room_id, "---")
    print(f"Ti = {room.internal_temp_C:.1f} °C")
    print(f"Te = {project.environment.external_design_temp_C:.1f} °C")

    rows = generate_fabric_from_topology(project, room)

    total_qf = 0.0

    for r in rows:
        adj = r.adjacent_room_id or "EXT"

        print(
            f"{r.surface_class:12} | "
            f"A={r.area_m2:.2f} | "
            f"U={r.u_value_W_m2K:.2f} | "
            f"dT={r.delta_t_K:.2f} | "
            f"Qf={r.qf_W:.2f} | "
            f"{r.boundary_kind} → {adj}"
        )

        total_qf += r.qf_W

    print(f"ΣQf = {total_qf:.2f} W")


# ======================================================================
# Main
# ======================================================================

def main() -> None:

    print("\n==============================")
    print("HVACgooee — Vertical Stack Demo")
    print("EURIKA v1 — Authoritative Pipeline")
    print("==============================")

    # --------------------------------------------------
    # Build project (authoritative bootstrap)
    # --------------------------------------------------

    project = build_vertical_stack_project_state()

    # --------------------------------------------------
    # Evaluate each room
    # --------------------------------------------------

    for room_id in project.rooms:
        print_room_results(project, room_id)


# ======================================================================
# Entry
# ======================================================================

if __name__ == "__main__":
    main()