# ======================================================================
# HVACgooee — Heat-Loss Panel Adapter (GUI v3)
# Phase: F-A — Environment → Heat-Loss Enrichment
# Status: OBSERVER (no execution authority)
# ======================================================================

from __future__ import annotations

from HVAC_legacy.heatloss.validation.heat_loss_execution_validator_v1 import (
    HeatLossExecutionValidatorV1,
    ValidationStatus,
)
from HVAC_legacy.project.project_state import ProjectState
from HVAC_legacy.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC_legacy.heatloss.validation.heat_loss_execution_validator_v1 import (
    HeatLossExecutionValidatorV1,
)
from HVAC_legacy.heatloss.validation.validation_dto import ValidationStatus


class HeatLossPanelAdapter:
    """
    Heat-Loss Panel Adapter (GUI v3)

    Responsibilities (Phase F-A):
    • Read ProjectState (read-only)
    • Run execution validation (read-only)
    • Reflect validation status textually
    • MUST NOT enable execution
    """

    def __init__(
        self,
        *,
        panel: HeatLossPanelV3,
        project_state: ProjectState,
    ) -> None:
        self._panel = panel
        self._ps = project_state

        # ------------------------------------------------------------------
        # Validator (read-only, stateless)
        # ------------------------------------------------------------------
        self._validator = HeatLossExecutionValidatorV1()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Refresh panel presentation from authoritative ProjectState.

        Phase F-A rules:
        • Validation may be run
        • Results may be displayed
        • Run button remains disabled
        """

        report = self._validator.validate(self._ps)

        self._update_status_from_validation(report)

        # Explicitly enforce Phase F-A rule
        self._panel.set_run_enabled(False)

    # ------------------------------------------------------------------
    # Presentation helpers (private)
    # ------------------------------------------------------------------
    def _update_status_from_validation(self, report) -> None:
        """
        Translate validation report into neutral, non-guiding UI text.
        """

        if report.status == ValidationStatus.PASS:
            self._panel.set_status_text(
                "Project is structurally ready for heat-loss execution "
                "(not yet calculated)."
            )
            return

        # FAIL case — summarise fatals only (warnings stay silent in F-A)
        fatal_count = len(report.fatal_issues)

        if fatal_count == 1:
            msg = "Heat-loss cannot run: 1 required input is missing."
        else:
            msg = f"Heat-loss cannot run: {fatal_count} required inputs are missing."

        self._panel.set_status_text(msg)
