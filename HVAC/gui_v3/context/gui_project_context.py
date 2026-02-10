# ======================================================================
# HVAC/gui_v3/context/gui_project_context.py
# ======================================================================

"""
HVACgooee — GUI Project Context

Phase: D.2 — Authority Boundary
Status: CANONICAL

Purpose
-------
Provide the GUI with a stable, GUI-owned handle to an authoritative project
without exposing mutation paths into ProjectState.

This object is the ONLY project-level object GUI code may retain.
"""

from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.project.project_state import ProjectState


class GuiProjectContext:
    def __init__(self, *, project_state: ProjectState) -> None:
        # ------------------------------------------------------------------
        # Authoritative project state (opaque to GUI)
        # ------------------------------------------------------------------
        self._project_state = project_state

        # ------------------------------------------------------------------
        # GUI settings (user / installation scoped)
        # ------------------------------------------------------------------
        settings_dir = Path.home() / ".hvacgooee" / "gui"
        settings_dir.mkdir(parents=True, exist_ok=True)

        self._gui_settings = GuiSettings(settings_dir=settings_dir)

        # ------------------------------------------------------------------
        # Observer registries (UI-only)
        # ------------------------------------------------------------------
        self._construction_focus_listeners: list = []




    @property
    def gui_settings(self) -> GuiSettings:
        return self._gui_settings

    # --------------------------------------------------
    # Read-only access (adapters only)
    # --------------------------------------------------
    @property
    def project_state(self) -> ProjectState:
        return self._project_state

    # --------------------------------------------------
    # Phase D.2 — Project switching
    # --------------------------------------------------
    def set_project_state(self, project_state: ProjectState) -> None:
        """
        Replace authoritative project state.

        Used by:
        • File → New
        • File → Open

        GUI must refresh all adapters after calling this.
        """
        self._project_state = project_state

    # ------------------------------------------------------------------
    # Construction focus (observer-only)
    # ------------------------------------------------------------------

    def focus_construction_element(self, *, room_id: str, element_id: str) -> None:
        """
        Observer-only focus request.

        Emitted by Heat-Loss worksheet selection.
        Listened to by Construction adapter.
        """
        if not hasattr(self, "_construction_focus_listeners"):
            return

        for cb in self._construction_focus_listeners:
            cb(room_id=room_id, element_id=element_id)

    def subscribe_construction_focus(self, callback) -> None:
        """
        Register observer for construction focus intent.
        """
        if not hasattr(self, "_construction_focus_listeners"):
            self._construction_focus_listeners = []

        self._construction_focus_listeners.append(callback)
