# ======================================================================
# HVAC/gui_v3/adapters/heat_loss_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.gui_v3.common.worksheet_row_meta import (
    WorksheetRowMeta,
    WorksheetCellMeta,
)

from HVAC.core.value_resolution import (
    resolve_effective_ach,
    resolve_effective_internal_temp_C,
)

from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1
from HVAC.heatloss.validation.surface_edit_validator import SurfaceEditValidator
from PySide6.QtCore import Signal

# ======================================================================
# HeatLossPanelAdapter
# ======================================================================

class HeatLossPanelAdapter:
    """
    Canonical adapter for Heat-Loss Panel projection.
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

        # ✅ NEW — adjacency click
        self._panel.adjacency_edit_requested.connect(
            self._on_adjacency_edit_requested
        )

    # ------------------------------------------------------------------
    # Adjacency helper (FIXED: instance method)
    # ------------------------------------------------------------------
    def _resolve_adjacent_temp(
        self,
        segment,
        project,
        environment,
    ) -> tuple[float | None, str]:

        if segment.boundary_kind != "INTER_ROOM":
            return None, ""

        adj_id = segment.adjacent_room_id

        if not adj_id:
            return None, "Unassigned"

        adj_room = project.rooms.get(adj_id)
        if not adj_room:
            return None, "Unassigned"

        ati = resolve_effective_internal_temp_C(adj_room, environment)

        return ati, f"{adj_room.name or adj_id}"

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
        from HVAC.core.value_resolution import resolve_effective_internal_temp_C

        ti, _ = resolve_effective_internal_temp_C(ps, room)

        te = None
        if ps.environment:
            te = getattr(ps.environment, "external_design_temp_C", None)

        dt = None
        if ti is not None and te is not None:
            dt = ti - te
        panel.set_internal_temperature(ti)  # 👈 push to UI
        # Header
        room_name = getattr(room, "name", room_id)
        panel.set_room_header(room_name, room_id)

        # Geometry
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

        # ACH
        ach, _ = resolve_effective_ach(ps, room)

        # Validation
        from HVAC.topology.topology_validator_v1 import TopologyValidatorV1

        validation = TopologyValidatorV1.validate_room_adjacency(ps, room_id)
        lookup = {v.surface_id: v for v in validation}

        # ------------------------------------------------------------------
        # Rows
        # ------------------------------------------------------------------

        rows, metas = self._build_rows_with_meta(ps, room, lookup)
        rows = self._overlay_results_if_available(ps, rows)

        # ------------------------------------------------------------------
        # Apply live ΔT to rows (FINAL authority)
        # ------------------------------------------------------------------

        if dt is not None:
            for r in rows:
                if r.get("element") in ("external_wall", "floor", "roof"):
                    r["dT"] = dt

        panel.set_rows(rows, metas)

        # ------------------------------------------------------------------
        # Totals (authoritative OR live fallback)
        # ------------------------------------------------------------------

        sum_qf = None
        qv = None
        qt = None

        hl_valid = bool(getattr(ps, "heatloss_valid", False))

        if hl_valid:
            hl = getattr(ps, "heatloss_results", None)

            if isinstance(hl, dict):
                fabric = hl.get("fabric", {})
                ventilation = hl.get("ventilation", {})
                room_totals = hl.get("room_totals", {})

                sum_qf = fabric.get("qf_by_room_W", {}).get(room_id)
                qv = ventilation.get("qv_by_room_W", {}).get(room_id)
                qt = room_totals.get("qt_by_room_W", {}).get(room_id)

        # ------------------------------------------------------------------
        # LIVE FALLBACK (no controller run)
        # ------------------------------------------------------------------

        if sum_qf is None:
            sum_qf = self._sum_qf_from_rows(rows)

        if qv is None:
            dt = None
            if ti is not None and ps.environment:
                te = getattr(ps.environment, "external_design_temp_C", None)
                if te is not None:
                    dt = ti - te

            qv = self._compute_qv_live(room, ach, dt)

        if qt is None:
            qt = (sum_qf or 0.0) + (qv or 0.0)
            hl = getattr(ps, "heatloss_results", None)

            if isinstance(hl, dict):
                fabric = hl.get("fabric", {})
                ventilation = hl.get("ventilation", {})
                room_totals = hl.get("room_totals", {})

                sum_qf = fabric.get("qf_by_room_W", {}).get(room_id)
                qv = ventilation.get("qv_by_room_W", {}).get(room_id)
                qt = room_totals.get("qt_by_room_W", {}).get(room_id)

        panel.set_room_results(
            sum_qf=sum_qf,
            ach=ach,
            qv=qv,
            qt=qt,
        )

        panel.set_run_enabled(True)

    # ------------------------------------------------------------------
    # LIVE FALLBACK — Qf aggregation + Qv + Qt
    # ------------------------------------------------------------------

    def _compute_row_qf(self, row: dict) -> float | None:
        A = row.get("A")
        U = row.get("U")
        dT = row.get("dT")

        if A is None or U is None or dT is None:
            return None

        return A * U * dT

    def _sum_qf_from_rows(self, rows: list[dict]) -> float:
        total = 0.0

        for r in rows:
            qf = r.get("Qf")

            if qf is None:
                qf = self._compute_row_qf(r)

            if qf is not None:
                total += qf

        return total

    def _compute_qv_live(self, room, ach: float, dt: float) -> float:
        if not room.geometry or ach is None or dt is None:
            return 0.0

        vol = (
                room.geometry.length_m
                * room.geometry.width_m
                * room.geometry.height_m
        )

        return 0.33 * ach * vol * dt
    # ------------------------------------------------------------------
    # Row builder
    # ------------------------------------------------------------------
    def _build_rows_with_meta(
        self,
        ps: Any,
        room: Any,
        lookup: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[WorksheetRowMeta]]:

        rows: list[dict[str, Any]] = []
        metas: list[WorksheetRowMeta] = []

        if room is None:
            return rows, metas

        source_rows = FabricFromSegmentsV1.build_rows_for_room(ps, room)

        for src in source_rows:
            rows.append(
                {
                    "surface_id": src.surface_id,
                    "element": src.element,
                    "A": src.area_m2,
                    "U": src.u_value_W_m2K,
                    "dT": None,
                    "Qf": src.qf_W,
                    "construction_id": src.construction_id,
                    "_segment": getattr(src, "boundary_segment", None),
                }
            )

        for row in rows:
            surface_id = row.get("surface_id")
            element = row.get("element")

            segment = row.get("_segment")

            ati = None
            adj_label = ""

            if segment and segment.boundary_kind == "INTER_ROOM":
                ati, adj_label = self._resolve_adjacent_temp(
                    segment,
                    ps,
                    ps.environment,
                )

            row["ati"] = ati
            row["adjacent_label"] = adj_label

            # --------------------------------------------------
            # Adjacency editable flag
            # --------------------------------------------------
            adjacency_editable = bool(
                segment and segment.boundary_kind == "INTER_ROOM"
            )

            # --------------------------------------------------
            # Validation state
            # --------------------------------------------------
            v = lookup.get(surface_id)

            if v is None:
                state = "GREEN"
                message = None
            elif v.severity == "ERROR":
                state = "RED"
                message = v.message
            elif v.severity == "WARNING":
                state = "ORANGE"
                message = v.message
            else:
                state = "GREEN"
                message = None

            if element == "internal_partition" and not adj_label:
                state = "ORANGE"
                message = "Waiting for adjacent room"

            # --------------------------------------------------
            # SINGLE meta object (correct)
            # --------------------------------------------------
            metas.append(
                WorksheetRowMeta(
                    surface_id=str(surface_id or ""),
                    element=str(element or ""),
                    state=state,
                    message=message,
                    adjacency_editable=adjacency_editable,  # ✅ correct placement
                    columns={
                        0: WorksheetCellMeta(field=None, editable=False, kind="readonly"),
                        1: WorksheetCellMeta(field="A", editable=True, kind="cell"),
                        2: WorksheetCellMeta(field="U", editable=True, kind="cell"),
                        3: WorksheetCellMeta(field=None, editable=False, kind="derived"),
                        4: WorksheetCellMeta(field=None, editable=False, kind="derived"),
                    },
                )
            )

        return rows, metas

    # ------------------------------------------------------------------
    # Result overlay
    # ------------------------------------------------------------------
    def _overlay_results_if_available(self, project, rows):
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
            getattr(r, "surface_id"): r
            for r in result_rows
            if getattr(r, "surface_id", None)
        }

        for row in rows:
            rr = lookup.get(row.get("surface_id"))
            if rr is None:
                continue

            if getattr(rr, "u_value_W_m2K", None) is not None:
                row["U"] = float(rr.u_value_W_m2K)

            if getattr(rr, "delta_t_K", None) is not None:
                row["dT"] = float(rr.delta_t_K)

            if getattr(rr, "qf_W", None) is not None:
                row["Qf"] = float(rr.qf_W)

        return rows

    # ------------------------------------------------------------------
    # ΣQf aggregator (display-only)
    # ------------------------------------------------------------------

    def _sum_qf(self, rows: list[dict]) -> float:
        total = 0.0

        for r in rows:
            qf = r.get("Qf")
            if qf is not None:
                total += qf

        return total
    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    def _on_current_room_changed(self, _room_id):
        self.refresh()

    def _on_cell_selected(self, row_index: int):
        meta = self._panel.meta_for_row(row_index)
        if not meta:
            return

        self._context.request_edit("surface", meta.surface_id)

    def _on_adjacency_edit_requested(self, surface_id: str):
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

        env = getattr(ps, "environment", None)
        ti = getattr(env, "default_internal_temp_C", None) if env else None

        if ti is None:
            self._apply_run_result(False, ["Default internal temperature missing"])
            return

        room_id = self._context.current_room_id
        room = ps.rooms.get(room_id) if room_id else None
        ach, _ = resolve_effective_ach(ps, room)

        if ach is None:
            self._apply_run_result(False, ["ACH is not defined."])
            return

        controller = HeatLossControllerV4(project_state=ps)

        controller.run(
            internal_design_temp_C=float(ti),
            ach=float(ach),
        )

        self._apply_run_result(success=True)

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    def _apply_run_result(self, *, success: bool, errors=None):
        if success:
            self._panel.set_ready()
        else:
            self._panel.set_not_ready(errors or ["Run failed"])

        self.refresh()