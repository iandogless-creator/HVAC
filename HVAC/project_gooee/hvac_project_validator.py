"""
hvac_project_validator.py
-------------------------
# ⚠️ FROZEN — DO NOT EXTEND

Validation engine for HVACgooee project folders.

Ensures that:
    - Graph structure is sound
    - All nodes exist
    - No missing emitters
    - No circular hydronic references
    - Minimal metadata exists
    - Project is consistent enough for export & simulation
"""
"""
Project Gooee — Structural Validator
-----------------------------------

Role:
• Validates structural correctness of a Project Gooee project
• Ensures schema and referential integrity

Rules:
• No calculations
• No defaults or inference
• No GUI imports
• No ProjectState usage
• No physics or engineering validation

This module performs pre-engine validation only.
"""

from __future__ import annotations

from typing import Dict, Any, List, Set


# ---------------------------------------------------------------------------
# Basic graph helpers
# ---------------------------------------------------------------------------

def find_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """
    Detect cycles in a directed graph using DFS.
    Returns list of cycles, each cycle is a list of node IDs.
    """
    visited: Set[str] = set()
    stack: Set[str] = set()
    cycles: List[List[str]] = []

    def dfs(node: str, path: List[str]):
        if node in stack:
            idx = path.index(node)
            cycles.append(path[idx:])
            return

        if node in visited:
            return

        visited.add(node)
        stack.add(node)

        for child in graph.get(node, []):
            dfs(child, path + [child])

        stack.remove(node)

    for n in graph.keys():
        dfs(n, [n])

    return cycles


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate_project_structure(project: Dict[str, Any]) -> List[str]:
    """
    Validate the overall project structure.

    Parameters
    ----------
    project : dict returned from load_project()

    Returns
    -------
    list[str] : list of error messages (empty list means success)
    """

    errors: List[str] = []

    # -------------------------------
    # Required sections
    # -------------------------------
    required_keys = ["project", "rooms", "emitters", "hydronics"]
    for key in required_keys:
        if key not in project:
            errors.append(f"Missing section: '{key}'")

    hydronics = project.get("hydronics", {})
    graph = hydronics.get("graph", {})
    metadata = hydronics.get("metadata", {})

    # -------------------------------
    # Hydronic graph checks
    # -------------------------------
    # Missing nodes
    for parent, children in graph.items():
        if parent not in metadata:
            errors.append(f"Node '{parent}' has no metadata entry")

        for c in children:
            if c not in metadata:
                errors.append(f"Node '{c}' (child of {parent}) has no metadata")

    # -------------------------------
    # Cycle detection
    # -------------------------------
    cycles = find_cycles(graph)
    for cycle in cycles:
        cycle_str = " → ".join(cycle)
        errors.append(f"Cycle detected: {cycle_str}")

    # -------------------------------
    # Emitters referenced?
    # -------------------------------
    emitters = project.get("emitters", {})
    emitter_ids = set(emitters.keys())

    graph_ids = set(metadata.keys())
    missing_emitters = emitter_ids - graph_ids
    for e in missing_emitters:
        errors.append(f"Emitter '{e}' not referenced in hydronics graph")

    # -------------------------------
    # Rooms and emitters linking
    # -------------------------------
    rooms = project.get("rooms", {})
    for room_id, room in rooms.items():
        if "emitters" in room:
            for em in room["emitters"]:
                if em not in emitter_ids:
                    errors.append(f"Room '{room_id}' references missing emitter '{em}'")

    # -------------------------------
    # Project metadata sanity
    # -------------------------------
    proj_meta = project.get("project", {})
    if "name" not in proj_meta:
        errors.append("project.json missing required field 'name'")

    return errors


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def validate_project(project: Dict[str, Any]) -> bool:
    """
    Returns True if the project is valid.
    Prints errors otherwise.
    """
    errors = validate_project_structure(project)

    if not errors:
        return True

    print("Project validation errors:")
    for e in errors:
        print(" ✗", e)

    return False


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo():
    broken_project = {
        "project": {"name": "Test House"},
        "rooms": {"kitchen": {"emitters": ["rad1"]}},
        "emitters": {"rad1": {"output": 1200}},
        "hydronics": {
            "graph": {"boiler": ["leg1"], "leg1": ["rad1", "badnode"]},
            "metadata": {
                "boiler": {"label": "Boiler"},
                "leg1": {"label": "Leg 1"},
                # rad1 metadata missing intentionally
            },
        },
    }

    ok = validate_project(broken_project)
    print("Valid?", ok)


if __name__ == "__main__":
    _demo()
