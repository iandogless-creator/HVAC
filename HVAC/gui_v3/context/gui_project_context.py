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

from HVAC_legacy.gui_v3.context.gui_settings import GuiSettings
from HVAC_legacy.project.project_state import ProjectState


class GuiProjectContext:
    """
    GUI-facing project context.

    Authority Rules
    ---------------
    • Wraps exactly one authoritative ProjectState
    • GUI code must never mutate ProjectState
    • Adapters may READ project_state
    • ProjectState replacement is explicit (New / Open)
    """

    def __init__(self, *, project_state: ProjectState) -> None:
        self._project_state: ProjectState = project_state

        # GUI-only persistence (Phase F+)
        self.gui_settings = GuiSettings(
            settings_dir=Path.home() / ".hvacgooee"
        )

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
