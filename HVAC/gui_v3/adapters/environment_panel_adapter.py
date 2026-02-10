# ======================================================================
# HVACgooee — Environment Panel Adapter (GUI v3)
# Phase: Phase F-A — Environment authority exposure
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel


class EnvironmentPanelAdapter:
    """
    Environment panel adapter (read-only).

    Phase F-A responsibilities:
    • Expose external design temperature
    • Expose calculation reference context
    • NO calculations
    • NO mutation
    """

    def __init__(
        self,
        *,
        panel: EnvironmentPanel,
        project_state: ProjectState,
    ) -> None:
        self._panel = panel
        self._ps = project_state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Refresh Environment panel from authoritative ProjectState.

        Phase F-A:
        • Read-only
        • No assumptions about internal storage
        """

        env = None

        # Canonical Project v3 access pattern
        if self._ps and hasattr(self._ps, "project_inputs"):
            env = getattr(self._ps.project_inputs, "environment", None)

        outside_c = (
            env.external_design_temperature_c
            if env and getattr(env, "external_design_temperature_c", None) is not None
            else None
        )

        self._panel.set_external_temperature(outside_c)

