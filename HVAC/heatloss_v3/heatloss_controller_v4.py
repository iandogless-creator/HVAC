# ======================================================================
# HVAC/heatloss_v3/heatloss_controller_v4.py
# ======================================================================
# HVACgooee — HeatLossControllerV4
# Phase: I / J — Authoritative Execution
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from typing import Dict

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext


class HeatLossControllerV4:
    """
    Authoritative heat-loss execution (minimal Phase I/J).

    Responsibilities
    ----------------
    • Resolve current ProjectState from GuiProjectContext
    • Compute steady-state fabric losses
    • Commit results to ps.heatloss.room_results

    Explicitly NOT responsible for:
    • GUI state
    • Readiness heuristics
    • Overrides persistence
    • Presentation formatting
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, *, gui_context: GuiProjectContext) -> None:
        self._context = gui_context

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_project(self) -> None:
        ps = self._context.project_state
        if ps is None:
            return

        results = {
            "room_results": {},
            "total_loss_w": 0.0,
        }

        Te = ps.environment.external_design_temperature

        for room_id, room in ps.rooms.items():
            Ti = room.get("internal_design_temperature")
            if Ti is None:
                continue

            dt_ext = Ti - Te

            L = room.get("length_m")
            W = room.get("width_m")
            H = room.get("height_m")
            ACH = room.get("air_change_rate")

            if None in (L, W, H, ACH):
                continue

            volume = L * W * H

            room_qf = 0.0
            row_results = []

            for surface_id, s in room.get("surfaces", {}).items():
                area = s.area_m2
                U = s.u_value_w_m2k
                if area is None or U is None:
                    continue

                if s.kind == "ext":
                    dt = dt_ext
                else:
                    dt = s.delta_t_override_k or 0.0

                qf = area * U * dt
                room_qf += qf

                row_results.append({
                    "surface_id": surface_id,
                    "area": area,
                    "delta_t": dt,
                    "u_value": U,
                    "loss_w": qf,
                })

            Qv = 0.33 * ACH * volume * dt_ext
            Qt = room_qf + Qv

            results["room_results"][room_id] = {
                "rows": row_results,
                "sum_qf": room_qf,
                "qv": Qv,
                "qt": Qt,
                "volume": volume,
            }

            results["total_loss_w"] += Qt

        ps.heatloss_results = results
