# ======================================================================
# HVAC/gui_v3/adapters/project_heatloss_readiness_adapter.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3


@dataclass(frozen=True, slots=True)
class ReadinessView:
    ok: bool
    reasons: List[str]
    show_fix_uvalues: bool


class ProjectHeatLossReadinessAdapter:
    """
    Phase II-B — Heat-loss readiness presentation adapter (CANONICAL)

    LOCKED RULES
    ------------
    • Reads ProjectState only (never mutate)
    • Uses ProjectState.evaluate_heatloss_readiness() only
    • Readiness is a concrete domain object
    • No dicts, no heuristics, no inference
    """

    def __init__(self, *, panel: HeatLossPanelV3, context: GuiProjectContext) -> None:
        self._panel = panel
        self._context = context

        if hasattr(self._context, "current_room_changed"):
            self._context.current_room_changed.connect(lambda _rid: self.refresh())

        self.refresh()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        ps = getattr(self._context, "project_state", None)
        if ps is None:
            self._apply(
                ReadinessView(
                    ok=False,
                    reasons=["No project loaded"],
                    show_fix_uvalues=False,
                )
            )
            return

        readiness = ps.evaluate_heatloss_readiness()

        # ---- Canonical DTO access (LOCKED) ----------------------------
        ok = readiness.is_ready
        reasons = list(readiness.blocking_reasons)

        show_fix = any(
            "u-value" in r.lower() or "u value" in r.lower() or "u-values" in r.lower()
            for r in reasons
        )

        self._apply(ReadinessView(ok=ok, reasons=reasons, show_fix_uvalues=show_fix))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _apply(self, view: ReadinessView) -> None:
        # Run gating
        self._panel.set_run_enabled(view.ok)

        # Readiness presentation
        if view.ok:
            self._panel.set_ready()
        else:
            self._panel.set_not_ready(view.reasons)

        # Optional fix action (Phase II-A contract)
        if hasattr(self._panel, "show_fix_uvalues_action"):
            self._panel.show_fix_uvalues_action(view.show_fix_uvalues)