# ======================================================================
# HVACgooee — Project Panel Adapter (GUI v3)
# Phase: E-C — Lifecycle Status Wiring
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState

from HVAC.gui_v3.panels.project_panel import (
    ProjectPanel,
    ProjectSummaryViewModel,
)


class ProjectPanelAdapter:
    """
    One-way adapter:
    ProjectState → ProjectSummaryViewModel → ProjectPanel

    Responsibilities
    ----------------
    • Read authoritative ProjectState
    • Translate lifecycle flags into display text
    • Push a read-only ViewModel into ProjectPanel

    Constraints (LOCKED)
    --------------------
    • No calculations
    • No inference
    • No mutation
    • No defaults invented
    • No GUI-side state
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        panel: ProjectPanel,
        project_state: ProjectState,
    ) -> None:
        self._panel = panel
        self._ps = project_state

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Refresh Project panel from HVAC.project.
State.

        Phase E rules:
        • Read-only
        • Deterministic
        • Presentation only
        """
        vm = self._build_view_model()
        self._panel.apply_view_model(vm)

    # ------------------------------------------------------------------
    # ViewModel assembly
    # ------------------------------------------------------------------
    def _build_view_model(self) -> ProjectSummaryViewModel:
        ps = self._ps

        heatloss_status = (
            "run" if getattr(ps, "heatloss_has_run", False) else "not run"
        )

        hydronics_status = (
            "run" if getattr(ps, "hydronics_has_run", False) else "not run"
        )

        return ProjectSummaryViewModel(
            project_name=getattr(ps, "project_name", None),
            project_reference=getattr(ps, "project_reference", None),
            project_revision=getattr(ps, "project_revision", None),
            heatloss_status=heatloss_status,
            hydronics_status=hydronics_status,
        )
