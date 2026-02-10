# ======================================================================
# HVAC/gui_v2/common/gui_view_state.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from HVAC.heatloss.dto.heatloss_results_dto import HeatLossResultDTO
from HVAC.project.project_state import ProjectState


@dataclass(slots=True)
class GuiViewState:
    """
    Canonical GUI view-state (v2).

    • Transient GUI truth only
    • NO physics
    • NO Qt widgets
    • Owns a SINGLE ProjectState reference (guarded)
    """

    # ------------------------------------------------------------
    # Active mode
    # ------------------------------------------------------------
    mode: str = "heatloss"

    # ------------------------------------------------------------
    # Project (authoritative engineering state)
    # ------------------------------------------------------------
    _project_state: Optional[ProjectState] = None

    # ------------------------------------------------------------
    # Education panel
    # ------------------------------------------------------------
    education_enabled: bool = False
    education_visible: bool = False

    # ------------------------------------------------------------
    # Heat-loss GUI state
    # ------------------------------------------------------------
    heatloss_results: Optional[HeatLossResultDTO] = None
    heatloss_valid: bool = False
    heat_demand_w: Optional[float] = None

    # ------------------------------------------------------------
    # Hydronics GUI state
    # ------------------------------------------------------------
    hydronics_dirty: bool = False

    # ------------------------------------------------------------
    # Guarded ProjectState access
    # ------------------------------------------------------------
    @property
    def project_state(self) -> Optional[ProjectState]:
        return self._project_state

    @project_state.setter
    def project_state(self, value: ProjectState) -> None:
        if self._project_state is not None and value is not self._project_state:
            raise RuntimeError(
                "❌ Forbidden: project_state reassigned!\n"
                f"old id={id(self._project_state)} new id={id(value)}"
            )
        self._project_state = value
