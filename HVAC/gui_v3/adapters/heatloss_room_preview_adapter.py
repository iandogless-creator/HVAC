# ======================================================================
# HVACgooee — Heat-Loss Room Preview Adapter
# Phase: D.6 — Preview Semantics
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from typing import List

from HVAC_legacy.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC_legacy.gui_v3.dto.heat_loss_preview_dto import HeatLossPreviewDTO


class HeatLossRoomPreviewAdapter:
    """
    Read-only adapter providing non-authoritative room-level
    heat-loss preview values.

    No calculations.
    No mutation.
    """

    def __init__(self, *, context: GuiProjectContext) -> None:
        self._context = context

    def build_room_previews(self) -> List[HeatLossPreviewDTO]:
        ps = self._context.project_state
        previews: List[HeatLossPreviewDTO] = []

        for room in ps.rooms.values():
            previews.append(
                HeatLossPreviewDTO(
                    room_id=room.room_id,
                    name=room.name,
                    preview_heatloss_qt_w=room.heatloss_preview_qt_w,
                )
            )

        return previews
