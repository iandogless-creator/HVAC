# ======================================================================
# HVAC/gui_v3/adapters/room_list_adapter.py
# ======================================================================

"""
HVACgooee — Room List Adapter

Phase: D.5 — First Concrete Adapter
Status: CANONICAL

Purpose
-------
Expose a stable, read-only list of rooms to GUI panels
without leaking domain authority.
"""

from __future__ import annotations

from typing import List

from HVAC_legacy.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC_legacy.gui_v3.dto.room_list_item_dto import RoomListItemDTO


class RoomListAdapter:
    """
    Adapter for presenting project rooms in GUI lists.

    Rules
    -----
    • Read-only
    • No caching
    • No mutation
    • No domain leakage
    """

    def __init__(self, *, context: GuiProjectContext) -> None:
        self._context = context

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_room_list(self) -> List[RoomListItemDTO]:
        """
        Build a fresh list of room DTOs.

        Must be called after any project refresh.
        """
        project_state = self._context.project_state

        items: List[RoomListItemDTO] = []

        for room in project_state.rooms.values():
            geom = room.geometry

            items.append(
                RoomListItemDTO(
                    room_id=room.room_id,
                    name=room.name,
                    floor_area_m2=geom.floor_area_m2,
                    volume_m3=geom.volume_m3,
                )
            )

        return items
