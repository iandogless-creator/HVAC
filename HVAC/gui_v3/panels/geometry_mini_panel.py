# ======================================================================
# HVAC/gui_v3/adapters/geometry_mini_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from PySide6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QHBoxLayout,
    QWidget,
)


class GeometryMiniPanel(QWidget):

    geometry_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
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

        # Emit intent when anything changes
        for w in (
            self._spin_length,
            self._spin_width,
            self._spin_height,
            self._spin_ti,
        ):
            w.valueChanged.connect(self._emit_geometry_changed)
    # ------------------------------------------------------------------
    # Intent emission
    # ------------------------------------------------------------------

    def _emit_geometry_changed(self) -> None:
        """
        Emit internal geometry intent (Phase I-B).

        Pure intent only:
        • length, width, height
        • internal design temperature (Ti)
        """

        intent = {
            "length_m": self._spin_length.value(),
            "width_m": self._spin_width.value(),
            "height_m": self._spin_height.value(),
            "ti_c": self._spin_ti.value(),
        }

        self.geometry_changed.emit(intent)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _row(self, label: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addStretch(1)
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


    # ------------------------------------------------------------------
    # GUI → Project intent
    # ------------------------------------------------------------------
    def _on_geometry_changed(self, payload: dict[str, Any]) -> None:
        """
        Receive geometry edits from GUI and write intent to ProjectState.
        """
        ps = self._context.project_state
        room_id = self._context.current_room_id

        if not ps or not room_id:
            return

        room = ps.rooms.get(room_id)
        if not room:
            return

        # Normalise + store intent
        room.geometry_intent = {
            "length_m": float(payload["length_m"]),
            "width_m": float(payload["width_m"]),
            "height_m": float(payload["height_m"]),
            "ti_c": float(payload["ti_c"]),
            "ach": float(payload["ach"]),
        }

        # Geometry changes invalidate heat-loss results
        if hasattr(ps, "mark_heatloss_dirty"):
            ps.mark_heatloss_dirty()

        # Force observers (HL panel, etc.) to update
        if hasattr(self._context, "refresh_all_adapters"):
            self._context.refresh_all_adapters()

    def _emit_geometry(self) -> None:
        payload = {"length_m": self._spin_length.value(),
                "width_m": self._spin_width.value(),
                "height_m": self._spin_height.value(),
                "ti_c": self._spin_ti.value(),
            }

        self.geometry_changed.emit(payload)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def clear(self) -> None:
        """
        Clear all geometry presentation fields.

        Phase I-B:
        - No defaults injected
        - No authority
        - Pure presentation reset
        """

        self._spin_length.setValue(0.0)
        self._spin_width.setValue(0.0)
        self._spin_height.setValue(0.0)
        self._spin_ti.setValue(0.0)

        # Derived (read-only labels)
        self._lbl_floor_area.setText("—")
        self._lbl_volume.setText("—")
