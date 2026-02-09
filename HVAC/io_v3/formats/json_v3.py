# ======================================================================
# HVAC/io_v3/formats/json_v3.py
# ======================================================================

"""
JSON format handler v3
"""

from __future__ import annotations
import json
from typing import Dict, Any


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
