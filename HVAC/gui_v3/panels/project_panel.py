# ======================================================================
# HVACgooee — Project Panel (GUI v3)
# ======================================================================

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
)


# ----------------------------------------------------------------------
# ProjectPanel
# ----------------------------------------------------------------------
class ProjectPanel(QWidget):
    """
    GUI v3 — Project Panel (Observer)

    Phase C: Read-only ViewModel binding.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Stored label references (read-only targets)
        self._lbl_project_name: Optional[QLabel] = None
        self._lbl_project_ref: Optional[QLabel] = None
        self._lbl_project_rev: Optional[QLabel] = None
        self._lbl_heatloss_status: Optional[QLabel] = None
        self._lbl_hydronics_status: Optional[QLabel] = None
        self.setMinimumWidth(260)


        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction (Frozen Layout)
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # ==============================================================
        # Section: Project
        # ==============================================================
        project_header = QLabel("Project")
        project_header.setStyleSheet(
            "font-size: 13px; font-weight: 600;"
        )
        root.addWidget(project_header)

        self._lbl_project_name = self._row("Name:", "—")
        self._lbl_project_ref = self._row("Reference:", "—")
        self._lbl_project_rev = self._row("Revision:", "—")

        root.addWidget(self._lbl_project_name.parentWidget())
        root.addWidget(self._lbl_project_ref.parentWidget())
        root.addWidget(self._lbl_project_rev.parentWidget())

        root.addItem(QSpacerItem(1, 16, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # ==============================================================
        # Section: Status
        # ==============================================================
        status_header = QLabel("Status")
        status_header.setStyleSheet(
            "font-size: 13px; font-weight: 600;"
        )
        root.addWidget(status_header)

        self._lbl_heatloss_status = self._row("Heat-loss:", "not run")
        self._lbl_hydronics_status = self._row("Hydronics:", "not run")

        root.addWidget(self._lbl_heatloss_status.parentWidget())
        root.addWidget(self._lbl_hydronics_status.parentWidget())

        root.addStretch(1)

    # ------------------------------------------------------------------
    # Static Row Helper (Frozen)
    # ------------------------------------------------------------------
    def _row(self, label_text: str, value_text: str) -> QLabel:
        """
        Creates a single static label/value row and returns
        the VALUE label for later read-only updates.
        """
        row = QWidget(self)
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        label = QLabel(label_text)
        value = QLabel(value_text)

        layout.addWidget(label)
        layout.addWidget(value)

        return value

    # ------------------------------------------------------------------
    # Phase C Binding API (Read-Only)
    # ------------------------------------------------------------------
    def apply_view_model(self, vm: "ProjectSummaryViewModel | None") -> None:
        """
        Applies a read-only ProjectSummaryViewModel.

        If vm is None, panel remains in default '— / not run' state.
        """
        if vm is None:
            return

        self._set_text(self._lbl_project_name, vm.project_name)
        self._set_text(self._lbl_project_ref, vm.project_reference)
        self._set_text(self._lbl_project_rev, vm.project_revision)

        self._set_text(self._lbl_heatloss_status, vm.heatloss_status)
        self._set_text(self._lbl_hydronics_status, vm.hydronics_status)

    # ------------------------------------------------------------------
    # Internal Helper
    # ------------------------------------------------------------------
    @staticmethod
    def _set_text(label: Optional[QLabel], value: Optional[str]) -> None:
        if label is None:
            return
        label.setText(value if value else "—")


# ----------------------------------------------------------------------
# ViewModel Contract (Read-Only)
# ----------------------------------------------------------------------
class ProjectSummaryViewModel:
    """
    Read-only DTO for ProjectPanel.

    No logic.
    No defaults.
    No ownership.
    """

    def __init__(
        self,
        project_name: Optional[str],
        project_reference: Optional[str],
        project_revision: Optional[str],
        heatloss_status: Optional[str],
        hydronics_status: Optional[str],
    ) -> None:
        self.project_name = project_name
        self.project_reference = project_reference
        self.project_revision = project_revision
        self.heatloss_status = heatloss_status
        self.hydronics_status = hydronics_status
