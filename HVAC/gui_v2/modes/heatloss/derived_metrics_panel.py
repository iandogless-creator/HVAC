# ======================================================================
# BEGIN FILE: HVAC/gui_v2/modes/heatloss/derived_metrics_panel.py
# ======================================================================
"""
derived_metrics_panel.py
------------------------

HVACgooee — Derived Heat-Loss Metrics Panel (GUI v2)

Purpose:
- Display SECONDARY metrics derived from HeatLossResultDTO
- Educational / interpretive only

Contract:
- NO physics
- NO recalculation of Qt
- Uses constants explicitly
- Accepts DTO as single input

Examples:
- ΣA
- ΣQf
- Cv
- Ce (reserved)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QGroupBox,
)

from HVAC.heatloss.dto.heatloss_results_dto import HeatLossResultDTO


# ============================================================================
# Constants (LOCKED for v1)
# ============================================================================

TAI_DIVISOR: float = 4.8   # Historical / CIBSE-derived constant


# ============================================================================
# Panel
# ============================================================================

class DerivedMetricsPanel(QWidget):
    """
    Displays derived (secondary) heat-loss metrics.

    All values are derived from DTO ONLY.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._dto: Optional[HeatLossResultDTO] = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        box = QGroupBox("Derived Metrics (Educational)")
        layout = QGridLayout(box)
        layout.setColumnStretch(1, 1)

        self.lbl_sum_area = QLabel("—")
        self.lbl_sum_qf = QLabel("—")
        self.lbl_cv = QLabel("—")
        self.lbl_ce = QLabel("—")

        layout.addWidget(QLabel("Σ Area (m²):"), 0, 0)
        layout.addWidget(self.lbl_sum_area, 0, 1)

        layout.addWidget(QLabel("Σ Qf (W):"), 1, 0)
        layout.addWidget(self.lbl_sum_qf, 1, 1)

        layout.addWidget(QLabel("Cv:"), 2, 0)
        layout.addWidget(self.lbl_cv, 2, 1)

        layout.addWidget(QLabel("Ce:"), 3, 0)
        layout.addWidget(self.lbl_ce, 3, 1)

        root.addWidget(box)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self._dto = None
        self.lbl_sum_area.setText("—")
        self.lbl_sum_qf.setText("—")
        self.lbl_cv.setText("—")
        self.lbl_ce.setText("—")

    def load_results(self, dto: HeatLossResultDTO) -> None:
        """
        Accept DTO and derive metrics.

        NO recalculation of Qt.
        """
        self._dto = dto

        sum_area = sum(b.area_m2 for b in dto.boundaries)
        sum_qf = dto.total_fabric_heat_loss_w

        self.lbl_sum_area.setText(f"{sum_area:.2f}")
        self.lbl_sum_qf.setText(f"{sum_qf:.1f} W")

        # Cv = ΣQf / ΣA / 4.8
        if sum_area > 0:
            cv = sum_qf / sum_area / TAI_DIVISOR
            self.lbl_cv.setText(f"{cv:.3f}")
        else:
            self.lbl_cv.setText("—")

        # Ce — reserved for future definition
        self.lbl_ce.setText("—")


# ======================================================================
# END FILE
# ======================================================================
