# ======================================================================
# HVAC/gui_v3/adapters/heat_loss_worksheet_adapter.py
# ======================================================================
# HVACgooee — Heat-Loss Worksheet Adapter (GUI v3)
# Phase: F — Worksheet Population (Observer-Only)
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from typing import Any, List

from HVAC_legacy.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC_legacy.gui_v3.panels.heat_loss_panel import (
    HeatLossPanelV3,
    HeatLossWorksheetRow,
)


class HeatLossWorksheetAdapter:
    """
    Observer-only adapter responsible for populating
    Heat-Loss worksheet rows.

    Responsibilities (LOCKED):
    • Read ProjectState
    • Build HeatLossWorksheetRow
    • Populate panel table
    • NEVER calculate
    • NEVER mutate ProjectState
    • NEVER execute
    """

    def __init__(
        self,
        *,
        panel: HeatLossPanelV3,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        self.refresh()

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self._refresh_rows()

    # ------------------------------------------------------------------
    # Row population
    # ------------------------------------------------------------------
    def _refresh_rows(self) -> None:
        ps = self._resolve_project_state()
        if ps is None:
            self._panel.set_rows([])
            return

        room_id = getattr(ps, "active_room_id", None)
        if not room_id:
            self._panel.set_rows([])
            return

        room = ps.rooms.get(room_id)
        if room is None:
            self._panel.set_rows([])
            return

        rows: List[HeatLossWorksheetRow] = []

        # ----------------------------------------------
        # Iterate room elements (fabric + openings)
        # ----------------------------------------------
        for element in getattr(room, "elements", []):
            overrides = (
                getattr(ps, "heatloss_overrides", {})
                .get(room_id, {})
                .get(element.element_id, {})
            )

            result = (
                getattr(ps.heatloss, "elements", {})
                .get((room_id, element.element_id))
            )

            rows.append(
                HeatLossWorksheetRow(
                    room_id=room_id,
                    element_id=element.element_id,
                    element_name=element.name,
                    element_kind=element.kind,

                    # Derived preview (pre-run)
                    derived_area_m2=element.area_m2,
                    derived_delta_t_k=element.delta_t_k,
                    derived_u_value_w_m2k=element.u_value_w_m2k,

                    # Results substrate (post-run)
                    result_area_m2=getattr(result, "area_m2", None),
                    result_delta_t_k=getattr(result, "delta_t_k", None),
                    result_u_value_w_m2k=getattr(result, "u_value_w_m2k", None),
                    result_loss_w=getattr(result, "loss_w", None),

                    # Worksheet overrides (intent only)
                    override_area_m2=overrides.get("area_m2"),
                    override_delta_t_k=overrides.get("delta_t_k"),
                    override_u_value_w_m2k=overrides.get("u_value_w_m2k"),
                )
            )

        self._panel.set_rows(rows)

    # ------------------------------------------------------------------
    # Resolution helper
    # ------------------------------------------------------------------
    def _resolve_project_state(self) -> Any:
        ps = getattr(self._context, "project_state", None)
        if ps is None:
            return None

        inner = getattr(ps, "project_state", None)
        return inner if inner is not None else ps
