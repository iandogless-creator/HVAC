# ======================================================================
# HVAC/gui_v3/adapters/geometry_mini_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel


class GeometryMiniPanelAdapter:
    """
    GUI v3 — Geometry Mini Panel Adapter

    Phase I-B:
    • Internal geometry only (L, W, H)
    • Internal design temperature (Ti)
    • ACH (ventilation)
    • Live derived floor area + volume
    • Emits intent only — never calculates authority
    """

    def __init__(
        self,
        *,
        panel: GeometryMiniPanel,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        # GUI → intent
        self._panel.geometry_changed.connect(self._on_geometry_changed)
        # context → GUI (room selection)
        self._context.subscribe_room_selection_changed(
            self._on_room_changed
        )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Pull geometry intent from ProjectState and present it.

        Phase I-B:
        • Geometry is room-scoped
        • Missing data clears presentation
        """
        ps = self._context.project_state
        room_id = self._context.current_room_id

        if not ps or not room_id:
            self._panel.clear()
            return

        room = ps.rooms.get(room_id)
        if not room:
            self._panel.clear()
            return

        geom = getattr(room, "geometry_intent", None)
        if not geom:
            self._panel.clear()
            return

        try:
            length = float(geom["length_m"])
            width = float(geom["width_m"])
            height = float(geom["height_m"])
            ti_c = float(geom["ti_c"])
            ach = float(geom.get("ach", 0.0))
        except (KeyError, TypeError, ValueError):
            self._panel.clear()
            return

        # Derived (presentation-only)
        floor_area = length * width
        volume = floor_area * height

        # Push to panel
        self._panel.set_inputs(
            length=length,
            width=width,
            height=height,
            ti_c=ti_c,
            ach=ach,
        )
        self._panel.set_floor_area(floor_area)
        self._panel.set_volume(volume)

    # ------------------------------------------------------------------
    # GUI → Project intent
    # ------------------------------------------------------------------
    def _on_geometry_changed(self, payload: dict) -> None:
        ps = self._context.project_state
        room_id = self._context.current_room_id

        if not ps or not room_id:
            return

        room = ps.rooms.get(room_id)
        if not room:
            return

        # Normalise & store intent
        room.geometry_intent = {
            "length_m": float(payload["length_m"]),
            "width_m": float(payload["width_m"]),
            "height_m": float(payload["height_m"]),
            "ti_c": float(payload["ti_c"]),
            "ach": float(payload["ach"]),
        }

        # Geometry changes invalidate heat-loss
        if hasattr(ps, "mark_heatloss_dirty"):
            ps.mark_heatloss_dirty()

        # Notify observers (HL panel, etc.)
        if hasattr(self._context, "refresh_all_adapters"):
            self._context.refresh_all_adapters()

    def _on_room_changed(self, room_id: str | None) -> None:
        """
        Room selection changed elsewhere in GUI.
        """
        self.refresh()
