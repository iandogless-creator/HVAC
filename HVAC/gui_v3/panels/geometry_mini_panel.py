# ======================================================================
# HVAC/gui_v3/panels/geometry_mini_panel.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QHBoxLayout,
)


class GeometryMiniPanel(QWidget):
    """
    GUI v3 — Geometry Mini Panel

    Phase I-B:
    • Pure intent editor
    • No ProjectState access
    • No calculations
    """

    geometry_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)

        header = QLabel("Geometry (internal)")
        header.setStyleSheet("font-weight: 600;")
        root.addWidget(header)

        self._spin_length = self._m_spin()
        self._spin_width = self._m_spin()
        self._spin_height = self._m_spin()
        self._spin_ti = self._temp_spin()

        self._lbl_floor_area = QLabel("— m²")
        self._lbl_volume = QLabel("— m³")

        root.addLayout(self._row("Length (m):", self._spin_length))
        root.addLayout(self._row("Width (m):", self._spin_width))
        root.addLayout(self._row("Height (m):", self._spin_height))

        root.addSpacing(4)
        root.addLayout(self._row("Floor area:", self._lbl_floor_area))
        root.addLayout(self._row("Volume:", self._lbl_volume))

        root.addSpacing(6)
        root.addLayout(self._row("Internal design temp (°C):", self._spin_ti))

        for w in (
            self._spin_length,
            self._spin_width,
            self._spin_height,
            self._spin_ti,
        ):
            w.valueChanged.connect(self._emit_geometry)

    def _emit_geometry(self) -> None:
        self.geometry_changed.emit({
            "length_m": self._spin_length.value(),
            "width_m": self._spin_width.value(),
            "height_m": self._spin_height.value(),
            "ti_c": self._spin_ti.value(),
        })

    def _row(self, label: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addStretch()
        row.addWidget(widget)
        return row

    def _m_spin(self) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(0.0, 1000.0)
        s.setDecimals(2)
        s.setSuffix(" m")
        return s

    def _temp_spin(self) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(-50.0, 50.0)
        s.setDecimals(1)
        s.setSuffix(" °C")
        return s

    def clear(self) -> None:
        self._spin_length.setValue(0.0)
        self._spin_width.setValue(0.0)
        self._spin_height.setValue(0.0)
        self._spin_ti.setValue(0.0)
        self._lbl_floor_area.setText("—")
        self._lbl_volume.setText("—")
