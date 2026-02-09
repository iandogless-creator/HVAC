# ======================================================================
# HVAC/gui_v3/adapters/room_tree_panel_adapter.py
# ======================================================================
# HVACgooee — RoomTreePanelAdapter (GUI v3)
# Phase: E-A — Room Selection Wiring
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from HVAC_legacy.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC_legacy.gui_v3.panels.room_tree_panel import RoomTreePanel


class RoomTreePanelAdapter:
    """
    RoomTreePanelAdapter — GUI v3

    Phase E-A responsibilities:
    • Read room list from ProjectState (read-only)
    • Populate RoomTreePanel
    • Reflect active room selection
    • Propagate user room selection back to context

    No calculations.
    No inference.
    No authority.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        panel: RoomTreePanel,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        self._panel.room_selected.connect(self._on_room_selected)

        # Safe initial sync
        self.refresh()

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Refresh room list and active selection.

        Phase E-A rules:
        • Read-only
        • None-safe
        • No side effects
        """
        ps = self._resolve_project_state()
        if ps is None:
            self._panel.set_rooms([])
            self._panel.set_active_room(None)
            return

        rooms = self._build_room_list(ps)
        self._panel.set_rooms(rooms)

        active_room_id = getattr(ps, "active_room_id", None)
        self._panel.set_active_room(active_room_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_room_list(self, ps) -> list[tuple[object, str]]:
        """
        Build (room_id, room_name) tuples.

        Phase E-A:
        • Flat list
        • Order preserved
        """
        rooms = []

        for room in getattr(ps, "rooms", []) or []:
            room_id = getattr(room, "id", None)
            name = getattr(room, "name", None) or "Unnamed room"

            if room_id is not None:
                rooms.append((room_id, name))

        return rooms

    def _resolve_project_state(self):
        """
        Accept either:
        • context.project_state → ProjectState
        • context.project_state → ProjectV3 (container)
        """
        ps = getattr(self._context, "project_state", None)
        if ps is None:
            return None

        inner = getattr(ps, "project_state", None)
        return inner if inner is not None else ps

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------
    def _on_room_selected(self, room_id: object) -> None:
        """
        User selected a room in the tree.

        This is *intent propagation*, not authority.
        """
        ps = getattr(self._context, "project_state", None)
        if ps is None:
            return

        # Conservative: only set if attribute exists
        if hasattr(ps, "active_room_id"):
            ps.active_room_id = room_id
