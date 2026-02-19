# ======================================================================
# HVAC/gui_v3/adapters/room_tree_panel_adapter.py
# ======================================================================
# HVACgooee — RoomTreePanelAdapter (GUI v3)
# Phase: E-A — Room Selection Wiring
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel


class RoomTreePanelAdapter:
    """
    RoomTreePanelAdapter — GUI v3

    Phase E-A responsibilities:
    • Read room list from ProjectState (read-only)
    • Populate RoomTreePanel
    • Reflect active room selection
    • Propagate user selection to GUI context

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

        # GUI → context
        self._panel.room_selected.connect(self._on_room_selected)

        # context → GUI
        # context → GUI
        self._context.current_room_changed.connect(
            self._on_context_room_changed
        )

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
        ps = self._context.project_state
        if ps is None:
            self._panel.set_rooms([])
            self._panel.set_active_room(None)
            return

        rooms = self._build_room_list(ps)
        self._panel.set_rooms(rooms)

        # Reflect current GUI focus
        self._panel.set_active_room(self._context.current_room_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_room_list(self, ps) -> list[str]:
        """
        Build flat list of room IDs.

        Phase E-A:
        • Flat list
        • Room ID is the label
        """
        if not hasattr(ps, "rooms") or not ps.rooms:
            return []

        return list(ps.rooms.keys())

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------
    def _on_room_selected(self, room_id: str | None) -> None:
        """
        User clicked a room in the Rooms panel.
        """
        self._context.set_current_room(room_id)

    def _on_context_room_changed(self, room_id: str | None) -> None:
        """
        Room selection changed elsewhere (bootstrap, programmatic).
        """
        self._panel.set_active_room(room_id)
