# ======================================================================
# HVAC/gui_v3/panels/geometry_mini_panel.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QHBoxLayout,
    QFormLayout,
    QLineEdit
)


class GeometryMiniPanel(QWidget):

    geometry_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QFormLayout(self)

        self._edit_length = QLineEdit()
        self._edit_width = QLineEdit()
        self._edit_height = QLineEdit()
        self._edit_ext = QLineEdit()
        self._edit_ti = QLineEdit()

        layout.addRow("Length (m)", self._edit_length)
        layout.addRow("Width (m)", self._edit_width)
        layout.addRow("Height (m)", self._edit_height)
        layout.addRow("External wall length (m)", self._edit_ext)
        layout.addRow("Ti (°C)", self._edit_ti)
        self._commit_timer = QTimer(self)
        self._commit_timer.setSingleShot(True)
        self._commit_timer.timeout.connect(self._maybe_commit)

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

        self._edit_length.editingFinished.connect(self._schedule_commit)
        self._edit_width.editingFinished.connect(self._schedule_commit)
        self._edit_height.editingFinished.connect(self._schedule_commit)
        self._edit_ext.editingFinished.connect(self._schedule_commit)
        self._edit_ti.editingFinished.connect(self._schedule_commit)


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

    # ------------------------------------------------------------------
    # Commit API (called by MainWindow / adapters)
    # ------------------------------------------------------------------
    def commit_if_valid(self) -> None:
        self._maybe_commit()

    def _schedule_commit(self):
        # restart timer every time
        self._commit_timer.start(150)

    # ------------------------------------------------------------------
    # Internal commit logic
    # ------------------------------------------------------------------
    def _maybe_commit(self) -> None:

        values = self._collect_values()

        # Only commit when FULL geometry is valid
        if not self._is_valid(values):
            self._set_dirty(True)
            return

        # Prevent duplicate commits
        if getattr(self, "_last_commit", None) == values:
            return

        self._last_commit = values

        self._set_dirty(False)

        print("GMP commit fired")

        self.geometry_committed.emit(values)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _collect_values(self) -> dict:

        return {
            "length_m": self._length_input.value(),
            "width_m": self._width_input.value(),
            "height_m": self._height_input.value(),
            "external_wall_length_m": self._external_wall_length_input.value(),
            "internal_temp_C": self._ti_input.value(),
        }

    def _is_valid(self, v: dict) -> bool:

        return (
                v["length_m"] > 0 and
                v["width_m"] > 0 and
                v["height_m"] > 0 and
                v["external_wall_length_m"] >= 0
        )

    def _set_dirty(self, dirty: bool):
        if dirty:
            self.setStyleSheet("border: 2px solid orange;")
        else:
            self.setStyleSheet("")