# ======================================================================
# HVAC/hydronics/probes/probe_emitter_candidate_builder_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.adapters.emitter_candidate_builder_v1 import (
    EmitterCandidateBuilderV1,
)
from HVAC.hydronics.adapters.room_emitter_demand_adapter_v1 import (
    RoomEmitterDemandAdapterV1,
)


def _make_project_state():
    try:
        from HVAC.dev.bootstrap_dev_project import make_dev_project_state
        return make_dev_project_state()
    except ImportError:
        pass

    try:
        from HVAC.dev.bootstrap_project_state import make_dev_bootstrap_project_state
        return make_dev_bootstrap_project_state()
    except ImportError:
        pass

    try:
        from HVAC.dev.bootstrap_dev_project import make_project_state
        return make_project_state()
    except ImportError:
        pass

    raise RuntimeError(
        "No recognised DEV project bootstrap found. "
        "Check HVAC/dev bootstrap function names."
    )


def main() -> None:
    project = _make_project_state()

    builder = EmitterCandidateBuilderV1()
    created = builder.ensure_default_emitters(project)

    print("\nHydronics H-C — Emitter candidate builder\n")
    print(f"Created emitters: {created}")
    print(f"Total emitters:   {len(project.emitters)}")

    print("\nEmitter demand rows after candidate creation:\n")

    demand_adapter = RoomEmitterDemandAdapterV1()
    rows = demand_adapter.build_rows(project)

    for row in rows:
        heat_load = (
            "—"
            if row.design_heat_load_W is None
            else f"{row.design_heat_load_W:.1f} W"
        )

        emitter_output = (
            "—"
            if row.emitter_output_W is None
            else f"{row.emitter_output_W:.1f} W"
        )

        print(
            f"{row.room_id:16s} | "
            f"{row.room_name:24s} | "
            f"load={heat_load:>10s} | "
            f"emitters={row.emitter_count:>2d} | "
            f"summary={row.emitter_summary:>18s} | "
            f"output={emitter_output:>10s} | "
            f"{row.status}"
        )


if __name__ == "__main__":
    main()