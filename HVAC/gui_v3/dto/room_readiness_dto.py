# ======================================================================
# HVACgooee — Room Readiness DTO
# Phase: D.7 — Presence-Based Readiness
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class RoomReadinessDTO:
    """
    GUI-owned readiness status for a single room.

    Presence-based only.
    Non-authoritative.
    """

    room_id: str
    name: str
    is_ready: bool
    missing_items: List[str]
