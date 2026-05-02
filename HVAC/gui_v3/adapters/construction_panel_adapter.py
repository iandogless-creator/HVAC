# HVAC/gui_v3/adapters/construction_panel_adapter.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from HVAC.gui_v3.panels.construction_panel import ConstructionPanel
    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext


class ConstructionPanelAdapter:
    def __init__(self, panel: ConstructionPanel, context: GuiProjectContext) -> None:
        self._panel = panel
        self._context = context
        self._panel.construction_selected.connect(self.refresh)
        # UI intent routing (ONE-TIME)
        self._panel.open_uvp_requested.connect(
            self._context.request_uvp_focus
        )

    def refresh(self) -> None:
        ps = self._context.project_state

        if ps is None:
            return

        selected_cid = self._panel.get_selected_construction_id()

        if not selected_cid:
            self._panel.set_usage_count(0)
            return
        self._context.construction_focus_changed.emit(selected_cid)

        mapping = getattr(ps, "surface_construction_map", None) or {}

        count = sum(1 for v in mapping.values() if v == selected_cid)

        self._panel.set_usage_count(count)