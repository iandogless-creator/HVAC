# ======================================================================
# ProjectState Inspector — READ ONLY
# ======================================================================

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from HVAC_legacy.project.project_state import ProjectState


class ProjectStateInspector(QWidget):
    """
    Read-only snapshot viewer for ProjectState.
    No mutation. No signals. No logic.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self._view = QTextBrowser()
        self._view.setReadOnly(True)
        layout.addWidget(self._view)

    def render(self, ps: ProjectState | None) -> None:
        if ps is None:
            self._view.setPlainText("No ProjectState loaded.")
            return

        self._view.setPlainText(
            "\n".join([
                "PROJECT STATE (AUTHORITATIVE)",
                "--------------------------------",
                f"heatloss_valid      : {ps.heatloss_valid}",
                f"heatloss_qt_w       : {ps.heatloss_qt_w}",
                "",
                f"hydronics_valid     : {ps.hydronics_valid}",
                f"hydronics_result    : {ps.hydronics_estimate_result is not None}",
                "",
                f"constructions_valid: {ps.constructions_valid}",
                f"constructions_count: {len(ps.constructions)}",
            ])
        )
