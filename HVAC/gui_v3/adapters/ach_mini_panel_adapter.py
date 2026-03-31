# ======================================================================
# HVAC/gui_v3/adapters/ach_mini_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Optional, Any

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.ach_mini_panel import ACHMiniPanel
from HVAC.core.value_resolution import resolve_effective_ach

class ACHMiniPanelAdapter:
    """
    ACH Mini Panel Adapter (GUI v3 — Overlay Model)

    Responsibilities
    ----------------
    • Prime ACHMiniPanel from ProjectState
    • Receive committed ACH value from panel
    • Apply ACH to authoritative room state
    • Mark heat-loss dirty
    • Trigger global refresh

    Authority
    ---------
    • Reads and writes ProjectState
    • Does NOT perform calculations
    • Does NOT access panel widgets directly
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        panel: ACHMiniPanel,
        context: GuiProjectContext,
        refresh_all_callback,
    ) -> None:
        self._panel = panel
        self._context = context
        self._refresh_all = refresh_all_callback

        self._bind_panel_signals()
        self._context.current_room_changed.connect(self._on_room_changed)
        self._panel.value_changed.connect(self._on_ach_changed)
        self.refresh()

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _bind_panel_signals(self) -> None:
        if hasattr(self._panel, "ach_committed"):
            self._panel.ach_committed.connect(self._on_ach_committed)
        elif hasattr(self._panel, "ach_changed"):
            self._panel.ach_changed.connect(self._on_ach_committed)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def refresh(self):
        ps = self._context.project_state
        room_id = self._context.current_room_id
        if not room_id:
            return

        room = ps.rooms.get(room_id)
        if room is None:
            return

        # ✅ THIS LINE
        ach, _ = resolve_effective_ach(ps, room)

        # ✅ AND THIS LINE
        self._panel.set_value(ach or 0.0)

    # ------------------------------------------------------------------
    # Context → panel
    # ------------------------------------------------------------------
    def _on_room_changed(self, _room_id: Optional[str]) -> None:
        self.refresh()

    def _on_ach_changed(self, value: float) -> None:
        ps = self._context.project_state
        room_id = self._context.current_room_id
        if not room_id:
            return

        room = ps.rooms.get(room_id)
        if room is None:
            return

        # write override
        room.ach_override = value

        # mark dirty
        ps.mark_heatloss_dirty()

        # trigger UI refresh (THIS is the correct mechanism)
        self._refresh_all()

    # ------------------------------------------------------------------
    # Panel → ProjectState
    # ------------------------------------------------------------------
    def _on_ach_committed(self, ach: float) -> None:
        ps = self._context.project_state
        room_id = self._context.current_room_id

        if ps is None or not room_id:
            return

        room = ps.rooms.get(room_id)
        if room is None:
            return

        value = float(ach)

        # Authoritative write
        room.ach_override = value

        # Mark dirty
        if hasattr(ps, "mark_heatloss_dirty"):
            ps.mark_heatloss_dirty()

        # Single refresh entry point
        self._refresh_all()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_ach_value(self, ps: Any, room: Any) -> float:
        """
        Single source of truth: shared resolver
        """
        ach, _ = resolve_effective_ach(ps, room)
        return float(ach) if ach is not None else 0.0

    def _push_ach_to_panel(self, ach_value: float) -> None:
        if hasattr(self._panel, "set_ach"):
            self._panel.set_ach(ach_value)
        elif hasattr(self._panel, "set_value"):
            self._panel.set_value(ach_value)
        else:
            self._panel.clear()

    # ------------------------------------------------------------------
    # Compatibility API (temporary)
    # ------------------------------------------------------------------
    def commit_air_change_rate(self, ach: float) -> None:
        self._on_ach_committed(float(ach))