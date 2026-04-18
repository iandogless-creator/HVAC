# ======================================================================
# HVAC/gui_v3/dto/adjacency_options.py
# ======================================================================

from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class RoomOption:
    room_id: str
    name: str
    available_count: int
    enabled: bool  # ≥1 free segment and not same room


@dataclass(slots=True)
class SegmentOption:
    segment_id: str
    label: str      # e.g. "Wall 2"
    length_m: float
    enabled: bool   # length-compatible with source (adapter can pre-filter)