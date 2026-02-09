"""
hvac_project_saver.py
---------------------
# ⚠️ FROZEN — DO NOT EXTEND

Saves HVACgooee project data to disk in a clean, structured format.

Complements hvac_project_loader.py.

Default project directory structure:

    project_dir/
        project.json
        rooms.json
        emitters.json
        hydronics.json
        materials.json
        settings.toml
"""
"""
Project Gooee — Saver
---------------------

Role:
• Persists Project Gooee domain models to disk
• Writes declared project intent only

Rules:
• No calculations
• No defaults or inference
• No GUI imports
• No ProjectState usage
• Uses serializer for representation

This module defines the domain → disk boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

try:
    import tomllib  # Python 3.11+
    import tomli_w  # TOML writer (tiny package)
except ModuleNotFoundError:
    tomllib = None
    tomli_w = None


# ---------------------------------------------------------------------------
# JSON save helper
# ---------------------------------------------------------------------------

def _save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------------------------
# TOML save helper
# ---------------------------------------------------------------------------

def _save_toml(path: Path, data: Dict[str, Any]) -> None:
    if tomli_w is None:
        raise RuntimeError("tomli_w not installed (needed for writing TOML files)")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        tomli_w.dump(data, f)


# ---------------------------------------------------------------------------
# Main saver
# ---------------------------------------------------------------------------

def save_project(
        project_data: Dict[str, Any],
        target_dir: Path,
) -> Path:
    """
    Save a complete HVACgooee project to a directory.

    Parameters
    ----------
    project_data : dict
        {
            "project": {...},
            "rooms": {...},
            "emitters": {...},
            "hydronics": {...},
            "materials": {...},
            "settings": {...}
        }

    target_dir : Path
        Location to store the project files.

    Returns
    -------
    Path : resolved path to the project directory
    """

    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    # JSON files
    if "project" in project_data:
        _save_json(target_dir / "project.json", project_data["project"])
    if "rooms" in project_data:
        _save_json(target_dir / "rooms.json", project_data["rooms"])
    if "emitters" in project_data:
        _save_json(target_dir / "emitters.json", project_data["emitters"])
    if "hydronics" in project_data:
        _save_json(target_dir / "hydronics.json", project_data["hydronics"])
    if "materials" in project_data:
        _save_json(target_dir / "materials.json", project_data["materials"])

    # TOML settings
    if "settings" in project_data:
        if tomli_w is None:
            raise RuntimeError("Cannot save settings.toml — tomli_w not installed.")
        _save_toml(target_dir / "settings.toml", project_data["settings"])

    return target_dir


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo():
    example = {
        "project": {"name": "Example House"},
        "rooms": {"kitchen": {"area": 12}},
        "emitters": {"kitchen_rad": {"output": 1200}},
        "hydronics": {"graph": {}, "metadata": {}},
        "materials": {},
        "settings": {"ui": {"mode": "simple"}}
    }

    out = save_project(example, Path("example_project_saved"))
    print("Project saved to:", out)


if __name__ == "__main__":
    _demo()
