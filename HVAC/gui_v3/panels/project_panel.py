# ======================================================================
# HVACgooee — Compact Project Panel (GUI v3)
# ======================================================================

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class ProjectPanel(QWidget):
    """Compact read-only summary of current project state."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(260)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(12, 12, 12, 12)

        project_header = QLabel("Project")
        project_header.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(project_header)

        self._lbl_project_name = self._row("Name", "—")
        self._lbl_project_folder = self._row("Folder", "Unsaved")
        self._lbl_room_count = self._row("Rooms", "0")

        root.addItem(QSpacerItem(1, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        status_header = QLabel("Status")
        status_header.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(status_header)

        self._lbl_heatloss_status = self._row("Heat-Loss", "NOT RUN")
        self._lbl_hydronics_status = self._row("Hydronics", "NOT RUN")

        root.addStretch(1)

    def _row(self, label_text: str, value_text: str) -> QLabel:
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(f"{label_text}:")
        label.setMinimumWidth(76)
        value = QLabel(value_text)

        layout.addWidget(label)
        layout.addWidget(value, 1)
        self.layout().addWidget(row)
        return value

    def apply_view_model(self, vm: "ProjectSummaryViewModel | None") -> None:
        if vm is None:
            self._set_text(self._lbl_project_name, None)
            self._set_text(self._lbl_project_folder, "Unsaved")
            self._set_text(self._lbl_room_count, "0")
            self._set_text(self._lbl_heatloss_status, "NOT RUN")
            self._set_text(self._lbl_hydronics_status, "NOT RUN")
            return

        self._set_text(self._lbl_project_name, vm.project_name)
        self._set_text(self._lbl_project_folder, vm.project_folder)
        self._lbl_project_folder.setToolTip(vm.project_folder_path or "")
        self._set_text(self._lbl_room_count, vm.room_count)
        self._set_text(self._lbl_heatloss_status, vm.heatloss_status)
        self._set_text(self._lbl_hydronics_status, vm.hydronics_status)

    @staticmethod
    def _set_text(label: Optional[QLabel], value: Optional[str]) -> None:
        if label is not None:
            label.setText(value if value else "—")


class ProjectSummaryViewModel:
    """Read-only Project-panel projection."""

    def __init__(
        self,
        *,
        project_name: Optional[str],
        project_folder: Optional[str],
        project_folder_path: Optional[str],
        room_count: str,
        heatloss_status: str,
        hydronics_status: str,
    ) -> None:
        self.project_name = project_name
        self.project_folder = project_folder
        self.project_folder_path = project_folder_path
        self.room_count = room_count
        self.heatloss_status = heatloss_status
        self.hydronics_status = hydronics_status
