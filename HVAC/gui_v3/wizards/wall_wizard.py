# ======================================================================
# HVAC/gui_v3/wizards/wall_wizard.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
)
from PySide6.QtCore import Signal

# ======================================================================
# Projection DTO
# ======================================================================

@dataclass(frozen=True)
class WallWizardProjection:
    """
    Read-only projection for Wall Wizard A.

    This is display data only.
    The wizard does not mutate ProjectState.
    """

    surface_id: str
    room_label: str
    element_label: str
    area_m2: Optional[float]
    construction_id: Optional[str]
    construction_name: str
    u_value_W_m2K: Optional[float]


# ======================================================================
# WallWizardDialog
# ======================================================================


class WallWizardDialog(QDialog):
    """
    Wall Wizard A — read-only shell.

    Scope
    -----
    • show selected wall surface
    • show room / element / area
    • show assigned construction
    • show construction U-value
    • placeholder for future openings

    Explicitly forbidden
    --------------------
    • no ProjectState mutation
    • no U-value writes
    • no heat-loss calculation
    • no opening creation yet
    """
    opening_requested = Signal(str, str)  # surface_id, opening_typeA
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Wall Wizard")
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)

        title = QLabel("Wall Wizard")
        title.setStyleSheet("font-weight: 700; font-size: 16px;")
        root.addWidget(title)

        self._surface_id = QLabel("—")
        self._room = QLabel("—")
        self._element = QLabel("—")
        self._area = QLabel("—")
        self._construction_id = QLabel("—")
        self._construction_name = QLabel("—")
        self._u_value = QLabel("—")
        self._openings = QLabel("Openings: not implemented yet")

        form = QFormLayout()
        form.addRow("Surface ID:", self._surface_id)
        form.addRow("Room:", self._room)
        form.addRow("Element:", self._element)
        form.addRow("Gross area:", self._area)
        form.addRow("Construction ID:", self._construction_id)
        form.addRow("Construction:", self._construction_name)
        form.addRow("U-value:", self._u_value)
        form.addRow("Openings:", self._openings)

        root.addLayout(form)
        self._current_surface_id: str | None = None
        # --------------------------------------------------
        # Opening intent buttons
        # --------------------------------------------------
        opening_title = QLabel("Opening options")
        opening_title.setStyleSheet("font-weight: 700; margin-top: 8px;")
        root.addWidget(opening_title)

        opening_row = QHBoxLayout()

        self._add_window_btn = QPushButton("Add Window…")
        self._add_door_btn = QPushButton("Add Door…")

        self._add_window_btn.clicked.connect(
            lambda: self._emit_opening_requested("WINDOW")
        )
        self._add_door_btn.clicked.connect(
            lambda: self._emit_opening_requested("DOOR")
        )

        opening_row.addWidget(self._add_window_btn)
        opening_row.addWidget(self._add_door_btn)

        root.addLayout(opening_row)

        self._opening_hint = QLabel("No openings defined yet.")
        root.addWidget(self._opening_hint)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        root.addWidget(close_btn)

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def set_projection(self, projection: WallWizardProjection) -> None:
        self._current_surface_id = projection.surface_id
        self._surface_id.setText(projection.surface_id or "—")
        self._room.setText(projection.room_label or "—")
        self._element.setText(projection.element_label or "—")

        if projection.area_m2 is None:
            self._area.setText("—")
        else:
            self._area.setText(f"{projection.area_m2:.2f} m²")

        self._construction_id.setText(projection.construction_id or "—")
        self._construction_name.setText(projection.construction_name or "—")

        if projection.u_value_W_m2K is None:
            self._u_value.setText("—")
        else:
            self._u_value.setText(f"{projection.u_value_W_m2K:.3f} W/m²·K")

        self._update_opening_buttons(projection)

    # ------------------------------------------------------------------
    # Opening intent
    # ------------------------------------------------------------------

    def _emit_opening_requested(self, opening_type: str) -> None:
        if not self._current_surface_id:
            return

        self.opening_requested.emit(
            self._current_surface_id,
            opening_type,
        )

    def _update_opening_buttons(self, projection: WallWizardProjection) -> None:
        element_text = (projection.element_label or "").lower()

        is_external_wall = "external wall" in element_text
        is_internal_wall = "internal wall" in element_text
        is_wall = "wall" in element_text

        # Wall Wizard A/B only supports wall surfaces.
        self._add_window_btn.setEnabled(is_external_wall)
        self._add_door_btn.setEnabled(is_wall)

        if is_external_wall:
            self._opening_hint.setText(
                "No openings defined yet. Window and door options are available."
            )
        elif is_internal_wall:
            self._opening_hint.setText(
                "No openings defined yet. Internal wall supports door/opening intent only."
            )
        else:
            self._opening_hint.setText(
                "Openings are only available for wall surfaces."
            )