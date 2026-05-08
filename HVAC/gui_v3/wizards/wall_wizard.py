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
)


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

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        root.addWidget(close_btn)

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def set_projection(self, projection: WallWizardProjection) -> None:
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