from HVAC.dev.bootstrap_project_state import make_dev_bootstrap_project_state
from HVAC.topology.dev_topology_fabric_bridge import generate_fabric_from_topology
from HVAC.core.value_resolution import resolve_effective_internal_temp_C
from HVAC.topology.adjacency_delta_t_resolver import AdjacencyDeltaTResolver
from HVAC.dev.bootstrap_vertical_3room import make_vertical_3room_project

ps = make_vertical_3room_project()

def run_isolation_test():
    print("\n==============================")
    print("HVACgooee Isolation Test")
    print("==============================\n")

    ps = make_vertical_3room_project()

    for room_id, room in ps.rooms.items():
        print(f"\n--- ROOM: {room_id} ---")

        ti, _ = resolve_effective_internal_temp_C(ps, room)
        te = ps.environment.external_design_temp_C

        print(f"Ti = {ti} °C")
        print(f"Te = {te} °C")

        rows = generate_fabric_from_topology(ps, room)

        print(f"[ROWS] {len(rows)} rows")

        for r in rows:
            get = r.get if isinstance(r, dict) else lambda k, d=None: getattr(r, k, d)

            sid = get("element_id")
            element = get("surface_class")
            A = get("area_m2")
            U = get("u_value_W_m2K")  # will be None for now
            seg = get("_segment")

            dt = AdjacencyDeltaTResolver.resolve_delta_t_K(
                project_state=ps,
                owner_room=room,
                boundary_kind=get("boundary_kind"),
                adjacent_room_id=get("adjacent_room_id"),
            )

            qf = None  # ALWAYS define first

            if A is not None and U is not None and dt is not None:
                qf = A * U * dt

            if seg:
                print(f"boundary={seg.boundary_kind}, adj={seg.adjacent_room_id}")
            else:
                print("boundary=DERIVED, adj=None")
            sid_str = sid if isinstance(sid, str) else str(sid or "N/A")
            element_str = element if isinstance(element, str) else str(element or "N/A")

            print(
                f"{sid_str:20s} | {element_str:20s} | "
                f"A={A} | U={U} | dT={dt} | Qf={qf}"
            )

    print("\n==============================")
    print("END TEST")
    print("==============================\n")


if __name__ == "__main__":
    run_isolation_test()