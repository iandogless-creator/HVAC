# ======================================================================
# HVACgooee — Project Panel Adapter (GUI v3)
# ======================================================================

from __future__ import annotations

from pathlib import Path
from typing import Any

from HVAC.gui_v3.panels.project_panel import (
    ProjectPanel,
    ProjectSummaryViewModel,
)


class ProjectPanelAdapter:
    """Read-only live projection of the current ProjectState."""

    def __init__(self, *, panel: ProjectPanel, context: Any) -> None:
        self._panel = panel
        self._context = context

        context.project_changed.connect(self.refresh)
        context.environment_changed.connect(self.refresh)
        context.room_state_changed.connect(lambda _room_id: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        project = getattr(self._context, "project_state", None)
        if project is None:
            self._panel.apply_view_model(None)
            return

        project_dir = getattr(project, "project_dir", None)
        resolved_dir = Path(project_dir) if project_dir is not None else None

        self._panel.apply_view_model(ProjectSummaryViewModel(
            project_name=getattr(project, "name", None),
            project_folder=(resolved_dir.name if resolved_dir else "Unsaved"),
            project_folder_path=(str(resolved_dir) if resolved_dir else None),
            room_count=str(len(getattr(project, "rooms", {}) or {})),
            heatloss_status=self._status(
                results=getattr(project, "heatloss_results", None),
                valid=bool(getattr(project, "heatloss_valid", False)),
            ),
            hydronics_status=self._status(
                results=getattr(project, "hydronics_results", None),
                valid=bool(getattr(project, "hydronics_valid", False)),
            ),
        ))

    @staticmethod
    def _status(*, results: object, valid: bool) -> str:
        if valid:
            return "VALID"
        if results is not None:
            return "DIRTY"
        return "NOT RUN"
