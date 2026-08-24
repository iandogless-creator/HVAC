# ======================================================================
# HVAC/gui_v3/adapters/room_tree_panel_adapter.py
# ======================================================================
# HVACgooee — RoomTreePanelAdapter (GUI v3)
# Phase: E-A — Room Selection Wiring
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel
from HVAC.core.room_identity import room_short_label
from HVAC.project.guarded_room_deletion_v1 import (
    build_guarded_room_deletion_plan_v1,
    delete_room_guarded_v1,
)

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
        panel= RoomTreePanel,
        context= GuiProjectContext,
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
    def _build_room_list(self, ps) -> list[tuple[str, str]]:
        """
        Build flat list of rooms for display.

        Internal room_id remains the emitted authority.
        Label is human-facing only.
        """
        if not hasattr(ps, "rooms") or not ps.rooms:
            return []

        return [
            (room_id, room_short_label(room_id, room))
            for room_id, room in ps.rooms.items()
        ]

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

    def request_room_removal_v1(
            self,
            room_id: str | None,
            *,
            parent=None,
    ) -> None:
        dialog_parent = parent if parent is not None else self._panel
        ps = self._context.project_state
        if ps is None or not room_id:
            return

        plan = build_guarded_room_deletion_plan_v1(ps, room_id)
        if not plan.ready:
            QMessageBox.warning(
                dialog_parent,
                "Remove Room",
                "Room cannot be removed:\n\n"
                + "\n".join(f"• {reason}" for reason in plan.blockers),
            )
            return

        room = ps.rooms.get(room_id)
        room_label = room_short_label(room_id, room)
        answer = QMessageBox.question(
            dialog_parent,
            "Remove Room",
            f"Remove {room_label}?\n\n"
            "Its room-owned surfaces and opening schedule will also be removed.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        ordered_room_ids = list(ps.rooms)
        removed_index = ordered_room_ids.index(room_id)
        remaining_room_ids = [
            candidate
            for candidate in ordered_room_ids
            if candidate != room_id
        ]
        next_room_id = remaining_room_ids[
            min(removed_index, len(remaining_room_ids) - 1)
        ]

        self._context.set_current_room(None)
        delete_room_guarded_v1(ps, room_id)
        self._context.notify_project_changed()
        self._context.set_current_room(next_room_id)
