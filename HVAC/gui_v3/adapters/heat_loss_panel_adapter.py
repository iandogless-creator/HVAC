# ======================================================================
# HVAC/gui_v3/adapters/heat_loss_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Dict, Any, List

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3

from HVAC.core.value_resolution import (
    resolve_effective_internal_temp_C,
    resolve_effective_height_m,
    resolve_effective_ach,
)

from HVAC.heatloss.fabric.fabric_from_segments_v1 import (
    FabricFromSegmentsV1,
)


class HeatLossPanelAdapter:
    """
    Adapter responsible for exposing read-only heat-loss context
    to the Heat-Loss Panel.

    Authority rules
    ---------------
    • Reads ProjectState only
    • Performs display resolution only
    • Does not mutate ProjectState
    • Does not run engines
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

        self._context.room_state_changed.connect(self.refresh)
        self._context.current_room_changed.connect(lambda _: self.refresh())
        self._panel.run_requested.connect(self._on_run_requested)

    # ------------------------------------------------------------------
    # Public refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:

        ps = self._context.project_state
        panel = self._panel

        if ps is None:
            panel.set_rows([])
            panel.set_run_enabled(False)
            panel.set_header_context(None)
            return

        room_id = self._context.current_room_id

        if not room_id:
            panel.set_rows([])
            panel.set_header_context(None)
            return

        room = ps.rooms.get(room_id)
        if room is None:
            panel.set_rows([])
            panel.set_header_context(None)
            return

        # --------------------------------------------------
        # Resolve effective values
        # --------------------------------------------------

        ti_C, ti_source = resolve_effective_internal_temp_C(ps, room)
        height_m, height_source = resolve_effective_height_m(ps, room)
        ach, ach_source = resolve_effective_ach(ps, room)

        te_C = (
            ps.environment.external_design_temp_C
            if ps.environment is not None
            else None
        )

        # --------------------------------------------------
        # Build rows from topology → fabric
        # --------------------------------------------------

        rows = self._build_rows(ps, room)

        # --------------------------------------------------
        # Overlay calculated results (if available)
        # --------------------------------------------------

        rows = self._overlay_results_if_available(ps, room_id, rows)

        # Guard: room changed during refresh
        if self._context.current_room_id != room_id:
            return

        # --------------------------------------------------
        # Push to panel
        # --------------------------------------------------

        panel.set_rows(rows)

        panel.set_header_context({
            "room_name": room.name,
            "ti_C": ti_C,
            "ti_source": ti_source,
            "height_m": height_m,
            "height_source": height_source,
            "ach": ach,
            "ach_source": ach_source,
        })

        panel.set_run_enabled(True)

    # ------------------------------------------------------------------
    # Row builder (Topology → Fabric)
    # ------------------------------------------------------------------

    def _build_rows(
        self,
        ps,
        room,
    ) -> List[Dict[str, Any]]:

        rows: List[Dict[str, Any]] = []

        fabric_rows = FabricFromSegmentsV1.build_rows_for_room(ps, room)

        for r in fabric_rows:
            rows.append({
                "surface_id": r.surface_id,
                "element": r.element,
                "A": float(r.area_m2) if r.area_m2 is not None else None,
                "U": float(r.u_value_W_m2K) if r.u_value_W_m2K is not None else None,
                "dT": float(r.delta_t_K) if r.delta_t_K is not None else None,
                "Qf": float(r.qf_W) if r.qf_W is not None else None,
                "construction_id": r.construction_id,
            })

        return rows

    # ------------------------------------------------------------------
    # Result overlay
    # ------------------------------------------------------------------

    def _overlay_results_if_available(
        self,
        project,
        room_id: str,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        if not getattr(project, "heatloss_valid", False):
            return rows

        hl = getattr(project, "heatloss_results", None)
        if not hl:
            return rows

        fabric = hl.get("fabric")
        if fabric is None:
            return rows

        result_rows = getattr(fabric, "rows", None)
        if not result_rows:
            return rows

        lookup: Dict[str, Any] = {
            getattr(r, "surface_id"): r
            for r in result_rows
            if getattr(r, "surface_id", None)
        }

        for row in rows:
            sid = row.get("surface_id")
            r = lookup.get(sid)

            if not r:
                continue

            if getattr(r, "u_value_W_m2K", None) is not None:
                row["U"] = float(r.u_value_W_m2K)

            if getattr(r, "delta_t_K", None) is not None:
                row["dT"] = float(r.delta_t_K)

            if getattr(r, "qf_W", None) is not None:
                row["Qf"] = float(r.qf_W)

        return rows

    # ------------------------------------------------------------------
    # Intent forwarding
    # ------------------------------------------------------------------

    def _on_run_requested(self) -> None:
        """
        Forward run request to controller layer.
        """
        pass