# ======================================================================
# HVAC/gui_v3/wizards/wall_wizard.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
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
class OpeningPreview:
    opening_type: str
    width_m: float
    height_m: float

    @property
    def area_m2(self) -> float:
        return self.width_m * self.height_m

@dataclass(frozen=True)
class WallWizardProjection:
    """
    Read-only projection for Wall Wizard.

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
    openings: list[OpeningPreview] = field(default_factory=list)

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

        self._current_surface_id: str | None = None
        self._current_gross_area_m2: float | None = None
        self._preview_openings: list[OpeningPreview] = []

        root = QVBoxLayout(self)

        self._surface_id = QLabel("—")
        self._room = QLabel("—")
        self._element = QLabel("—")

        self._gross_area = QLabel("—")
        self._opening_area = QLabel("0.00 m²")
        self._net_area = QLabel("—")

        self._construction_id = QLabel("—")
        self._construction_name = QLabel("—")
        self._u_value = QLabel("—")

        form = QFormLayout()
        form.addRow("Surface ID:", self._surface_id)
        form.addRow("Room:", self._room)
        form.addRow("Element:", self._element)
        form.addRow("Gross wall area:", self._gross_area)
        form.addRow("Opening area:", self._opening_area)
        form.addRow("Net wall area:", self._net_area)
        form.addRow("Construction ID:", self._construction_id)
        form.addRow("Construction:", self._construction_name)
        form.addRow("U-value:", self._u_value)
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
        self._current_gross_area_m2 = projection.area_m2
        self._preview_openings = list(projection.openings)

        self._surface_id.setText(projection.surface_id or "—")
        self._room.setText(projection.room_label or "—")
        self._element.setText(projection.element_label or "—")

        if projection.area_m2 is None:
            self._gross_area.setText("—")
        else:
            self._gross_area.setText(f"{projection.area_m2:.2f} m²")

        self._construction_id.setText(projection.construction_id or "—")
        self._construction_name.setText(projection.construction_name or "—")

        if projection.u_value_W_m2K is None:
            self._u_value.setText("—")
        else:
            self._u_value.setText(f"{projection.u_value_W_m2K:.3f} W/m²·K")

        self._refresh_area_summary()
        self._update_opening_buttons(projection)

    # ------------------------------------------------------------------
    # Opening intent / preview
    # ------------------------------------------------------------------

    def _emit_opening_requested(self, opening_type: str) -> None:
        if not self._current_surface_id:
            return

        # Wall-Wizard C1: temporary preview only.
        # No ProjectState mutation.
        if opening_type == "WINDOW":
            self._preview_openings.append(
                OpeningPreview(
                    opening_type="WINDOW",
                    width_m=1.20,
                    height_m=1.20,
                )
            )
        elif opening_type == "DOOR":
            self._preview_openings.append(
                OpeningPreview(
                    opening_type="DOOR",
                    width_m=0.90,
                    height_m=2.10,
                )
            )

        self._refresh_area_summary()

        self.opening_requested.emit(
            self._current_surface_id,
            opening_type,
        )

    def _refresh_area_summary(self) -> None:
        gross = self._current_gross_area_m2
        opening_area = sum(o.area_m2 for o in self._preview_openings)

        self._opening_area.setText(f"{opening_area:.2f} m²")

        if gross is None:
            self._net_area.setText("—")
        else:
            net = max(gross - opening_area, 0.0)
            self._net_area.setText(f"{net:.2f} m²")

        if not self._preview_openings:
            self._opening_hint.setText("No openings defined yet.")
            return

        parts = [
            f"{o.opening_type.title()} "
            f"{o.width_m:.2f} × {o.height_m:.2f} = {o.area_m2:.2f} m²"
            for o in self._preview_openings
        ]

        self._opening_hint.setText(
            "Preview openings: " + "; ".join(parts)
        )

    def _update_opening_buttons(self, projection: WallWizardProjection) -> None:
        element_text = (projection.element_label or "").lower()

        is_external_wall = "external wall" in element_text
        is_internal_wall = "internal wall" in element_text
        is_wall = "wall" in element_text

        self._add_window_btn.setEnabled(is_external_wall)
        self._add_door_btn.setEnabled(is_wall)

        if self._preview_openings:
            return

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
