# ======================================================================
# HVAC/gui_v3/adapters/project_heatloss_readiness_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Iterable

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3


class ProjectHeatLossReadinessAdapter:
    """
    GUI v3 — Project Heat-Loss Readiness Adapter

    Phase F-B — Readiness rules (presentation only)

    Responsibilities
    ----------------
    • Pull readiness state from controller / ProjectState
    • Present readiness + blocking reasons to HeatLossPanel
    • Never infer, calculate, or decide readiness

    Explicitly forbidden
    --------------------
    • Computing readiness
    • Guessing missing requirements
    • Clearing or mutating ProjectState
    """

    def __init__(
        self,
        *,
        panel: HeatLossPanelV3,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Pull readiness state and present it.

        Readiness contract (Phase F-B)
        --------------------------------
        Controller must expose:
            is_ready: bool
            blocking_reasons: Iterable[str]
        """
        ps = self._context.project_state

        # --------------------------------------------------
        # No project loaded
        # --------------------------------------------------
        if not ps:
            self._panel.set_not_ready(
                reasons=["No project loaded"]
            )
            return

        readiness = getattr(ps, "heatloss_readiness", None)

        # --------------------------------------------------
        # No readiness information yet
        # --------------------------------------------------
        if readiness is None:
            self._panel.set_not_ready(
                reasons=["Heat-loss readiness not evaluated"]
            )
            return

        is_ready = bool(getattr(readiness, "is_ready", False))
        reasons: Iterable[str] = getattr(readiness, "blocking_reasons", [])

        # --------------------------------------------------
        # Present state (no logic here)
        # --------------------------------------------------
        if is_ready:
            self._panel.set_ready()
        else:
            self._panel.set_not_ready(
                reasons=list(reasons)
            )
