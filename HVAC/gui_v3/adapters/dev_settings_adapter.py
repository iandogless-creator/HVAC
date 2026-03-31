# ======================================================================
# HVAC/gui_v3/adapters/dev_settings_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.gui_v3.panels.dev_settings_panel import DevSettingsPanel
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext


class DevSettingsAdapter:
    """
    Handles DEV panel actions.

    Responsibility
    --------------
    • Receives UI intent
    • Triggers topology rebuild
    """

    def __init__(
        self,
        *,
        panel: DevSettingsPanel,
        context: GuiProjectContext,
        main_window,
    ) -> None:
        self._panel = panel
        self._context = context
        self._main_window = main_window

        self._panel.topology_mode_changed.connect(self._on_mode_changed)

    # ------------------------------------------------------------------
    # Event
    # ------------------------------------------------------------------

    def _on_mode_changed(self, mode: str) -> None:
        ps = self._context.project_state
        if ps is None:
            return

        if mode == "bootstrap":
            from HVAC.topology.dev_two_room_adjacency_bootstrap import (
                apply_two_room_adjacency_bootstrap,
            )
            apply_two_room_adjacency_bootstrap(ps)

        elif mode == "resolver":
            from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
            TopologyResolverV1.resolve_project(ps)

        # --------------------------------------------------
        # Refresh entire UI
        # --------------------------------------------------
        ps.mark_heatloss_dirty()
        self._main_window._refresh_all_adapters()