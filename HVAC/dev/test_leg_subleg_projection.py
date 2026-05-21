# ======================================================================
# HVAC/dev/test_leg_subleg_projection.py
# ======================================================================

import json
from pathlib import Path

from HVAC.project.project_state import ProjectState
from HVAC.hydronics.topology.leg_subleg_projection_v1 import (
    build_leg_subleg_topology_v1,
)


PROJECT_PATH = Path("HVAC/HVACprojects/6 room/project.json")


def make_dev_project_state() -> ProjectState:
    with PROJECT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return ProjectState.from_dict(data)


def main() -> None:
    project = make_dev_project_state()
    topology = build_leg_subleg_topology_v1(project)

    print()
    print("=" * 96)
    print("HVACgooee — H-T2 Leg/Subleg Topology Projection")
    print("=" * 96)
    print()
    print(f"Basis: {topology.basis}")
    print(f"Common leg section: {topology.common_leg_section_id}")
    print(f"Selected index route circuit: {topology.selected_index_route_circuit_id}")
    print(f"True index circuit: {topology.true_index_circuit_id}")

    print()
    print("NODES")
    print("-" * 96)
    for node in topology.nodes:
        print(
            f"{node.node_id:<36} | "
            f"{node.label:<28} | "
            f"room={node.room_id or '—':<12} | "
            f"emitter={node.emitter_id or '—'}"
        )

    print()
    print("SECTIONS")
    print("-" * 132)
    for section in topology.sections:
        flow = "—" if section.flow_kg_s is None else f"{section.flow_kg_s:.4f} kg/s"
        print(
            f"{section.section_id:<36} | "
            f"{section.label:<32} | "
            f"{section.role:<18} | "
            f"{section.from_node_id} -> {section.to_node_id} | "
            f"flow={flow:<12} | "
            f"term={section.termination}"
        )

    print()
    print("TERMINAL CIRCUITS")
    print("-" * 96)
    for circuit in topology.terminal_circuits:
        print(
            f"{circuit.circuit_id:<34} | "
            f"{circuit.label:<28} | "
            f"selected={circuit.is_selected_index_route!s:<5} | "
            f"true_index={circuit.is_true_index_circuit!s:<5} | "
            f"sections={circuit.section_ids}"
        )


if __name__ == "__main__":
    main()