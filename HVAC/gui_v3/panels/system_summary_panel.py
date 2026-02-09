# ======================================================================
# HVACgooee — System Summary Panel (GUI v3)
# Phase: GUI v3 — Observer
# Sub-Phase: Phase C (Read-Only Binding)
# Status: READY
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


class SystemSummaryPanel(QWidget):
    """
    GUI v3 — System Summary Panel (Observer)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._lbl_total_heatloss: Optional[QLabel] = None
        self._lbl_design_dt: Optional[QLabel] = None
        self._lbl_flow_rate: Optional[QLabel] = None
        self._lbl_pump_head: Optional[QLabel] = None

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        header_hl = QLabel("Heat-Loss")
        header_hl.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(header_hl)

        self._lbl_total_heatloss = self._row("Total heat loss:", "—")
        self._lbl_design_dt = self._row("Design ΔT:", "—")

        root.addWidget(self._lbl_total_heatloss.parentWidget())
        root.addWidget(self._lbl_design_dt.parentWidget())

        root.addItem(QSpacerItem(1, 16, QSizePolicy.Minimum, QSizePolicy.Fixed))

        header_hy = QLabel("Hydronics")
        header_hy.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(header_hy)

        self._lbl_flow_rate = self._row("Design flow rate:", "—")
        self._lbl_pump_head = self._row("Pump head:", "—")

        root.addWidget(self._lbl_flow_rate.parentWidget())
        root.addWidget(self._lbl_pump_head.parentWidget())

        root.addStretch(1)

    def _row(self, label_text: str, value_text: str) -> QLabel:
        row = QWidget(self)
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        label = QLabel(label_text)
        value = QLabel(value_text)

        layout.addWidget(label)
        layout.addWidget(value)

        return value

    def apply_view_model(self, vm: "SystemSummaryViewModel | None") -> None:
        if vm is None:
            return

        self._set(self._lbl_total_heatloss, vm.total_heatloss)
        self._set(self._lbl_design_dt, vm.design_dt)
        self._set(self._lbl_flow_rate, vm.flow_rate)
        self._set(self._lbl_pump_head, vm.pump_head)

    @staticmethod
    def _set(label: Optional[QLabel], value: Optional[str]) -> None:
        if label:
            label.setText(value if value else "—")


class SystemSummaryViewModel:
    """
    Read-only DTO for SystemSummaryPanel.
    """

    def __init__(
        self,


    total_heatloss: Optional[str],
        design_dt: Optional[str],
        flow_rate: Optional[str],
        pump_head: Optional[str],
    ) -> None:
        self.total_heatloss = total_heatloss
        self.design_dt = design_dt
        self.flow_rate = flow_rate
        self.pump_head = pump_head
