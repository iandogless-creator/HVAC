# HVAC/gui_v3/adapters/construction_panel_adapter.py
class ConstructionPanelAdapter:
    def __init__(self, panel: ConstructionPanel, context: GuiProjectContext) -> None:
        self._panel = panel
        self._context = context

        # UI intent routing (ONE-TIME)
        self._panel.open_uvp_requested.connect(
            self._context.request_uvp_focus
        )

    def commit_construction(self, surface_id: str, construction_id: str) -> None:
        ps = self._context.project_state
        room = self._context.current_room

        if ps is None or room is None:
            return

        room.constructions[surface_id] = construction_id

        # Phase I-B
        ps.mark_heatloss_dirty()