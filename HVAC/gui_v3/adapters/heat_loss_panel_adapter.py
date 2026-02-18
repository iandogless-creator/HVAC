# ======================================================================
# HVAC/gui_v3/adapters/heat_loss_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3


class HeatLossPanelAdapter:
    """
    GUI v3 — Heat-Loss Panel Adapter

    Observer-only:
    • Reads ProjectState
    • Populates HeatLossPanelV3
    • Forwards run intent to controller
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        panel: HeatLossPanelV3,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        # GUI → controller intent
        self._panel.run_requested.connect(self._on_run_requested)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Refresh panel presentation from ProjectState.
        """
        ps = self._context.project_state
        panel = self._panel

        if ps is None:
            panel.set_rows([])
            panel.set_status_text("No project loaded")
            panel.set_run_enabled(False)
            return

        # Delegate row construction to worksheet adapter
        # (this adapter does not know row structure)
        panel.set_run_enabled(True)

    # ------------------------------------------------------------------
    # Intent forwarding
    # ------------------------------------------------------------------
    def _on_run_requested(self) -> None:
        """
        Forward run request to controller via context.
        """
        # MainWindow / controller already subscribed
        pass
