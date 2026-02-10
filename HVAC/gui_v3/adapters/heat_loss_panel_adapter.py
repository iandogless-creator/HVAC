# ======================================================================
# HVACgooee — Heat-Loss Panel Adapter (GUI v3)
# Phase: F-E — Worksheet → Construction focus (observer-only)
# Status: OBSERVER (no execution authority)
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import QItemSelection, QModelIndex

from HVAC.project.project_state import ProjectState
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3, HeatLossWorksheetRow
from HVAC.heatloss.validation.heat_loss_execution_validator_v1 import (
    HeatLossExecutionValidatorV1,
)
from HVAC.heatloss.validation.validation_dto import ValidationStatus


class HeatLossPanelAdapter:
    def __init__(
        self,
        *,
        panel: HeatLossPanelV3,
        project_state: ProjectState,
        gui_context,  # GuiProjectContext (observer-only)
    ) -> None:
        self._panel = panel
        self._ps = project_state
        self._context = gui_context

        self._validator = HeatLossExecutionValidatorV1()

        # --------------------------------------------------------------
        # Phase F-E — worksheet selection awareness (observer-only)
        # --------------------------------------------------------------
        self._panel._table.selectionModel().selectionChanged.connect(
            self._on_worksheet_selection_changed
        )


    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Phase F-E rules:
        • Intent visible
        • Validation visible
        • Selection awareness active
        • No calculations
        • Run disabled
        """

        self._update_intent_fields()

        report = self._validator.validate(self._ps)
        self._update_status_from_validation(report)

        self._panel.set_run_enabled(False)

    # ------------------------------------------------------------------
    # Intent presentation (Phase F-B)
    # ------------------------------------------------------------------
    def _update_intent_fields(self) -> None:
        # ---- Method (declared intent only)
        method = getattr(self._ps.heatloss, "method", None)

        self._panel.set_method_text(str(method) if method else "—")

        # ---- Reference ΔT (environment-derived, non-authoritative)
        env = getattr(self._ps, "environment", None)

        if env:
            ti = getattr(env, "internal_design_temperature", None)
            te = getattr(env, "external_design_temperature", None)
        else:
            ti = te = None

        if ti is not None and te is not None:
            self._panel.set_delta_t_text(f"{ti - te:.1f} K (reference)")
        else:
            self._panel.set_delta_t_text("—")

    # ------------------------------------------------------------------
    # Validation presentation
    # ------------------------------------------------------------------
    def _update_status_from_validation(self, report) -> None:
        if report.status == ValidationStatus.PASS:
            self._panel.set_status_text(
                "Project is structurally ready for heat-loss execution "
                "(not yet calculated)."
            )
            return

        n = len(report.fatal_issues)
        msg = (
            "Heat-loss cannot run: 1 required input is missing."
            if n == 1
            else f"Heat-loss cannot run: {n} required inputs are missing."
        )
        self._panel.set_status_text(msg)

    # ------------------------------------------------------------------
    # Phase F-E — worksheet selection handling
    # ------------------------------------------------------------------
    def _on_worksheet_selection_changed(
            self,
            selected: QItemSelection,
            deselected: QItemSelection,
    ) -> None:
        """
        Observer-only reaction to worksheet row selection.

        Emits construction-focus intent via GUI context.
        """

        if not selected.indexes():
            return

        index: QModelIndex = selected.indexes()[0]
        model = self._panel._model

        if index.row() >= len(model._rows):
            return

        row: HeatLossWorksheetRow = model._rows[index.row()]

        # --------------------------------------------------------------
        # Emit observer-only focus intent
        # --------------------------------------------------------------
        self._context.focus_construction_element(
            room_id=row.room_id,
            element_id=row.element_id,
        )

