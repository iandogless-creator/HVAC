# ======================================================================
# HVAC/gui_v3/adapters/uvp_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.uvp_panel import UVPPanel
from PySide6.QtCore import Qt, Signal, QObject

from HVAC.constructions.physics.construction_model_save_candidate_v1 import (
    build_construction_model_save_candidate_v1,
)
from HVAC.core.construction_v1 import ConstructionV1
from HVAC.core.value_resolution import resolve_effective_internal_temp_C

class UVPPanelAdapter(QObject):
    """
    GUI v3 — UVP Panel Adapter

    Responsibilities
    ----------------
    • Observe UVP focus intent from GuiProjectContext
    • Update UVP panel presentation only

    Explicitly forbidden
    --------------------
    • ProjectState access
    • U-value calculation
    • Construction inference
    """
    u_value_changed = Signal(str, float)  # cid, value

    def __init__(self, *, panel: UVPPanel, context: GuiProjectContext) -> None:
        super().__init__()
        self._panel = panel
        self._context = context
        # --------------------------------------------------
        # Focus routing (FROM context → panel)
        # --------------------------------------------------
        context.subscribe_uvp_focus(self._on_focus_changed)

        self._context.construction_focus_changed.connect(
            self._on_construction_focus
        )

        # --------------------------------------------------
        # Intent routing (FROM panel → context)
        # --------------------------------------------------

        self._panel.u_value_changed.connect(
            self._context.request_construction_u_value_change
        )
        if hasattr(self._context, "surface_focus_changed"):
            self._context.surface_focus_changed.connect(
                self._on_surface_focus_changed
            )

        self._panel.assign_requested.connect(
            self._context.request_assign_construction
        )
        self._panel.construction_model_save_requested.connect(
            self._on_construction_model_save_requested
        )

    def _on_construction_model_save_requested(
        self,
        name: str,
        selected_method: str,
        evidence,
    ) -> None:
        ps = self._context.project_state
        if ps is None:
            self._panel.set_construction_model_save_result(
                ready=False,
                status="Blocked — no project is open.",
            )
            return

        result = build_construction_model_save_candidate_v1(
            evidence,
            name=name,
            selected_method=selected_method,
            existing_constructions=ps.constructions,
        )
        if not result.ready:
            self._panel.set_construction_model_save_result(
                ready=False,
                status=result.status + ": " + "; ".join(result.blockers),
            )
            return

        ps.constructions[result.construction_id] = ConstructionV1(
            construction_id=result.construction_id,
            name=result.name,
            u_value_W_m2K=float(result.u_value_W_m2K),
            layer_path_evidence=result.evidence.to_dict(),
            u_value_method_acceptance=result.method_acceptance.to_dict(),
        )
        ps.mark_heatloss_dirty()
        self._panel.set_constructions(ps.constructions)
        self._panel.set_construction_model_save_result(
            ready=True,
            status=result.status,
            construction_id=result.construction_id,
            model_name=result.name,
        )
        self._context.set_current_construction_id(result.construction_id)
        self._context.notify_project_changed()

    def _on_focus_changed(self, surface_id: str | None) -> None:
        """
        UVP surface focus projection.

        Compatibility-safe:
        older code used focus_surface();
        current UVPPanel uses set_selected_surface().
        """

        if not surface_id:
            surface_id = getattr(self._context, "current_surface_id", None)

        if hasattr(self._panel, "set_selected_surface"):
            self._panel.set_selected_surface(surface_id)
            return

        if hasattr(self._panel, "focus_surface"):
            self._panel.focus_surface(surface_id)
            return

    def _on_construction_focus(self, cid: str) -> None:
        self._panel.highlight_construction(cid)

        surface_id = getattr(self._context, "current_surface_id", None)
        if hasattr(self._panel, "set_selected_surface"):
            self._panel.set_selected_surface(surface_id)

    def _on_surface_focus_changed(self, surface_id: str | None) -> None:

        if hasattr(self._panel, "set_selected_surface"):
            self._panel.set_selected_surface(surface_id)
        elif hasattr(self._panel, "focus_surface"):
            self._panel.focus_surface(surface_id)

    def _push_heat_flow_temperature_contexts(self) -> None:
        ps = self._context.project_state
        if ps is None:
            self._panel.set_heat_flow_temperature_contexts([])
            return
        te_C = getattr(getattr(ps, "environment", None), "external_design_temp_C", None)
        contexts = []
        if te_C is not None:
            for room_id, room in ps.rooms.items():
                ti_C, source = resolve_effective_internal_temp_C(ps, room)
                if ti_C is None:
                    continue
                contexts.append((
                    str(room_id),
                    str(getattr(room, "name", room_id) or room_id),
                    float(ti_C),
                    float(te_C),
                    "room override" if source == "room" else "Environment default",
                ))
        surface_id = self._context.get_uvp_focus() or getattr(
            self._context, "current_surface_id", None
        )
        segment = getattr(ps, "boundary_segments", {}).get(surface_id)
        selected_room_id = (
            str(getattr(segment, "owner_room_id", "") or "")
            or str(getattr(self._context, "current_room_id", "") or "")
        )
        self._panel.set_heat_flow_temperature_contexts(
            contexts, selected_room_id or None
        )

    def refresh(self) -> None:
        ps = self._context.project_state
        if not ps:
            return

        # --------------------------------------------------
        # 1. Push construction library and heat-flow context
        # --------------------------------------------------
        self._panel.set_constructions(ps.constructions)
        self._push_heat_flow_temperature_contexts()

        # --------------------------------------------------
        # 2. Resolve current surface
        # --------------------------------------------------
        surface_id = self._context.get_uvp_focus()

        if not surface_id:
            surface_id = getattr(self._context, "current_surface_id", None)

        if not surface_id:
            self._panel.set_selected_surface(None)
            return

        self._panel.set_selected_surface(surface_id)

        # --------------------------------------------------
        # 3. Resolve assigned construction
        # --------------------------------------------------
        mapping = getattr(ps, "surface_construction_map", {}) or {}

        assigned_cid = mapping.get(surface_id)

        # fallback to topology default (important)
        if not assigned_cid:
            seg = ps.boundary_segments.get(surface_id)
            if seg:
                from HVAC.fabric.generate_fabric_from_topology import (
                    _resolve_construction_id,
                )

                assigned_cid = _resolve_construction_id(
                    ps,
                    surface_id,
                    seg.geometry_ref,
                    seg.boundary_kind,
                )

        # --------------------------------------------------
        # 4. Push to panel
        # --------------------------------------------------
        if hasattr(self._panel, "set_selected_construction"):
            self._panel.set_selected_construction(assigned_cid)
        elif hasattr(self._panel, "highlight_construction"):
            self._panel.highlight_construction(assigned_cid)
        elif hasattr(self._panel, "_select_construction_in_list"):
            self._panel._select_construction_in_list(assigned_cid)
