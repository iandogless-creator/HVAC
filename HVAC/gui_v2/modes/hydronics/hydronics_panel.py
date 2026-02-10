# ======================================================================
# HVAC/gui_v2/modes/hydronics/hydronics_panel.py
# ======================================================================

"""
HVACgooee — Hydronics Panel (Estimate v3)

RULES (LOCKED)
--------------
• READ-ONLY with respect to ProjectState
• Does NOT run engines
• Does NOT mutate ProjectState
• Consumes committed (authoritative) heat-loss only
• Emits explicit user intent to run hydronics
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)

from HVAC.gui_v2.common.gui_view_state import GuiViewState
from HVAC.hydronics_v3.dto.hydronics_estimate_result_dto import (
    HydronicsEstimateResultDTO,
)


class HydronicsPanel(QWidget):
    """
    Hydronics estimate panel (v3).
    """

    # 🔒 Intent only
    run_hydronics_requested = Signal()

    def __init__(
        self,
        view_state: GuiViewState,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.view_state = view_state
        self._build_ui()

    def _build_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Authoritative Qt banner
        self.lbl_qt_authoritative = QLabel("Design Load (Qt): —")
        self.lbl_qt_authoritative.setStyleSheet(
            "font-weight:600; color:#9aa0a6;"
        )
        self.main_layout.addWidget(self.lbl_qt_authoritative)

        self.btn_run = QPushButton("Run Hydronics")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self._on_run_clicked)
        self.main_layout.addWidget(self.btn_run)

        self.main_layout.addStretch(1)

    def sync_heatloss_authority(self) -> None:
        """
        Reflect authoritative heat-loss into Hydronics.
        """
        ps = self.view_state.project_state

        if ps and ps.heatloss_valid and ps.heatloss_qt_w is not None:
            self.lbl_qt_authoritative.setText(
                f"Design Load (Qt): {ps.heatloss_qt_w:.2f} W"
            )
            self.lbl_qt_authoritative.setStyleSheet(
                "font-weight:600; color:#2e7d32;"
            )
        else:
            self.lbl_qt_authoritative.setText(
                "Design Load (Qt): — (Run Heat-Loss Engine)"
            )
            self.lbl_qt_authoritative.setStyleSheet(
                "font-weight:600; color:#9aa0a6;"
            )

    # ------------------------------------------------------------------
    # READ-ONLY sync
    # ------------------------------------------------------------------

    def refresh_from_project_state(self) -> None:
        ps = self.view_state.project_state
        if ps is None:
            print("[Hydronics] refresh: project_state = None")
            return

        print(
            "[Hydronics] refresh:",
            f"heatloss_valid={getattr(ps, 'heatloss_valid', None)}",
            f"heatloss_qt_w={getattr(ps, 'heatloss_qt_w', None)}",
            f"hydronics_valid={getattr(ps, 'hydronics_valid', None)}",
        )

        if ps.heatloss_valid and ps.heatloss_qt_w is not None:
            self.lbl_qt_authoritative.setText(
                f"Design Load (Qt): {ps.heatloss_qt_w:.2f} W"
            )
            self.btn_run.setEnabled(True)
        else:
            self.lbl_qt_authoritative.setText("Design Load (Qt): —")
            self.btn_run.setEnabled(False)

    # ------------------------------------------------------------------
    # Intent
    # ------------------------------------------------------------------

    def _on_run_clicked(self) -> None:
        self.run_hydronics_requested.emit()

    # ------------------------------------------------------------------
    # Rendering (UI-only)
    # ------------------------------------------------------------------

    def render_results(self, result: HydronicsEstimateResultDTO) -> None:
        QMessageBox.information(
            self,
            "Hydronics Estimate Complete",
            (
                f"Design Load (Qt): {result.design_heat_load_w:.2f} W\n"
                f"Flow: {result.design_flow_rate_l_s:.3f} l/s\n"
                f"Flow: {result.design_flow_rate_m3_h:.3f} m³/h"
            ),
        )

