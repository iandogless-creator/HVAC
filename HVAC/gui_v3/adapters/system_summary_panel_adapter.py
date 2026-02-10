# ======================================================================
# HVACgooee — System Summary Panel Adapter (GUI v3)
# Phase: E — Wiring (ViewModel)
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from typing import Optional

from HVAC.project.project_state import ProjectState

from HVAC.gui_v3.panels.system_summary_panel import (
    SystemSummaryPanel,
    SystemSummaryViewModel,
)


class SystemSummaryPanelAdapter:
    """
    System Summary Panel Adapter (GUI v3)

    Role
    ----
    • Phase E wiring adapter
    • Translates ProjectState → SystemSummaryViewModel
    • Read-only
    • No calculations
    • No inference
    """

    def __init__(
        self,
        *,
        panel: SystemSummaryPanel,
        project_state: ProjectState,
    ) -> None:
        self._panel = panel
        self._ps = project_state

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self._panel.apply_view_model(self._build_view_model())

    # ------------------------------------------------------------------
    # ViewModel construction
    # ------------------------------------------------------------------
    def _build_view_model(self) -> SystemSummaryViewModel:
        ps = self._ps

        return SystemSummaryViewModel(
            total_heatloss_w=_fmt(ps.total_heatloss_w),
            design_dt_c=_fmt(ps.design_dt_c),
            flow_rate_kg_s=_fmt(ps.design_flow_rate_kg_s),
            pump_head_kpa=_fmt(ps.pump_head_kpa),
        )


# ----------------------------------------------------------------------
# Formatting helper (presentation-only)
# ----------------------------------------------------------------------
def _fmt(value: Optional[float]) -> Optional[str]:
    """
    Presentation-safe formatting.
    No rounding policy.
    No units.
    No defaults.
    """
    return None if value is None else f"{value}"
