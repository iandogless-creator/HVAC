# ======================================================================
# HVACgooee — Environment Panel Adapter (GUI v3)
# Phase: Phase F-A — Environment authority exposure
# Status: CANONICAL
# ======================================================================

# ======================================================================
# HVACgooee — Environment Panel Adapter (GUI v3)
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel


class EnvironmentPanelAdapter:
    """
    Observer adapter for EnvironmentPanel.

    Responsibilities:
    • Read ProjectState
    • Present environment data
    • No authority, no mutation
    """

    def __init__(self, panel: EnvironmentPanel, project_state) -> None:
        self._panel = panel
        self._project_state = project_state

    # ------------------------------------------------------------------
    # Observer refresh
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        ps = self._project_state
        if ps is None:
            return

        # External design temperature
        te = getattr(ps, "external_design_temperature", None)
        if hasattr(self._panel, "set_external_temperature"):
            self._panel.set_external_temperature(te)

        # Reference ΔT
        dt = getattr(ps, "reference_delta_t", None)
        if hasattr(self._panel, "set_reference_delta_t"):
            self._panel.set_reference_delta_t(dt)

        # Method / metadata (optional)
        method = getattr(ps, "heatloss_method", None)
        if hasattr(self._panel, "set_method"):
            self._panel.set_method(method)

    def _on_external_design_temp_changed(self, te_c: float) -> None:
        """
        Forward user-entered external design temperature (Te)
        into the heat-loss run intent context.
        """
        self._gui_context.heatloss_run_context.external_design_temp_C = te_c

    # HVAC/gui_v3/adapters/environment_panel_adapter.py

    def set_external_design_temperature(self, value: float) -> None:
        ps = self._context.project_state
        if ps is None or ps.environment is None:
            return

        ps.environment.external_design_temperature = value

        # Phase I-B
        ps.mark_heatloss_dirty()

