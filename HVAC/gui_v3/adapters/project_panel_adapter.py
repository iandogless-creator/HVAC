# ======================================================================
# HVACgooee — Project Panel Adapter (GUI v3)
# ======================================================================

from __future__ import annotations

from typing import Optional

from HVAC.gui_v3.panels.project_panel import (
    ProjectPanel,
    ProjectSummaryViewModel,
)


class ProjectPanelAdapter:
    """
    Observer adapter for ProjectPanel.

    Responsibilities:
    • Read ProjectState
    • Build ProjectSummaryViewModel
    • Push it into ProjectPanel

    No authority.
    No persistence.
    No calculation.
    """

    def __init__(self, panel: ProjectPanel, project_state) -> None:
        self._panel = panel
        self._project_state = project_state

    # ------------------------------------------------------------------
    # Observer refresh
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        if self._project_state is None:
            self._panel.apply_view_model(None)
            return

        vm = ProjectSummaryViewModel(
            project_name=getattr(self._project_state, "name", None),
            project_reference=getattr(self._project_state, "reference", None),
            project_revision=getattr(self._project_state, "revision", None),
            heatloss_status=self._heatloss_status(),
            hydronics_status=self._hydronics_status(),
        )

        self._panel.apply_view_model(vm)

    # ------------------------------------------------------------------
    # Internal helpers (presentation only)
    # ------------------------------------------------------------------
    def _heatloss_status(self) -> Optional[str]:
        if not hasattr(self._project_state, "heat_loss_valid"):
            return "not run"
        return "valid" if self._project_state.heat_loss_valid else "not run"

    def _hydronics_status(self) -> Optional[str]:
        if not hasattr(self._project_state, "hydronics_valid"):
            return "not run"
        return "valid" if self._project_state.hydronics_valid else "not run"