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
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from HVAC.fabric.generate_fabric_from_topology import (
    generate_fabric_from_topology,
)
from HVAC.gui_v3.common.worksheet_row_meta import (
    WorksheetRowMeta,
    WorksheetCellMeta,
)
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
        self._context.construction_focus_changed.connect(
            self._on_construction_focus
        )
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
        # Rows — canonical topology → fabric projection
        # --------------------------------------------------------------
        rows, metas = self._build_topology_rows_with_meta(ps, room)

        self._row_meta_by_surface = {
            meta.surface_id: meta
            for meta in metas
            if getattr(meta, "surface_id", None)
        }

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
        cid = getattr(self._context, "current_construction_id", None)
        if cid:
            self.highlight_rows_for_construction(cid)
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

    def highlight_rows_for_construction(self, cid: str) -> None:
        """
        Soft-highlight all HLP rows using the focused construction.

        Uses worksheet row meta as the projection contract.
        Does not mutate ProjectState.
        """

        table = self._panel._table

        for row in range(table.rowCount()):
            meta = self._panel.meta_for_row(row)
            assigned_cid = getattr(meta, "construction_id", None) if meta else None

            highlight = assigned_cid == cid

            for col in range(table.columnCount()):
                cell = table.item(row, col)
                if not cell:
                    continue

                if highlight and col == 0:
                    cell.setData(Qt.UserRole + 1, "true")
                else:
                    cell.setData(Qt.UserRole + 1, "")

        table.viewport().update()

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    def _on_construction_focus(self, cid: str) -> None:
        self.highlight_rows_for_construction(cid)

    def _on_current_room_changed(self, _room_id) -> None:
        self.refresh()

    def _on_cell_selected(self, row_index: int) -> None:
        """
        HLP row selection routing.

        Rules
        -----
        • Keep existing surface focus behaviour
        • Focus the selected row's construction
        • Do NOT open adjacency here
        • Do NOT alter selected-cell styling
        """

        meta = self._panel.meta_for_row(row_index)
        if not meta:
            return

        # --------------------------------------------------
        # Surface focus — existing behaviour
        # --------------------------------------------------
        surface_id = getattr(meta, "surface_id", None)
        if surface_id:
            self._context.request_edit("surface", surface_id)

        # --------------------------------------------------
        # Construction focus — Phase V-C4
        # --------------------------------------------------
        cid = getattr(meta, "construction_id", None)
        if not cid:
            return

        if hasattr(self._context, "set_current_construction_id"):
            self._context.set_current_construction_id(cid)
        else:
            # Legacy fallback only
            self._context.current_construction_id = cid
            self._context.construction_focus_changed.emit(cid)

        self.highlight_rows_for_construction(cid)

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

    def _build_topology_rows_with_meta(self, ps, room) -> tuple[list[dict], list[WorksheetRowMeta]]:
        """
        Build GUI worksheet rows from canonical topology → fabric rows.

        Projection only:
        • no ProjectState mutation
        • no controller execution
        • no readiness decisions

        Guarantees:
        • every display row carries surface_id
        • every display row has matching row meta
        • adjacency-editable rows are marked from boundary_kind
        """

        fabric_rows = generate_fabric_from_topology(ps, room)

        rows: list[dict] = []
        metas: list[WorksheetRowMeta] = []

        for src in fabric_rows:
            seg = getattr(src, "_segment", None)

            surface_id = (
                    getattr(src, "surface_id", None)
                    or getattr(src, "element_id", None)
                    or getattr(src, "segment_id", None)
                    or getattr(seg, "segment_id", None)
            )

            if surface_id is None:
                surface_id = f"{room.room_id}-row-{len(rows)}"

            boundary_kind = (
                    getattr(src, "boundary_kind", None)
                    or getattr(seg, "boundary_kind", None)
            )

            adjacent_room_id = (
                    getattr(src, "adjacent_room_id", None)
                    or getattr(seg, "adjacent_room_id", None)
            )

            construction_id = getattr(src, "construction_id", None)

            geometry_ref = (
                    getattr(src, "geometry_ref", None)
                    or getattr(seg, "geometry_ref", None)
                    or ""
            )

            surface_class = getattr(src, "surface_class", None)

            adjacent_label = None
            if boundary_kind == "INTER_ROOM" and adjacent_room_id:
                adjacent_room = ps.rooms.get(adjacent_room_id)
                adjacent_label = (
                    adjacent_room.name
                    if adjacent_room is not None and getattr(adjacent_room, "name", None)
                    else adjacent_room_id
                )

            # --------------------------------------------------
            # Build a projection source for formatting.
            # Do not let _format_element guess from partial src.
            # --------------------------------------------------

            format_src = {
                "surface_id": str(surface_id),
                "element_id": str(surface_id),
                "element": getattr(src, "element", None),
                "surface_class": surface_class,
                "geometry_ref": geometry_ref,
                "boundary_kind": boundary_kind,
                "adjacent_room_id": adjacent_room_id,
                "adjacent_label": adjacent_label,
                "_segment": seg,
            }

            element = self._format_element(format_src)

            rows.append({
                "surface_id": str(surface_id),
                "segment_id": str(surface_id),
                "element_id": str(surface_id),

                # HeatLossPanelV3.set_rows() expects lowercase "element".
                "element": element,

                "A": float(src.area_m2),
                "U": float(src.u_value_W_m2K),
                "dT": float(src.delta_t_K),
                "Qf": self._compute_qf(src),

                # Retained internally, not displayed as HLP column.
                "construction_id": construction_id,
                "boundary_kind": boundary_kind,
                "adjacent_room_id": adjacent_room_id,
                "adjacent_label": adjacent_label,
                "dT_label": self._format_dt(src),

                # Projection/debug fields.
                "_segment": seg,
                "geometry_ref": geometry_ref,
                "surface_class": surface_class,
            })

            adjacency_editable = (
                    boundary_kind == "INTER_ROOM"
                    and adjacent_room_id is not None
            )

            metas.append(
                WorksheetRowMeta(
                    surface_id=str(surface_id),
                    element=element,
                    adjacency_editable=adjacency_editable,
                    columns={
                        0: WorksheetCellMeta(
                            field="element",
                            editable=False,
                            kind="readonly",
                        ),
                        1: WorksheetCellMeta(
                            field="A",
                            editable=False,
                            kind="derived",
                        ),
                        2: WorksheetCellMeta(
                            field="U",
                            editable=False,
                            kind="derived",
                        ),
                        3: WorksheetCellMeta(
                            field="dT",
                            editable=adjacency_editable,
                            kind="derived",
                        ),
                        4: WorksheetCellMeta(
                            field="Qf",
                            editable=False,
                            kind="derived",
                        ),
                    },
                )
            )

        return rows, metas

    def _compute_qf(self, src) -> float:
        return float(src.area_m2 * src.u_value_W_m2K * src.delta_t_K)

    def _format_element(self, src) -> str:
        def read(obj, key: str, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        seg = read(src, "_segment", None)

        element = str(read(src, "element", "") or "").lower()
        surface_class = str(read(src, "surface_class", "") or "").lower()

        geometry_ref = str(
            read(src, "geometry_ref", None)
            or getattr(seg, "geometry_ref", "")
            or ""
        ).lower()

        boundary_kind = str(
            read(src, "boundary_kind", None)
            or getattr(seg, "boundary_kind", "")
            or ""
        ).upper()

        adjacent_room_id = (
                read(src, "adjacent_room_id", None)
                or getattr(seg, "adjacent_room_id", None)
        )

        # --------------------------------------------------
        # Geometry-first classification
        # --------------------------------------------------
        # Vertical adjacency must remain Floor/Ceiling.
        # It must not be displayed as Wall just because it is INTER_ROOM.
        # --------------------------------------------------

        if geometry_ref == "floor":
            if boundary_kind == "EXTERNAL":
                return "External Floor"
            return "Floor"

        if geometry_ref == "ceiling":
            if boundary_kind == "EXTERNAL":
                return "Roof / External Ceiling"
            return "Ceiling"

        if geometry_ref == "roof":
            if boundary_kind == "EXTERNAL":
                return "Roof / External Ceiling"
            return "Ceiling"

        if geometry_ref == "wall" or "edge" in geometry_ref:
            if boundary_kind == "EXTERNAL":
                return "External Wall"
            return "Wall"

        # --------------------------------------------------
        # Fallbacks
        # --------------------------------------------------

        if element == "floor" or surface_class == "floor":
            if boundary_kind == "EXTERNAL" or not boundary_kind:
                return "External Floor"
            return "Floor"

        if element in ("roof", "ceiling") or surface_class in ("roof", "ceiling"):
            if boundary_kind == "EXTERNAL" or not boundary_kind:
                return "Roof / External Ceiling"
            return "Ceiling"

        if element in ("external_wall", "wall") or surface_class in ("wall", "external_wall"):
            if boundary_kind == "EXTERNAL" or not boundary_kind:
                return "External Wall"
            return "Wall"

        if element == "internal_partition" or surface_class == "internal_partition":
            return "Wall"

        return str(element or surface_class).replace("_", " ").title()

    def _format_dt(self, src) -> str:
        text = f"{float(src.delta_t_K):.1f}"

        if src.boundary_kind == "INTER_ROOM" and src.adjacent_room_id:
            return f"{text} → {src.adjacent_room_id}"

        if src.boundary_kind == "EXTERNAL":
            return f"{text} → ext"

        return text

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    def _apply_run_result(self, *, success: bool, errors=None) -> None:
        if success:
            self._panel.set_ready()
        else:
            self._panel.set_not_ready(errors or ["Run failed"])

        self.refresh()