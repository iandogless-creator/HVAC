# ======================================================================
# HVAC/gui_v3/adapters/heat_loss_worksheet_adapter.py
# ======================================================================
# HVACgooee — Heat-Loss Worksheet Adapter (GUI v3)
# Phase: F — Worksheet Population (Observer-Only)
# Status: CANONICAL (Room-level aggregates separated)
# ======================================================================

from __future__ import annotations

from typing import Any, List
from PySide6.QtWidgets import (
    QLabel,
    QFrame,
    QGridLayout,
    QDoubleSpinBox,
)
from PySide6.QtWidgets import QFrame, QGridLayout
from PySide6.QtCore import Qt
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.gui_v3.dto.heat_loss_worksheet_row_dto import HeatLossWorksheetRowDTO
from HVAC.gui_v3.dev.heat_loss_dev_rows import build_dev_rows


class HeatLossWorksheetAdapter:
    """
    Observer-only adapter responsible for populating the Heat-Loss worksheet.

    LOCKED RESPONSIBILITIES
    ----------------------
    • Read ProjectState (never mutate)
    • Build HeatLossWorksheetRowDTO
    • Populate worksheet rows (surface level only)
    • Populate room-level result block (ΣQf, Qv, Qt)
    • Maintain row → surface mapping
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

        # Row index → surface_id mapping (GUI-only)
        self._row_surface_ids: dict[int, str] = {}

        # Context → worksheet refresh
        self._context.current_room_changed.connect(lambda _: self.refresh())

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self._row_surface_ids.clear()
        self._refresh_rows()

    # ------------------------------------------------------------------
    # Main refresh
    # ------------------------------------------------------------------
    def _refresh_rows(self) -> None:
        ps = self._resolve_project_state()
        room_id = self._context.current_room_id

        if not ps or not room_id:
            self._panel.set_rows([])
            self._panel.set_room_results(sum_qf=None, qv=None, qt=None)
            return

        # --------------------------------------------------
        # AUTHORITATIVE RESULT PATH (Valid execution)
        # --------------------------------------------------
        if getattr(ps, "heatloss_valid", False):

            container = getattr(ps, "heatloss_results", None)
            if not isinstance(container, dict):
                self._panel.set_rows([])
                self._panel.set_room_results(sum_qf=None, qv=None, qt=None)
                return

            fabric = container.get("fabric")
            if not isinstance(fabric, dict):
                self._panel.set_rows([])
                self._panel.set_room_results(sum_qf=None, qv=None, qt=None)
                return

            # ---- Surface rows (room-filtered) ----
            rows: List[HeatLossWorksheetRowDTO] = []

            for r in fabric.get("rows", []):
                if not isinstance(r, dict):
                    continue
                if r.get("room_id") != room_id:
                    continue

                rows.append(
                    HeatLossWorksheetRowDTO(
                        room_id=room_id,
                        element_id=r.get("surface_id"),
                        element_name=r.get("surface_class"),
                        area_m2=r.get("area_m2"),
                        delta_t_k=r.get("delta_t_K"),
                        u_value_w_m2k=r.get("u_value_W_m2K"),
                        qf_w=r.get("qf_W"),
                    )
                )

            self._panel.set_rows(rows)

            # ---- Room aggregates (NO CALCULATION HERE) ----
            sum_qf_room: float | None = None
            qv_room: float | None = None
            qt_room: float | None = None

            # ΣQf
            qf_by_room = fabric.get("qf_by_room_W")
            if isinstance(qf_by_room, dict):
                sum_qf_room = qf_by_room.get(room_id)

            if sum_qf_room is None:
                total_by_room = fabric.get("total_by_room_W")
                if isinstance(total_by_room, dict):
                    sum_qf_room = total_by_room.get(room_id)

            # Qv
            ventilation = container.get("ventilation")
            if isinstance(ventilation, dict):
                qv_by_room = ventilation.get("qv_by_room_W")
                if isinstance(qv_by_room, dict):
                    qv_room = qv_by_room.get(room_id)

            # Qt
            room_totals = container.get("room_totals")
            if isinstance(room_totals, dict):
                qt_by_room = room_totals.get("qt_by_room_W")
                if isinstance(qt_by_room, dict):
                    qt_room = qt_by_room.get(room_id)

            self._panel.set_room_results(
                sum_qf=sum_qf_room,
                qv=qv_room,
                qt=qt_room,
            )

            # ---- Row mapping (for navigation only) ----
            self._row_surface_ids.clear()
            for row_index, row in enumerate(rows):
                if row.element_id:
                    self._row_surface_ids[row_index] = row.element_id

            return

        # --------------------------------------------------
        # STRUCTURAL PREVIEW (Pre-execution)
        # --------------------------------------------------
        room = ps.rooms.get(room_id)
        if room is None:
            self._panel.set_rows([])
            self._panel.set_room_results(sum_qf=None, qv=None, qt=None)
            return

        rows: List[HeatLossWorksheetRowDTO] = []

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

        self._panel.set_rows(rows)
        self._panel.set_room_results(sum_qf=None, qv=None, qt=None)

        self._row_surface_ids.clear()
        for row_index, row in enumerate(rows):
            if row.element_id:
                self._row_surface_ids[row_index] = row.element_id

    # ------------------------------------------------------------------
    # Row lookup (for navigation)
    # ------------------------------------------------------------------
    def surface_id_for_row(self, row_index: int) -> str | None:
        return self._row_surface_ids.get(row_index)

    # ------------------------------------------------------------------
    # Resolution helper
    # ------------------------------------------------------------------
    def _resolve_project_state(self) -> Any:
        ps = getattr(self._context, "project_state", None)
        if ps is None:
            return None

        inner = getattr(ps, "project_state", None)
        return inner if inner is not None else ps