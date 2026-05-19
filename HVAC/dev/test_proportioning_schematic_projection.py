
# ======================================================================
# HVAC/dev/test_proportioning_schematic_projection.py
# ======================================================================

import json
from pathlib import Path

from HVAC.project.project_state import ProjectState
from HVAC.hydronics.proportioning.proportioning_schematic_projection_v1 import (
    build_proportioning_schematic_v1,
)


PROJECT_PATH = Path("HVAC/HVACprojects/6 room/project.json")


def make_dev_project_state() -> ProjectState:
    with PROJECT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return ProjectState.from_dict(data)


def main() -> None:
    project = make_dev_project_state()
    schematic = build_proportioning_schematic_v1(project)

    print()
    print("=" * 96)
    print("HVACgooee — H-S1 Proportioning Schematic Projection")
    print("=" * 96)
    print()
    print(f"Title: {schematic.title}")
    print(f"Basis: {schematic.basis}")

    print()
    print("NODES")
    print("-" * 96)
    for node in schematic.nodes:
        print(
            f"{node.node_id:<34} | "
            f"{node.role:<34} | "
            f"lane={node.lane:<2} | "
            f"order={node.order:<2} | "
            f"{node.label}"
        )

    print()
    print("EDGES")
    print("-" * 96)
    for edge in schematic.edges:
        print(
            f"{edge.edge_id:<42} | "
            f"{edge.role:<34} | "
            f"{edge.from_node_id} -> {edge.to_node_id} | "
            f"flow={edge.flow_label} | "
            f"status={edge.status}"
        )


if __name__ == "__main__":
    main()