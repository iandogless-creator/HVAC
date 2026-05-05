# ======================================================================
# HVAC/gui_v3/adapters/construction_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.panels.construction_panel import ConstructionPanel
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext


class ConstructionPanelAdapter:
    """
    GUI v3 — Construction Panel Adapter

    Responsibilities
    ----------------
    • Observe construction focus from GuiProjectContext
    • Read ProjectState.constructions
    • Project selected construction into ConstructionPanel

    Forbidden
    ---------
    • No ProjectState mutation
    • No U-value calculation
    • No topology mutation
    """

    def __init__(
        self,
        *,
        panel: ConstructionPanel,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        self._context.construction_focus_changed.connect(
            self._on_construction_focus_changed
        )

        self._panel.u_values_requested.connect(
            self._context.set_uvp_focus
        )

    def _on_construction_focus_changed(self, cid: str) -> None:
        ps = self._context.project_state
        if ps is None:
            return

        construction = ps.constructions.get(cid)
        if construction is None:
            self._panel.set_focused_construction(
                construction_id=cid,
                name=None,
                u_value_W_m2K=None,
                usage_count=0,
            )
            return

        mapping = getattr(ps, "surface_construction_map", {}) or {}

        usage_count = sum(
            1 for assigned_cid in mapping.values()
            if assigned_cid == cid
        )

        self._panel.set_focused_construction(
            construction_id=cid,
            name=construction.name,
            u_value_W_m2K=construction.u_value_W_m2K,
            usage_count=usage_count,
        )

    def refresh(self) -> None:
        cid = getattr(self._context, "current_construction_id", None)
        if cid:
            self._on_construction_focus_changed(cid)