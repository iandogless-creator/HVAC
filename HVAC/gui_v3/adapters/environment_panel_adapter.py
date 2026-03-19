# ======================================================================
# HVAC/gui_v3/adapters/environment_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel


class EnvironmentPanelAdapter:
    """
    Canonical Adapter

    Responsibilities
    ----------------
    • Sync EnvironmentPanel <-> ProjectState.environment
    • Mutate authoritative state on user input
    • Mark heatloss dirty on changes
    """

    def __init__(
        self,
        context: GuiProjectContext,
        panel: EnvironmentPanel,
    ) -> None:
        self._context = context
        self._panel = panel

        panel.external_temp_changed.connect(self._on_external_temp_changed)
        panel.default_internal_temp_changed.connect(self._on_default_internal_temp_changed)
        panel.default_height_changed.connect(self._on_default_height_changed)
        panel.default_ach_changed.connect(self._on_default_ach_changed)

    # ------------------------------------------------------------------
    # Observer refresh
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        ps = self._context.project_state
        if ps is None:
            return

        if ps.environment is None:
            ps.environment = EnvironmentStateV1()

        env = ps.environment

        self._panel.set_external_temp(
            getattr(env, "external_design_temp_C", None)
            or getattr(env, "external_design_temp_C", None)
        )

        self._panel.set_default_internal_temp(
            getattr(env, "default_internal_temp", None)
            or getattr(env, "default_internal_temp_C", None)
        )

        self._panel.set_default_height(
            getattr(env, "default_room_height_m", None)
        )

        self._panel.set_default_ach(
            getattr(env, "default_ach", None)
        )

    # ------------------------------------------------------------------
    # Signal handlers (authoritative mutation)
    # ------------------------------------------------------------------

    def _ensure_env(self) -> EnvironmentStateV1:
        ps = self._context.project_state
        if ps is None:
            raise RuntimeError("No project_state in GUI context")

        if ps.environment is None:
            ps.environment = EnvironmentStateV1()

        return ps.environment

    def _mark_dirty(self) -> None:
        ps = self._context.project_state
        if ps is None:
            return

        if hasattr(ps, "mark_heatloss_dirty"):
            ps.mark_heatloss_dirty()

    # ------------------------------------------------------------------
    # External temperature
    # ------------------------------------------------------------------

    def _on_external_temp_changed(self, value: float) -> None:
        env = self._ensure_env()

        if hasattr(env, "external_design_temp_C"):
            env.external_design_temp_C = value
        else:
            env.external_design_temp_C = value

        self._mark_dirty()

        # notify observers (ΔT refresh etc)
        self._context.environment_changed.emit()

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------

    def _on_default_internal_temp_changed(self, value: float) -> None:
        env = self._ensure_env()

        if hasattr(env, "default_internal_temp_C"):
            env.default_internal_temp_C = value
        else:
            env.default_internal_temp = value

        self._mark_dirty()

        self._context.environment_changed.emit()

    def _on_default_height_changed(self, value: float) -> None:
        env = self._ensure_env()
        env.default_room_height_m = value

        self._mark_dirty()

        self._context.environment_changed.emit()

    def _on_default_ach_changed(self, value: float) -> None:
        env = self._ensure_env()
        env.default_ach = value

        self._mark_dirty()

        self._context.environment_changed.emit()