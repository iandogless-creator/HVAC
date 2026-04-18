# ======================================================================
# HVAC/gui_v3/adapters/heat_loss_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.core.value_resolution import (
    resolve_effective_ach,
    resolve_effective_internal_temp_C,
)
from HVAC.heatloss.fabric.row_builder_v1 import build_rows_with_meta
from HVAC.heatloss.validation.surface_edit_validator import SurfaceEditValidator


# ======================================================================
# HeatLossPanelAdapter
# ======================================================================

class HeatLossPanelAdapter:
    """
    Canonical adapter for Heat-Loss Panel projection.

    Authority
    ---------
    • Reads ProjectState
    • Builds worksheet rows via shared row builder
    • Overlays authoritative results when available
    • Computes live fallback totals when authoritative results are absent
    • Emits edit intent through GuiProjectContext
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
        self._validator = SurfaceEditValidator()

        self._context.room_state_changed.connect(self.refresh)
        self._context.current_room_changed.connect(self._on_current_room_changed)

        self._panel.run_requested.connect(self._on_run_requested)
        self._panel.cell_selected.connect(self._on_cell_selected)
        self._panel.adjacency_edit_requested.connect(
            self._on_adjacency_edit_requested
        )

    # ------------------------------------------------------------------
    # Public refresh
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        ps = self._context.project_state
        panel = self._panel

        if ps is None:
            panel.clear()
            panel.set_run_enabled(False)
            panel.set_heatloss_status(is_valid=False)
            return

        panel.set_heatloss_status(
            is_valid=bool(getattr(ps, "heatloss_valid", False))
        )

        room_id = self._context.current_room_id
        if not room_id:
            panel.clear()
            panel.set_run_enabled(False)
            return

        room = ps.rooms.get(room_id)
        if room is None:
            panel.clear()
            panel.set_run_enabled(False)
            return

        # --------------------------------------------------
        # Perimeter (derived — adapter only, NO state write)
        # --------------------------------------------------
        segs = [
            s for s in ps.boundary_segments.values()
            if s.owner_room_id == room_id
        ]

        external_perimeter_m = sum(
            s.length_m for s in segs if s.boundary_kind == "EXTERNAL"
        )

        inter_room_perimeter_m = sum(
            s.length_m for s in segs if s.boundary_kind == "INTER_ROOM"
        )

        gross_perimeter_m = external_perimeter_m + inter_room_perimeter_m

        # (DEV: visibility only — safe to remove later)
        print(
            f"[PERIM] gross={gross_perimeter_m:.2f} "
            f"ext={external_perimeter_m:.2f} "
            f"int={inter_room_perimeter_m:.2f}"
        )

        ti, _ = resolve_effective_internal_temp_C(ps, room)

        te = None
        if ps.environment is not None:
            te = getattr(ps.environment, "external_design_temp_C", None)

        panel.set_internal_temperature(ti)

        room_name = getattr(room, "name", room_id)
        panel.set_room_header(room_name, room_id)

        geometry = getattr(room, "geometry", None)
        if geometry is None:
            panel.set_geometry_summary(
                length_m=None,
                width_m=None,
                height_m=None,
            )
        else:
            panel.set_geometry_summary(
                length_m=getattr(geometry, "length_m", None),
                width_m=getattr(geometry, "width_m", None),
                height_m=getattr(geometry, "height_m", None),
            )

        ach, _ = resolve_effective_ach(ps, room)

        # --------------------------------------------------------------
        # Rows (single shared builder)
        # --------------------------------------------------------------
        rows, metas = build_rows_with_meta(ps, room)
        self._row_meta_by_surface = {
            m.surface_id: m for m in metas
        }
        rows = list(rows)

        rows = self._overlay_results_if_available(ps, rows)

        panel.set_rows(rows, metas)
        panel.set_row_meta_lookup(self._row_meta_by_surface)

        # --------------------------------------------------------------
        # Totals (authoritative OR live fallback)
        # --------------------------------------------------------------
        sum_qf = None
        qv = None
        qt = None

        if bool(getattr(ps, "heatloss_valid", False)):
            hl = getattr(ps, "heatloss_results", None)

            if isinstance(hl, dict):
                fabric = hl.get("fabric", {})
                ventilation = hl.get("ventilation", {})
                room_totals = hl.get("room_totals", {})

                sum_qf = fabric.get("qf_by_room_W", {}).get(room_id)
                qv = ventilation.get("qv_by_room_W", {}).get(room_id)
                qt = room_totals.get("qt_by_room_W", {}).get(room_id)

        if sum_qf is None:
            sum_qf = self._sum_qf_from_rows(rows)

        if qv is None:
            dt_room = None
            if ti is not None and te is not None:
                dt_room = ti - te
            qv = self._compute_qv_live(room, ach, dt_room)

        if qt is None:
            qt = (sum_qf or 0.0) + (qv or 0.0)

        panel.set_room_results(
            sum_qf=sum_qf,
            ach=ach,
            qv=qv,
            qt=qt,
        )

        panel.set_run_enabled(True)
    # ------------------------------------------------------------------
    # Live fallback helpers
    # ------------------------------------------------------------------
    def _compute_row_qf(self, row: dict) -> float | None:
        area = row.get("A")
        u_value = row.get("U")
        delta_t = row.get("dT")

        if area is None or u_value is None or delta_t is None:
            row["Qf"] = None
            return None

        qf = float(area) * float(u_value) * float(delta_t)
        row["Qf"] = qf
        return qf

    def _sum_qf_from_rows(self, rows: list[dict]) -> float:
        total = 0.0

        for row in rows:
            qf = row.get("Qf")
            if qf is None:
                qf = self._compute_row_qf(row)

            if qf is not None:
                total += float(qf)

        return total

    def _compute_qv_live(self, room, ach: float | None, dt: float | None) -> float:
        geometry = getattr(room, "geometry", None)
        if geometry is None or ach is None or dt is None:
            return 0.0

        length_m = getattr(geometry, "length_m", None)
        width_m = getattr(geometry, "width_m", None)
        height_m = getattr(geometry, "height_m", None)

        if length_m is None or width_m is None or height_m is None:
            return 0.0

        volume_m3 = float(length_m) * float(width_m) * float(height_m)
        return 0.33 * float(ach) * volume_m3 * float(dt)

    # ------------------------------------------------------------------
    # Result overlay
    # ------------------------------------------------------------------
    def _overlay_results_if_available(self, project, rows: list[dict]) -> list[dict]:
        if not getattr(project, "heatloss_valid", False):
            return rows

        hl = getattr(project, "heatloss_results", None)
        if not isinstance(hl, dict):
            return rows

        fabric = hl.get("fabric")
        if not isinstance(fabric, dict):
            return rows

        result_rows = fabric.get("rows")
        if not result_rows:
            return rows

        lookup = {
            getattr(result_row, "surface_id"): result_row
            for result_row in result_rows
            if getattr(result_row, "surface_id", None)
        }

        for row in rows:
            result_row = lookup.get(row.get("surface_id"))
            if result_row is None:
                continue

            if getattr(result_row, "u_value_W_m2K", None) is not None:
                row["U"] = float(result_row.u_value_W_m2K)

            if getattr(result_row, "delta_t_K", None) is not None:
                row["dT"] = float(result_row.delta_t_K)

            if getattr(result_row, "qf_W", None) is not None:
                row["Qf"] = float(result_row.qf_W)

        return rows

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    def _on_current_room_changed(self, _room_id) -> None:
        self.refresh()

    def _on_cell_selected(self, row_index: int) -> None:
        meta = self._panel.meta_for_row(row_index)
        if not meta:
            return

        surface_id = getattr(meta, "surface_id", None)
        if not surface_id:
            return

        self._context.request_edit("surface", surface_id)

    def _on_adjacency_edit_requested(self, surface_id: str) -> None:
        """
        Legacy-safe pass-through.

        If the context still exposes request_adjacency_edit(), use it.
        Otherwise do nothing here and let MainWindow / OverlayController
        own the active adjacency workflow.
        """
        if hasattr(self._context, "request_adjacency_edit"):
            self._context.request_adjacency_edit(surface_id)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
    def _on_run_requested(self) -> None:
        from HVAC.topology.topology_validator_v1 import TopologyValidatorV1
        from HVAC.heatloss.controller_v4_orchestrator import HeatLossControllerV4

        ps = self._context.project_state
        if ps is None:
            return

        errors: list[str] = []
        for room_id in ps.rooms:
            errors.extend(
                TopologyValidatorV1.validate_room_segments(ps, room_id)
            )

        if errors:
            self._apply_run_result(success=False, errors=errors)
            return

        room_id = self._context.current_room_id
        room = ps.rooms.get(room_id) if room_id else None
        if room is None:
            self._apply_run_result(success=False, errors=["No room selected"])
            return

        ti, _ = resolve_effective_internal_temp_C(ps, room)
        if ti is None:
            self._apply_run_result(
                success=False,
                errors=["Internal temperature is not defined."],
            )
            return

        ach, _ = resolve_effective_ach(ps, room)
        if ach is None:
            self._apply_run_result(
                success=False,
                errors=["ACH is not defined."],
            )
            return

        controller = HeatLossControllerV4(project_state=ps)
        controller.run(
            internal_design_temp_C=float(ti),
        )

        self._apply_run_result(success=True)

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    def _apply_run_result(self, *, success: bool, errors=None) -> None:
        if success:
            self._panel.set_ready()
        else:
            self._panel.set_not_ready(errors or ["Run failed"])

        self.refresh()