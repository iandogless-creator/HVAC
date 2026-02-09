# ======================================================================
# HVAC/gui_v2/modes/heatloss/widgets/geometry_inputs_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
)


@dataclass(frozen=True, slots=True)
class RectGeometry:
    length_m: float
    width_m: float
    height_m: float

    @property
    def floor_area_m2(self) -> float:
        return max(0.0, self.length_m) * max(0.0, self.width_m)

    @property
    def ceiling_area_m2(self) -> float:
        return self.floor_area_m2

    @property
    def perimeter_m(self) -> float:
        return 2.0 * (max(0.0, self.length_m) + max(0.0, self.width_m))

    @property
    def wall_area_m2(self) -> float:
        return self.perimeter_m * max(0.0, self.height_m)

    @property
    def volume_m3(self) -> float:
        return self.floor_area_m2 * max(0.0, self.height_m)


class GeometryInputsWidgetV1(QGroupBox):
    """
    HVACgooee — Geometry Inputs Widget v1 (GUI-only)

    Purpose
    -------
    Collect minimal rectangular geometry and expose derived quantities
    for UI orchestration (NOT engines).

    RULES
    -----
    • GUI-only
    • No engine imports
    • No DTO imports
    • Emits explicit signals for orchestration
    """

    geometry_changed = Signal(object)  # emits RectGeometry

    def __init__(self, *, default_height_m: float = 2.4, parent: QWidget | None = None):
        super().__init__(parent)
        self.setTitle("Geometry (simple rectangle)")

        # -----------------------------
        # Controls
        # -----------------------------
        self._length = QDoubleSpinBox()
        self._length.setRange(0.0, 9999.0)
        self._length.setDecimals(3)
        self._length.setSingleStep(0.1)
        self._length.setValue(5.0)
        self._length.setSuffix(" m")

        self._width = QDoubleSpinBox()
        self._width.setRange(0.0, 9999.0)
        self._width.setDecimals(3)
        self._width.setSingleStep(0.1)
        self._width.setValue(4.0)
        self._width.setSuffix(" m")

        self._height = QDoubleSpinBox()
        self._height.setRange(0.0, 99.0)
        self._height.setDecimals(3)
        self._height.setSingleStep(0.05)
        self._height.setValue(float(default_height_m))
        self._height.setSuffix(" m")

        # -----------------------------
        # Derived readouts (labels only)
        # -----------------------------
        self._floor_area_lbl = QLabel("0.00 m²")
        self._wall_area_lbl = QLabel("0.00 m²")
        self._volume_lbl = QLabel("0.00 m³")

        for lbl in (self._floor_area_lbl, self._wall_area_lbl, self._volume_lbl):
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # -----------------------------
        # Layout
        # -----------------------------
        grid = QGridLayout()
        r = 0

        grid.addWidget(QLabel("Length"), r, 0)
        grid.addWidget(self._length, r, 1)
        r += 1

        grid.addWidget(QLabel("Width"), r, 0)
        grid.addWidget(self._width, r, 1)
        r += 1

        grid.addWidget(QLabel("Height"), r, 0)
        grid.addWidget(self._height, r, 1)
        r += 1

        grid.addWidget(QLabel("Floor / Ceiling area (derived)"), r, 0)
        grid.addWidget(self._floor_area_lbl, r, 1)
        r += 1

        grid.addWidget(QLabel("Total wall area (derived)"), r, 0)
        grid.addWidget(self._wall_area_lbl, r, 1)
        r += 1

        grid.addWidget(QLabel("Volume (derived)"), r, 0)
        grid.addWidget(self._volume_lbl, r, 1)

        outer = QVBoxLayout()
        outer.addLayout(grid)
        outer.addStretch(1)
        self.setLayout(outer)

        # -----------------------------
        # Wiring
        # -----------------------------
        self._length.valueChanged.connect(self._emit)
        self._width.valueChanged.connect(self._emit)
        self._height.valueChanged.connect(self._emit)

        self._emit()  # initial

    def geometry(self) -> RectGeometry:
        return RectGeometry(
            length_m=float(self._length.value()),
            width_m=float(self._width.value()),
            height_m=float(self._height.value()),
        )

    def _emit(self) -> None:
        g = self.geometry()
        self._floor_area_lbl.setText(f"{g.floor_area_m2:.2f} m²")
        self._wall_area_lbl.setText(f"{g.wall_area_m2:.2f} m²")
        self._volume_lbl.setText(f"{g.volume_m3:.2f} m³")
        self.geometry_changed.emit(g)
