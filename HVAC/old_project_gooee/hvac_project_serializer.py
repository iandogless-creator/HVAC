"""
hvac_project_serializer.py
--------------------------
# ⚠️ FROZEN — DO NOT EXTEND

Central serializer for HVACgooee objects.

Converts internal Python objects (Room, Emitter, HydronicNode, Pipe, etc.)
into clean, JSON-serializable dictionaries. Also performs the reverse,
turning clean dictionaries back into object instances (future expansion).

This keeps saving/loading consistent across:
    - project loader
    - project saver
    - GUI
    - DXF exporter
    - CLI tools
"""
"""
Project Gooee — Serializer
--------------------------

Role:
• Translates Project Gooee domain models to/from
  JSON-safe representations

Rules:
• No calculations
• No defaults or inference
• No file IO
• No GUI imports
• No ProjectState usage

This module defines the domain ↔ representation boundary.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_value(value: Any) -> Any:
    """
    Serialize a single value to something JSON/TOML-friendly.
    """

    # Basic Python types pass straight through
    if value is None or isinstance(value, (int, float, str, bool)):
        return value

    # Lists: serialize elements
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]

    # Dicts: serialize key/values
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}

    # Dataclasses: convert to dict then serialize
    if is_dataclass(value):
        return _serialize_value(asdict(value))

    # Tuples: convert to lists
    if isinstance(value, tuple):
        return [_serialize_value(v) for v in value]

    # Anything else: stringify as fallback
    return str(value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def serialize_project_object(obj: Any) -> Any:
    """
    Convert an internal HVACgooee object to a JSON/TOML serializable object.

    Examples:

        serialize_project_object(Room(...))     → dict
        serialize_project_object([Room(...)])   → list[dict]
        serialize_project_object({"x": Room})   → dict

    This is used by hvac_project_saver before writing to disk.
    """
    return _serialize_value(obj)


def serialize_entire_project(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize the entire project dict returned by the GUI or internal systems.

    This ensures that:
        - All dataclasses are converted to dicts
        - All custom classes are serialized
        - Lists/dicts are clean
        - Non-serializable objects never reach the saver

    Returns
    -------
    dict : fully serialized version of the project.
    """

    return {key: _serialize_value(value) for key, value in project.items()}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo():
    from dataclasses import dataclass

    @dataclass
    class Room:
        name: str
        area: float
        emitters: List[str]

    room = Room("Kitchen", 12.5, ["rad1"])
    obj = {
        "room": room,
        "nested": {"inner": (1, 2, 3)},
        "misc": [Room("Bath", 6.5, ["rad2"])]
    }

    print(serialize_entire_project(obj))


if __name__ == "__main__":
    _demo()

