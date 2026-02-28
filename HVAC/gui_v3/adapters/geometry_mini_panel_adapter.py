from __future__ import annotations
from typing import Any

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel
from HVAC.gui_v3.panels.ach_mini_panel import ACHMiniPanel

class GeometryMiniPanelAdapter:
    """
    Phase I-B — Geometry intent adapter
    """

    def __init__(self, panel: GeometryMiniPanel, context: GuiProjectContext) -> None:
        self._panel = panel
        self._context = context

        self._panel.geometry_changed.connect(self._on_geometry_changed)
        self._context.current_room_changed.connect(self.refresh)

        self.refresh()

    def refresh(self) -> None:
        room_id = self._context.current_room_id
        if not room_id:
            self._panel.clear()
            return

        ps = self._context.project_state
        room = ps.rooms.get(room_id) if ps else None
        if not room or not getattr(room, "geometry_intent", None):
            self._panel.clear()
            return

        gi = room.geometry_intent
        self._panel._spin_length.setValue(gi["length_m"])
        self._panel._spin_width.setValue(gi["width_m"])
        self._panel._spin_height.setValue(gi["height_m"])
        self._panel._spin_ti.setValue(gi["ti_c"])

    def _on_geometry_changed(self, payload: dict[str, Any]) -> None:
        room_id = self._context.current_room_id
        if not room_id:
            return

        # Emit intent ONLY — no calculation
        self._context.emit_geometry_intent_changed(
            room_id=room_id,
            geometry=payload,
        )

    # HVAC/gui_v3/adapters/geometry_mini_panel_adapter.py

    def commit_geometry(self, length_m: float, width_m: float, height_m: float) -> None:
        ps = self._context.project_state
        room = self._context.current_room
        if ps is None or room is None:
            return

        room.geometry.length_m = length_m
        room.geometry.width_m = width_m
        room.geometry.height_m = height_m

        # Phase I-B
        ps.mark_heatloss_dirty()