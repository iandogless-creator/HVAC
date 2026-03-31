# ======================================================================
# HVAC/gui_v3/panels/geometry_mini_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional, Dict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QHBoxLayout,
)


# ======================================================================
# GeometryMiniPanel
# ======================================================================

class GeometryMiniPanel(QWidget):
    """
    Geometry editor (overlay panel)

    Authority
    ---------
    • Edits geometry only (length, width, height)
    • Emits committed values only
    • Does NOT mutate ProjectState directly
    • Does NOT perform calculations
    • Does NOT display results (Qf, etc.)

    Lifecycle
    ---------
    • Created by OverlayController
    • Primed by adapter
    • Emits commit → adapter writes → refresh
    """

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    geometry_committed = Signal(dict)
    ti_changed = Signal(float)
    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self._last_values: Optional[Dict] = None

        self._build_ui()
        self._wire_signals()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Header
        self._header = QLabel("Geometry")
        self._header.setStyleSheet("font-weight: 600;")
        root.addWidget(self._header)

        # Inputs
        self._spin_length = self._m_spin()
        self._spin_width = self._m_spin()
        self._spin_height = self._m_spin()

        root.addLayout(self._row("Length (m):", self._spin_length))
        root.addLayout(self._row("Width (m):", self._spin_width))
        root.addLayout(self._row("Height (m):", self._spin_height))

        self._ti = QDoubleSpinBox()
        self._ti.setRange(5.0, 35.0)
        self._ti.setDecimals(1)
        self._ti.setSuffix(" °C")
        self._ti.editingFinished.connect(
            lambda: self.ti_changed.emit(self._ti.value())
        )
        # Derived display (read-only, visual only)
        self._lbl_floor = QLabel("— m²")
        self._lbl_volume = QLabel("— m³")

        root.addSpacing(4)
        root.addLayout(self._row("Floor area:", self._lbl_floor))
        root.addLayout(self._row("Volume:", self._lbl_volume))

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _wire_signals(self) -> None:
        for spin in (self._spin_length, self._spin_width, self._spin_height):
            spin.editingFinished.connect(self._on_edit_finished)
            spin.valueChanged.connect(self._update_derived_labels)

    # ------------------------------------------------------------------
    # Public API (adapter calls)
    # ------------------------------------------------------------------
    def set_room_header(self, room_name: str) -> None:
        self._header.setText(f"Geometry — {room_name}")

    def set_values(
        self,
        *,
        length_m: Optional[float],
        width_m: Optional[float],
        height_m: Optional[float],
    ) -> None:
        self._set_spin(self._spin_length, length_m)
        self._set_spin(self._spin_width, width_m)
        self._set_spin(self._spin_height, height_m)

        self._update_derived_labels()

        self._last_values = self._collect_values()

    def clear(self) -> None:
        self.set_values(
            length_m=0.0,
            width_m=0.0,
            height_m=0.0,
        )
        self._lbl_floor.setText("— m²")
        self._lbl_volume.setText("— m³")
        self._last_values = None

    # ------------------------------------------------------------------
    # Commit logic
    # ------------------------------------------------------------------
    def _on_edit_finished(self) -> None:
        values = self._collect_values()

        if not self._is_valid(values):
            self._set_dirty(True)
            return

        if values == self._last_values:
            return

        self._last_values = values
        self._set_dirty(False)

        self.geometry_committed.emit(values)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _collect_values(self) -> Dict[str, float]:
        return {
            "length_m": float(self._spin_length.value()),
            "width_m": float(self._spin_width.value()),
            "height_m": float(self._spin_height.value()),
        }

    def _is_valid(self, v: Dict[str, float]) -> bool:
        return (
            v["length_m"] > 0
            and v["width_m"] > 0
            and v["height_m"] > 0
        )

    def _update_derived_labels(self) -> None:
        l = self._spin_length.value()
        w = self._spin_width.value()
        h = self._spin_height.value()

        if l > 0 and w > 0:
            self._lbl_floor.setText(f"{l * w:.2f} m²")
        else:
            self._lbl_floor.setText("— m²")

        if l > 0 and w > 0 and h > 0:
            self._lbl_volume.setText(f"{l * w * h:.2f} m³")
        else:
            self._lbl_volume.setText("— m³")

    def _set_spin(self, spin: QDoubleSpinBox, value: Optional[float]) -> None:
        spin.blockSignals(True)
        spin.setValue(float(value) if value is not None else 0.0)
        spin.blockSignals(False)

    def _set_dirty(self, dirty: bool) -> None:
        if dirty:
            self.setStyleSheet("border: 2px solid orange;")
        else:
            self.setStyleSheet("")

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _row(self, label: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addStretch()
        row.addWidget(widget)
        return row

    def _m_spin(self) -> QDoubleSpinBox:
        s = QDoubleSpinBox(self)
        s.setRange(0.0, 1000.0)
        s.setDecimals(2)
        s.setSingleStep(0.10)
        s.setSuffix(" m")
        s.setFixedWidth(90)
        return s