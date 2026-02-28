# ======================================================================
# HVAC/gui_v3/context/gui_project_context.py
# ======================================================================

"""
HVACgooee — GUI Project Context

Phase: D.2 / I-J / K-A — Authority Boundary
Status: CANONICAL

Purpose
-------
GUI-only coordination state:
• Current room focus
• Heat-Loss run intent (HLPA)
• HLPE session state

Authority rules
---------------
• Owns NO engineering data
• Does NOT compute
• Reads ProjectState only
• Emits GUI intent via signals
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Optional, Literal, Callable

from PySide6.QtCore import QObject, Signal

from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.project.project_state import ProjectState

# ----------------------------------------------------------------------
# Types
# ----------------------------------------------------------------------

HLPEditScope = Literal["geometry", "assumptions", "construction"]


# ----------------------------------------------------------------------
# GUI-only run intent (HLPA-owned)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class HeatLossRunContext:
    """
    GUI-owned heat-loss run intent.

    Phase II-A rules:
    • GUI sets
    • Controller consumes
    • ProjectState never sees this
    """
    internal_design_temp_C: float | None = None


# ======================================================================
# GuiProjectContext
# ======================================================================

class GuiProjectContext(QObject):
    """
    GUI v3 — Project Context (Observer / Intent Bridge)
    """

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    current_room_changed = Signal(object)   # room_id | None
    hlpe_active_changed = Signal(bool)
    # --------------------------------------------------------------
    # UVP focus (GUI-only intent)
    # --------------------------------------------------------------
    _uvp_surface_id: str | None = None
    _uvp_subscribers: list[callable] = []
    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, *, project_state: ProjectState) -> None:
        super().__init__()

        # ---------------- Authoritative project ----------------
        self._project_state: ProjectState = project_state

        # ---------------- GUI-only focus ----------------
        self._current_room_id: Optional[str] = None

        # ---------------- Heat-loss run intent ----------------
        self.heatloss_run_context = HeatLossRunContext()

        # ---------------- HLPE session state ----------------
        self._hlpe_active: bool = False
        self.hlpe_scope: Optional[HLPEditScope] = None
        self.hlpe_target_room_id: Optional[str] = None
        self.hlpe_target_surface_id: Optional[str] = None

        # ---------------- GUI settings ----------------
        settings_dir = Path.home() / ".hvacgooee" / "gui"
        settings_dir.mkdir(parents=True, exist_ok=True)
        self._gui_settings = GuiSettings(settings_dir=settings_dir)

        # ---------------- Observers ----------------
        self._room_selection_listeners: list[Callable[[Optional[str]], None]] = []

    # ==================================================================
    # Read-only access
    # ==================================================================
    @property
    def project_state(self) -> ProjectState:
        return self._project_state

    @property
    def gui_settings(self) -> GuiSettings:
        return self._gui_settings

    @property
    def current_room_id(self) -> Optional[str]:
        return self._current_room_id

    # ==================================================================
    # Project switching (authoritative swap)
    # ==================================================================
    def set_project_state(self, project_state: ProjectState) -> None:
        self._project_state = project_state
        self.set_current_room(None)
        self.close_hlpe()

    # --------------------------------------------------------------
    # UVP focus (GUI-only intent)
    # --------------------------------------------------------------
    def set_uvp_focus(self, surface_id: str | None) -> None:
        self._uvp_surface_id = surface_id
        for cb in self._uvp_subscribers:
            cb(surface_id)

    def get_uvp_focus(self) -> str | None:
        return self._uvp_surface_id

    def subscribe_uvp_focus(self, callback) -> None:
        self._uvp_subscribers.append(callback)

    def request_uvp_focus(self, surface_id: str | None = None) -> None:
        """
        GUI intent: request U-Values panel focus.

        May be surface-specific or generic.
        """
        self.set_uvp_focus(surface_id)



    # ==================================================================
    # Project loading (Phase K-A)
    # ==================================================================
    def load_project(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        project_state = ProjectState.from_dict(payload)
        self.set_project_state(project_state)

    # ==================================================================
    # Room focus (GUI-only)
    # ==================================================================
    def set_current_room(self, room_id: Optional[str]) -> None:
        if self._current_room_id == room_id:
            return

        self._current_room_id = room_id
        self.current_room_changed.emit(room_id)

        for cb in list(self._room_selection_listeners):
            cb(room_id)

    def subscribe_room_selection_changed(
        self,
        callback: Callable[[Optional[str]], None],
    ) -> None:
        self._room_selection_listeners.append(callback)

    # ==================================================================
    # HLPE session control (GUI-only)
    # ==================================================================
    @property
    def hlpe_active(self) -> bool:
        return self._hlpe_active

    def open_hlpe(
        self,
        *,
        scope: HLPEditScope,
        room_id: str,
        surface_id: Optional[str] = None,
    ) -> None:
        if self._hlpe_active:
            return

        self._hlpe_active = True
        self.hlpe_scope = scope
        self.hlpe_target_room_id = room_id
        self.hlpe_target_surface_id = surface_id
        self.hlpe_active_changed.emit(True)

    def close_hlpe(self) -> None:
        if not self._hlpe_active:
            return

        self._hlpe_active = False
        self.hlpe_scope = None
        self.hlpe_target_room_id = None
        self.hlpe_target_surface_id = None
        self.hlpe_active_changed.emit(False)