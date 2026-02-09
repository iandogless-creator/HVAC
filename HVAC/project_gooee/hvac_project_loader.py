"""
hvac_project_loader.py
----------------------
# ⚠️ FROZEN — DO NOT EXTEND

Unified loader for HVACgooee project folders.

A typical project directory may contain:

    project.json        → metadata (name, client, date)
    rooms.json          → room geometry + heat-loss data
    emitters.json       → radiators, FCUs, UFH loops
    hydronics.json      → graph + metadata + connectors
    materials.json      → optional material definitions
    settings.toml       → project-level overrides

This loader does **three things**:

1. Normalises the project directory structure
2. Loads all available files
3. Returns a structured Python dict that downstream modules can use
"""
"""
Project Gooee — Project Loader
------------------------------

Role:
• Loads an HVACgooee project from disk
• Assembles Project Gooee domain objects

Rules:
• No calculations
• No defaults or inference
• No GUI imports
• No ProjectState usage
• Structural validation only

This module defines the disk → domain boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _maybe_load_json(path: Path) -> Dict[str, Any] | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _maybe_load_toml(path: Path) -> Dict[str, Any] | None:
    if not path.is_file() or tomllib is None:
        return None
    with path.open("rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------

def load_project(project_dir: Path) -> Dict[str, Any]:
    """
    Load an HVACgooee project directory.

    Returns a dict:
    {
        "project": {...},
        "rooms": {...},
        "emitters": {...},
        "hydronics": {...},
        "materials": {...},
        "settings": {...},
        "path": <Path>
    }
    """

    project_dir = project_dir.resolve()

    project = _maybe_load_json(project_dir / "project.json")
    rooms = _maybe_load_json(project_dir / "rooms.json")
    emitters = _maybe_load_json(project_dir / "emitters.json")
    hydronics = _maybe_load_json(project_dir / "hydronics.json")
    materials = _maybe_load_json(project_dir / "materials.json")
    settings = _maybe_load_toml(project_dir / "settings.toml")

    return {
        "project": project or {},
        "rooms": rooms or {},
        "emitters": emitters or {},
        "hydronics": hydronics or {},
        "materials": materials or {},
        "settings": settings or {},
        "path": project_dir,
    }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo():
    example = Path("example_project")
    data = load_project(example)
    print(data)


if __name__ == "__main__":
    _demo()
