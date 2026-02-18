# ======================================================================
# HVAC/gui_v3/adapters/heat_loss_worksheet_adapter.py
# ======================================================================
# HVACgooee — Heat-Loss Worksheet Adapter (GUI v3)
# Phase: F — Worksheet Population (Observer-Only)
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from typing import Any, List

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.gui_v3.dto.heat_loss_worksheet_row_dto import HeatLossWorksheetRowDTO
from HVAC.gui_v3.dev.heat_loss_dev_rows import build_dev_rows


class HeatLossWorksheetAdapter:
    """
    Observer-only adapter responsible for populating
    Heat-Loss worksheet rows.

    LOCKED RESPONSIBILITIES
    ----------------------
    • Read ProjectState (never mutate)
    • Build HeatLossWorksheetRowDTO
    • Populate worksheet table
    • NEVER calculate
    • NEVER execute engines
    """

    def __init__(
        self,
        *,
        panel: HeatLossPanelV3,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        # Context → worksheet refresh (non-positional)
        self._context.subscribe_room_selection_changed(
            lambda _: self.refresh()
        )

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
        room_id = self._context.current_room_id

        if not ps or not room_id:
            self._panel.set_rows([])
            return

        room = ps.rooms.get(room_id)
        if room is None:
            self._panel.set_rows([])
            return

        rows: List[HeatLossWorksheetRowDTO] = []

        # --------------------------------------------------
        # Authoritative elements (future engine path)
        # --------------------------------------------------
        for element in getattr(room, "elements", []):
            rows.append(
                HeatLossWorksheetRowDTO(
                    room_id=room_id,
                    element_id=element.element_id,
                    element_name=element.name,
                    area_m2=element.area_m2,
                    delta_t_k=element.delta_t_k,
                    u_value_w_m2k=element.u_value_w_m2k,
                    qf_w=None,
                )
            )

        # --------------------------------------------------
        # DEV fallback — visible worksheet until engine exists
        # --------------------------------------------------
        if not rows:
            rows = build_dev_rows(room_id=room_id)

        self._panel.set_rows(rows)

    # ------------------------------------------------------------------
    # Resolution helper
    # ------------------------------------------------------------------
    def _resolve_project_state(self) -> Any:
        ps = getattr(self._context, "project_state", None)
        if ps is None:
            return None

        # Guard for wrapped ProjectState (legacy loaders)
        inner = getattr(ps, "project_state", None)
        return inner if inner is not None else ps
