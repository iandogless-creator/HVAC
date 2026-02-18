# ======================================================================
# HVAC/gui_v3/adapters/ach_mini_panel_adapter.py
# ======================================================================
# HVACgooee — ACH Mini Panel Adapter (GUI v3)
# Phase: E-A + I-B — Room-scoped ventilation intent
# Status: CANONICAL (intent mutation TEMPORARY)
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.ach_mini_panel import ACHMiniPanel


class ACHMiniPanelAdapter:
    """
    GUI v3 — ACH Mini Panel Adapter

    Responsibilities
    ----------------
    • Present room-scoped ACH (air changes per hour)
    • Emit intent only (no calculation, no validation)
    • React to room selection changes
    • Clear presentation when no room is active

    Notes
    -----
    • Direct mutation of RoomState is TEMPORARY (Phase I-B)
    • Will be replaced with ProjectState.with_ventilation_intent()
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        panel: ACHMiniPanel,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        # GUI → intent
        self._panel.ach_changed.connect(self._on_ach_changed)

        # context → GUI (room selection)
        self._context.subscribe_room_selection_changed(
            self._on_room_changed
        )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Refresh ACH display from ProjectState.

        Phase I-B rules:
        • Room-scoped
        • Read-only presentation
        • Missing data clears panel
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
            ach = float(geom.get("ach", 0.0))
        except (TypeError, ValueError):
            self._panel.clear()
            return

        self._panel.set_ach(ach)

    # ------------------------------------------------------------------
    # Context → GUI
    # ------------------------------------------------------------------
    def _on_room_changed(self, room_id: str | None) -> None:
        """
        React to room selection changes.
        """
        self.refresh()

    # ------------------------------------------------------------------
    # GUI → Project intent
    # ------------------------------------------------------------------
    def _on_ach_changed(self, ach: float) -> None:
        """
        User edited ACH value.

        TEMPORARY:
        Direct mutation of room geometry intent (Phase I-B).
        """
        ps = self._context.project_state
        room_id = self._context.current_room_id

        if not ps or not room_id:
            return

        room = ps.rooms.get(room_id)
        if not room:
            return

        geom = getattr(room, "geometry_intent", None)
        if geom is None:
            geom = {}

        geom["ach"] = float(ach)
        room.geometry_intent = geom

        # Invalidate heat-loss if supported
        if hasattr(ps, "mark_heatloss_dirty"):
            ps.mark_heatloss_dirty()
