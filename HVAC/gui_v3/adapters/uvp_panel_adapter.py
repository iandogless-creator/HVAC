# ======================================================================
# HVAC/gui_v3/adapters/uvp_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.uvp_panel import UVPPanel


class UVPPanelAdapter:
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

    def __init__(self, *, panel: UVPPanel, context: GuiProjectContext) -> None:
        self._panel = panel
        self._context = context

        context.subscribe_uvp_focus(self._on_focus_changed)

    def _on_focus_changed(self, surface_id: str | None) -> None:
        self._panel.focus_surface(surface_id)