# ======================================================================
# HVACgooee — Room List Item DTO
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RoomListItemDTO:
    """
    GUI-owned DTO representing a room in list views.

    Contains display-safe data only.
    """

    room_id: str
    name: str
    floor_area_m2: float
    volume_m3: float
