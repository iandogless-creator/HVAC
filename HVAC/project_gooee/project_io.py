"""
project_io.py
--------------
Simple JSON project loader/saver for HVACgooee v1.
"""
# ⚠️ FROZEN — DO NOT EXTEND

from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path


PROJECT_VERSION = "1.0"


def save_project(path: str, data: dict) -> None:
    """Save project data to a JSON file."""
    full = {
        "version": PROJECT_VERSION,
        **data
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(full, f, indent=4)


def load_project(path: str) -> dict:
    """Load project JSON data."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
