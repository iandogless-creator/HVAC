# ======================================================================
# HVAC/gui_v3/context/gui_project_context.py
# ======================================================================

"""
HVACgooee — GUI Project Context

Phase: D.2 / I-J / K-A — Authority Boundary
Status: CANONICAL
"""

from __future__ import annotations

from pathlib import Path
import json
from typing import Callable, Optional, Literal

from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.project.project_state import ProjectState

HLPEditScope = Literal["geometry", "assumptions", "construction"]


class GuiProjectContext:
    """
    GUI-owned handle to authoritative ProjectState.

    GUI rules:
    - Does NOT define ProjectState
    - Does NOT mutate ProjectState
    - Does NOT calculate
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, *, project_state: ProjectState) -> None:
        self._project_state = project_state

        # GUI settings (installation scoped)
        settings_dir = Path.home() / ".hvacgooee" / "gui"
        settings_dir.mkdir(parents=True, exist_ok=True)
        self._gui_settings = GuiSettings(settings_dir=settings_dir)

        # --------------------------------------------------------------
        # GUI-only focus
        # --------------------------------------------------------------
        self.current_room_id: Optional[str] = None

        # --------------------------------------------------------------
        # HLPE session state (GUI-only)
        # --------------------------------------------------------------
        self.hlpe_active: bool = False
        self.hlpe_scope: Optional[HLPEditScope] = None
        self.hlpe_target_room_id: Optional[str] = None
        self.hlpe_target_surface_id: Optional[str] = None
        # --------------------------------------------------------------
        # Room selection observers (GUI-only)
        # --------------------------------------------------------------
        self._room_selection_listeners: list[Callable[[Optional[str]], None]] = []

        self._hlpe_listeners: list[Callable[[], None]] = []

        # Observer-only listeners
        self._construction_focus_listeners: list = []

    # ------------------------------------------------------------------
    # Read-only access
    # ------------------------------------------------------------------
    @property
    def project_state(self) -> ProjectState:
        return self._project_state

    @property
    def gui_settings(self) -> GuiSettings:
        return self._gui_settings

    # ------------------------------------------------------------------
    # Project switching (authoritative swap)
    # ------------------------------------------------------------------
    def set_project_state(self, project_state: ProjectState) -> None:
        """
        Replace authoritative ProjectState.

        GUI must refresh adapters after calling.
        """
        self._project_state = project_state

        # Reset GUI focus on project swap
        self.current_room_id = None

        # Clear edit session on project swap
        self.close_hlpe()

        # Notify listeners
        for cb in list(self._room_selection_listeners):
            cb(None)

    # ------------------------------------------------------------------
    # Project loading (Phase K-A)
    # ------------------------------------------------------------------
    def load_project(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        project_state = ProjectState.from_dict(payload)
        self.set_project_state(project_state)

    # ------------------------------------------------------------------
    # Room focus (GUI-only)
    # ------------------------------------------------------------------
    def set_current_room(self, room_id: Optional[str]) -> None:
        if room_id == self.current_room_id:
            return

        self.current_room_id = room_id

        # Room change invalidates HLPE (keep simple for v1)
        self.close_hlpe()

        for cb in list(self._room_selection_listeners):
            cb(room_id)

    def subscribe_room_selection_changed(
        self,
        callback: Callable[[Optional[str]], None],
    ) -> None:
        self._room_selection_listeners.append(callback)

    # ------------------------------------------------------------------
    # HLPE session control (GUI-only)
    # ------------------------------------------------------------------
    def open_hlpe(
        self,
        *,
        scope: HLPEditScope,
        room_id: str,
        surface_id: Optional[str] = None,
    ) -> None:
        self.hlpe_active = True
        self.hlpe_scope = scope
        self.hlpe_target_room_id = room_id
        self.hlpe_target_surface_id = surface_id
        self._notify_hlpe_changed()

    def close_hlpe(self) -> None:
        if not self.hlpe_active:
            return

        self.hlpe_active = False
        self.hlpe_scope = None
        self.hlpe_target_room_id = None
        self.hlpe_target_surface_id = None
        self._notify_hlpe_changed()

    def subscribe_hlpe_changed(self, callback: Callable[[], None]) -> None:
        self._hlpe_listeners.append(callback)

    def _notify_hlpe_changed(self) -> None:
        for cb in list(self._hlpe_listeners):
            cb()

    # ------------------------------------------------------------------
    # Construction focus (observer-only intent)
    # ------------------------------------------------------------------
    def focus_construction_element(
        self,
        *,
        room_id: str,
        element_id: str,
    ) -> None:
        for cb in self._construction_focus_listeners:
            cb(room_id=room_id, element_id=element_id)

    def subscribe_construction_focus(self, callback) -> None:
        self._construction_focus_listeners.append(callback)

    def make_bootstrap_project_state() -> ProjectState:
        room = RoomStateV1(
            room_id="room-001",
            name="Living Room",
            fabric_elements=(
                FabricElement(
                    element_id="wall-001",
                    name="External Wall",
                    area_m2=12.0,
                    u_value=0.35,
                    delta_t=20.0,
                ),
            ),
        )

        return ProjectState(
            rooms={room.room_id: room},
            heat_loss_valid=False,
            heat_loss_revision=0,
        )
