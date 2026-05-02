# ======================================================================
# HVAC/gui_v3/adapters/uvp_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.uvp_panel import UVPPanel
from PySide6.QtCore import Qt, Signal, QObject

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
        self._panel = panel
        self._context = context
        super().__init__()
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

        self._panel.assign_requested.connect(
            self._context.request_assign_construction
        )


    def _on_focus_changed(self, surface_id: str | None) -> None:
        self._panel.focus_surface(surface_id)

    def _on_construction_focus(self, cid: str) -> None:
        self._panel.highlight_construction(cid)

    def refresh(self) -> None:
        ps = self._context.project_state
        if not ps:
            return

        # --------------------------------------------------
        # 1. Push construction library
        # --------------------------------------------------
        self._panel.set_constructions(ps.constructions)

        # --------------------------------------------------
        # 2. Resolve current surface
        # --------------------------------------------------
        surface_id = self._context.get_uvp_focus()
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
                    _resolve_construction_id
                )
                assigned_cid = _resolve_construction_id(
                    ps,
                    seg,
                    seg.geometry_ref,
                )

        # --------------------------------------------------
        # 4. Push to panel
        # --------------------------------------------------
        if assigned_cid:
            self._panel.set_selected_construction(assigned_cid)