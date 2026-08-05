# ======================================================================
# HVAC/gui_v3/adapters/environment_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.heatloss.physics.environment_pipe_pair_spacing_defaults_v1 import (
    default_environment_pipe_pair_spacing_defaults_v1,
    normalise_environment_pipe_pair_spacing_defaults_v1,
)


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
        panel.design_flow_temp_changed.connect(self._on_design_flow_temp_changed)
        panel.design_return_temp_changed.connect(self._on_design_return_temp_changed)
        panel.basic_ps_max_velocity_changed.connect(
            self._on_basic_ps_max_velocity_changed
        )
        panel.bare_pipe_emissivity_changed.connect(
            self._on_bare_pipe_emissivity_changed
        )
        panel.bare_pipe_pair_spacing_default_changed.connect(
            self._on_bare_pipe_pair_spacing_default_changed
        )

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

        self._panel.set_design_flow_temp(
            getattr(env, "design_flow_temp_c", None)
        )

        self._panel.set_design_return_temp(
            getattr(env, "design_return_temp_c", None)
        )

        self._panel.set_basic_ps_max_velocity(
            getattr(env, "basic_ps_max_velocity_m_s", 1.0)
        )
        self._panel.set_bare_pipe_emissivity(
            getattr(env, "bare_pipe_emissivity", None)
        )
        self._panel.set_bare_pipe_pair_spacing_defaults(
            getattr(
                env,
                "bare_pipe_pair_spacing_defaults_by_nominal_od_mm",
                default_environment_pipe_pair_spacing_defaults_v1(),
            )
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

    # ------------------------------------------------------------------
    # H-S21-A — Hydronic design source inputs
    # ------------------------------------------------------------------

    def _on_design_flow_temp_changed(self, value: float) -> None:
        env = self._ensure_env()
        env.design_flow_temp_c = value

        # Hydronic design temperatures do not affect fabric heat-loss.
        self._context.environment_changed.emit()

    def _on_design_return_temp_changed(self, value: float) -> None:
        env = self._ensure_env()
        env.design_return_temp_c = value

        # Hydronic design temperatures do not affect fabric heat-loss.
        self._context.environment_changed.emit()

    # ------------------------------------------------------------------
    # H-S37-B1 — Basic PS maximum velocity default intent
    # ------------------------------------------------------------------

    def _on_basic_ps_max_velocity_changed(self, value: float) -> None:
        env = self._ensure_env()
        env.basic_ps_max_velocity_m_s = value

        # Basic PS intent does not affect fabric heat-loss.
        self._context.environment_changed.emit()

    # ------------------------------------------------------------------
    # H-S66-K — universal bare-pipe emissivity default
    # ------------------------------------------------------------------

    def _on_bare_pipe_emissivity_changed(self, value: float) -> None:
        env = self._ensure_env()
        env.bare_pipe_emissivity = None if value < 0.0 else float(value)

        # Surface emissivity affects pipe radiation only, not fabric heat loss.
        self._context.environment_changed.emit()
        project_changed = getattr(self._context, "project_changed", None)
        emit = getattr(project_changed, "emit", None)
        if callable(emit):
            emit()

    # ------------------------------------------------------------------
    # H-S66-N1A — universal stacked pipe-pair support geometry
    # ------------------------------------------------------------------

    def _on_bare_pipe_pair_spacing_default_changed(
            self,
            nominal_od_mm: int,
            support_type: str,
            centre_spacing_mm: float,
    ) -> None:
        env = self._ensure_env()
        values = getattr(
            env,
            "bare_pipe_pair_spacing_defaults_by_nominal_od_mm",
            default_environment_pipe_pair_spacing_defaults_v1(),
        )
        values = normalise_environment_pipe_pair_spacing_defaults_v1(values)
        values[str(int(nominal_od_mm))] = {
            "support_type": str(support_type),
            "centre_spacing_mm": float(centre_spacing_mm),
        }
        env.bare_pipe_pair_spacing_defaults_by_nominal_od_mm = (
            normalise_environment_pipe_pair_spacing_defaults_v1(values)
        )

        # Pair spacing affects pipe external convection only.
        self._context.environment_changed.emit()
        project_changed = getattr(self._context, "project_changed", None)
        emit = getattr(project_changed, "emit", None)
        if callable(emit):
            emit()
