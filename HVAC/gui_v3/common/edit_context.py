# ======================================================================
# HVAC/gui_v3/common/edit_context.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class EditContext:
    """
    Canonical edit context for GUI v3 overlay system.

    This is the SINGLE source of truth for edit routing.
    """

    kind: str                # "surface" | "geometry" | "ach"
    room_id: str

    # Surface-level editing (Phase IV canonical)
    surface_id: Optional[str] = None

    # Optional (future / legacy compatibility)
    row: Optional[int] = None
    column: Optional[int] = None
    field: Optional[str] = None