# HVAC/dev/test_heatloss_pipeline.py

from HVAC.dev.bootstrap_phase_iv_b_adjacency import bootstrap_phase_iv_b
from HVAC.heatloss.fabric.row_builder_v1 import build_rows_with_meta
from HVAC.core.value_resolution import resolve_effective_internal_temp_C
from HVAC.topology.adjacency_delta_t_resolver import AdjacencyDeltaTResolver
from HVAC.dev.bootstrap_project_state import bootstrap_project_state

def run_isolation_test():
    print("\n==============================")
    print("HVACgooee Isolation Test")
    print("==============================\n")

    ps = bootstrap_phase_iv_b()

    for room_id, room in ps.rooms.items():
        print(f"\n--- ROOM: {room_id} ---")

        # --------------------------------------------------
        # Ti / Te
        # --------------------------------------------------
        ti, _ = resolve_effective_internal_temp_C(ps, room)
        te = ps.environment.external_design_temp_C

        print(f"Ti = {ti} °C")
        print(f"Te = {te} °C")

        # --------------------------------------------------
        # Rows
        # --------------------------------------------------
        rows, metas = build_rows_with_meta(ps, room)

        print(f"[ROWS] {len(rows)} rows")

        # --------------------------------------------------
        # Inspect each surface
        # --------------------------------------------------
        for r in rows:
            get = r.get if isinstance(r, dict) else lambda k, d=None: getattr(r, k, d)

            sid = get("surface_id")
            element = get("element")
            A = get("A")
            U = get("U")
            seg = get("_segment")

            # Resolve ΔT using canonical resolver
            dt = AdjacencyDeltaTResolver.resolve_delta_t_K(
                project_state=ps,
                owner_room=room,
                boundary_kind=seg.boundary_kind if seg else "EXTERNAL",
                adjacent_room_id=seg.adjacent_room_id if seg else None,
            )

            # Compute Qf manually
            qf = None
            if A is not None and U is not None and dt is not None:
                qf = A * U * dt

            print(
                f"{sid:20s} | {element:20s} | "
                f"A={A:6.2f} | U={U} | dT={dt} | Qf={qf}"
            )

    print("\n==============================")
    print("END TEST")
    print("==============================\n")


if __name__ == "__main__":
    run_isolation_test()