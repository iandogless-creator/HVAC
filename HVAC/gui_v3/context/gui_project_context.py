# ======================================================================
# HVAC/gui_v3/context/gui_project_context.py
# ======================================================================

"""
HVACgooee — GUI Project Context

Phase: D.2 / I-J / K-A / III — Authority Boundary
Status: CANONICAL

Purpose
-------
GUI-only coordination state:

• Current room focus
• Heat-Loss run intent (HLPA)
• HLPE session state
• Filesystem binding (project_dir)
• Workspace root

Authority rules
---------------
• Owns NO engineering data
• Does NOT compute
• Reads ProjectState only
• Emits GUI intent via signals
• Does NOT load/save directly (persistence layer handles that)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal, Callable, List
from PySide6.QtCore import QObject, Signal
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.project.project_state import ProjectState


# ----------------------------------------------------------------------
# Types
# ----------------------------------------------------------------------

HLPEditScope = Literal["geometry", "assumptions", "construction"]


# ----------------------------------------------------------------------
# GUI-only run intent
# ----------------------------------------------------------------------

@dataclass(slots=True)
class HeatLossRunContext:
    """
    GUI-owned heat-loss run intent.

    Rules:
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
    environment_changed = Signal()
    room_state_changed = Signal(str)  # room_id
    edit_requested = Signal(str, str)  # kind, surface_id
    adjacency_edit_requested = Signal(str)  # surface_id
    construction_focus_changed = Signal(str)  # construction_id
    project_changed = Signal()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, *, project_state: ProjectState) -> None:
        super().__init__()

        # ---------------- Authoritative project ----------------
        self._project_state: ProjectState = project_state

        # Filesystem binding (GUI concern only)
        self.project_dir: Path | None = None

        # Workspace root (default open/save location)
        self.workspace_root: Path = Path.cwd() / "HVACProjects"
        self.workspace_root.mkdir(exist_ok=True)

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

        # ---------------- UVP focus ----------------
        self._uvp_surface_id: Optional[str] = None
        self._uvp_subscribers: List[Callable[[Optional[str]], None]] = []

        # ---------------- Observers ----------------
        self._room_selection_listeners: List[Callable[[Optional[str]], None]] = []

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

    def notify_project_changed(self) -> None:
        self.project_changed.emit()


    # ==================================================================
    # Project switching (authoritative swap)
    # ==================================================================

    # HVAC/gui_v3/context/gui_project_context.py

    def set_project_state(
            self,
            project_state: ProjectState,
            project_dir: Path | None = None,
    ) -> None:
        """
        Authoritative ProjectState swap.

        Rules
        -----
        • ProjectState owns engineering state
        • Context owns GUI focus only
        • project_dir is stored on ProjectState
        • current_room_id is changed only via backing field or set_current_room()
        """

        # --------------------------------------------------
        # Swap authoritative state
        # --------------------------------------------------
        self._project_state = project_state

        # --------------------------------------------------
        # Filesystem binding
        # --------------------------------------------------
        self._project_state.project_dir = project_dir
        self.project_dir = project_dir

        # --------------------------------------------------
        # Reset GUI focus silently before broadcast
        # --------------------------------------------------
        self._current_room_id = None

        # --------------------------------------------------
        # Notify project-level observers
        # --------------------------------------------------
        self.project_changed.emit()

        # --------------------------------------------------
        # Deterministic room selection
        # --------------------------------------------------
        if self._project_state.rooms:
            first_room_id = next(iter(self._project_state.rooms))
            self.set_current_room(first_room_id)

    def request_adjacency_edit(self, surface_id: str) -> None:
        """
        GUI intent: user wants to edit adjacency for a surface.

        • Does NOT mutate ProjectState
        • Routed to MainWindow (overlay authority)
        """
        if not self.current_room_id:
            return

        self.adjacency_edit_requested.emit(surface_id)
    # ==================================================================
    # UVP focus (GUI-only intent)
    # ==================================================================

    def set_uvp_focus(self, surface_id: Optional[str]) -> None:
        self._uvp_surface_id = surface_id
        for cb in list(self._uvp_subscribers):
            cb(surface_id)

    def get_uvp_focus(self) -> Optional[str]:
        return self._uvp_surface_id

    def subscribe_uvp_focus(
        self,
        callback: Callable[[Optional[str]], None],
    ) -> None:
        self._uvp_subscribers.append(callback)

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

    def request_edit(self, kind: str, surface_id: str) -> None:
        if not self.current_room_id:
            return

        self.edit_requested.emit(kind, surface_id)

    def request_construction_u_value_change(self, cid: str, value: float):
        ps = self.project_state
        if not ps:
            return

        c = ps.constructions.get(cid)
        if not c:
            return

        c.u_value_W_m2K = float(value)

        ps.mark_heatloss_dirty()

        self.project_changed.emit()

    def request_assign_construction(self, surface_id: str, cid: str) -> None:
        ps = self.project_state
        if ps is None:
            return

        if cid not in ps.constructions:
            raise ValueError(f"Invalid construction: {cid}")

        ps.surface_construction_map[surface_id] = cid
        ps.mark_heatloss_dirty()

        self.notify_project_changed()