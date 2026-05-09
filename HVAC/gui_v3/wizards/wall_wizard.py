# ======================================================================
# HVAC/gui_v3/wizards/wall_wizard.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QComboBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


# ======================================================================
# Opening Preview DTO
# ======================================================================

# ======================================================================
# Opening Preview DTO
# ======================================================================

@dataclass(frozen=True)
class OpeningPreview:
    opening_type: str
    profile_id: str
    profile_name: str
    width_m: float
    height_m: float
    quantity: int = 1

    @property
    def area_m2(self) -> float:
        return self.width_m * self.height_m * self.quantity

    @property
    def size_label(self) -> str:
        return f"{self.width_m:.2f} × {self.height_m:.2f} m"


# ======================================================================
# Opening Profiles — Wall Wizard E1 preview catalogue
# ======================================================================

OPENING_PROFILES = {
    "SMALL_WINDOW": {
        "name": "Small Window",
        "opening_type": "WINDOW",
        "width_m": 0.60,
        "height_m": 0.90,
        "external_only": True,
    },
    "STANDARD_WINDOW": {
        "name": "Standard Window",
        "opening_type": "WINDOW",
        "width_m": 1.20,
        "height_m": 1.20,
        "external_only": True,
    },
    "LARGE_WINDOW": {
        "name": "Large Window",
        "opening_type": "WINDOW",
        "width_m": 1.80,
        "height_m": 1.20,
        "external_only": True,
    },
    "EXTERNAL_DOOR": {
        "name": "External Door",
        "opening_type": "DOOR",
        "width_m": 0.90,
        "height_m": 2.10,
        "external_only": True,
    },
    "INTERNAL_DOOR": {
        "name": "Internal Door",
        "opening_type": "DOOR",
        "width_m": 0.90,
        "height_m": 2.10,
        "external_only": False,
    },
}


# ======================================================================
# Projection DTO
# ======================================================================

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
    Wall Wizard E1 — room-level opening schedule preview.

    Scope
    -----
    • show selected wall / room context
    • show gross wall area
    • preview grouped opening schedule
    • show opening area and net wall area
    • emit opening intent only

    Explicitly forbidden
    --------------------
    • no ProjectState mutation
    • no U-value writes
    • no heat-loss calculation
    • no opening persistence yet
    """

    opening_requested = Signal(str, object)  # surface_id, OpeningPreview

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Wall Wizard")
        self.setWindowTitle("Wall Wizard")
        self.setMinimumWidth(620)

        self._current_surface_id: str | None = None
        self._current_gross_area_m2: float | None = None
        self._preview_openings: list[OpeningPreview] = []

        root = QVBoxLayout(self)

        title = QLabel("Wall Wizard")
        title.setStyleSheet("font-weight: 700; font-size: 16px;")
        root.addWidget(title)

        # --------------------------------------------------
        # Projection fields
        # --------------------------------------------------
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

        # --------------------------------------------------
        # Opening schedule controls
        # --------------------------------------------------
        opening_title = QLabel("Opening schedule preview")
        opening_title.setStyleSheet("font-weight: 700; margin-top: 8px;")
        root.addWidget(opening_title)

        control_row = QHBoxLayout()

        self._profile_combo = QComboBox()

        self._quantity_spin = QSpinBox()
        self._quantity_spin.setRange(1, 99)
        self._quantity_spin.setValue(1)

        self._add_opening_btn = QPushButton("Add opening")

        control_row.addWidget(QLabel("Profile:"))
        control_row.addWidget(self._profile_combo, 1)
        control_row.addWidget(QLabel("Qty:"))
        control_row.addWidget(self._quantity_spin)
        control_row.addWidget(self._add_opening_btn)

        root.addLayout(control_row)

        # --------------------------------------------------
        # Opening schedule table
        # --------------------------------------------------
        self._opening_table = QTableWidget(0, 4)
        self._opening_table.setHorizontalHeaderLabels(
            ["Profile", "Qty", "Size", "Area"]
        )
        self._opening_table.verticalHeader().setVisible(False)
        self._opening_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._opening_table.setEditTriggers(QTableWidget.NoEditTriggers)

        header = self._opening_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self._opening_table.setMinimumHeight(120)
        root.addWidget(self._opening_table)

        self._opening_hint = QLabel("No openings defined yet.")
        root.addWidget(self._opening_hint)

        self._add_opening_btn.clicked.connect(self._add_selected_opening)

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

        self._update_opening_profile_choices(projection)
        self._refresh_area_summary()

    # ------------------------------------------------------------------
    # Opening intent / preview
    # ------------------------------------------------------------------

    def _add_selected_opening(self) -> None:
        if not self._current_surface_id:
            return

        profile_id = self._profile_combo.currentData()
        if not profile_id:
            return

        profile = OPENING_PROFILES.get(str(profile_id))
        if not profile:
            return

        quantity = int(self._quantity_spin.value())

        opening = OpeningPreview(
            opening_type=str(profile["opening_type"]),
            profile_id=str(profile_id),
            profile_name=str(profile["name"]),
            width_m=float(profile["width_m"]),
            height_m=float(profile["height_m"]),
            quantity=quantity,
        )

        self._preview_openings.append(opening)
        self._refresh_area_summary()

        self.opening_requested.emit(
            self._current_surface_id,
            opening,
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

        self._refresh_opening_table()

        if not self._preview_openings:
            self._opening_hint.setText("No openings defined yet.")
            return

        grouped_count = self._grouped_openings()
        self._opening_hint.setText(
            f"{len(grouped_count)} grouped schedule line(s), "
            f"total opening area {opening_area:.2f} m²."
        )

    def _refresh_opening_table(self) -> None:
        rows = list(self._grouped_openings().values())

        self._opening_table.setRowCount(len(rows))

        for row_index, opening in enumerate(rows):
            self._opening_table.setItem(
                row_index,
                0,
                QTableWidgetItem(opening.profile_name),
            )
            self._opening_table.setItem(
                row_index,
                1,
                QTableWidgetItem(str(opening.quantity)),
            )
            self._opening_table.setItem(
                row_index,
                2,
                QTableWidgetItem(opening.size_label),
            )
            self._opening_table.setItem(
                row_index,
                3,
                QTableWidgetItem(f"{opening.area_m2:.2f} m²"),
            )

    def _grouped_openings(self) -> dict[tuple[str, str, float, float], OpeningPreview]:
        grouped: dict[tuple[str, str, float, float], OpeningPreview] = {}

        for opening in self._preview_openings:
            key = (
                opening.profile_id,
                opening.profile_name,
                opening.width_m,
                opening.height_m,
            )

            existing = grouped.get(key)
            if existing is None:
                grouped[key] = opening
                continue

            grouped[key] = OpeningPreview(
                opening_type=existing.opening_type,
                profile_id=existing.profile_id,
                profile_name=existing.profile_name,
                width_m=existing.width_m,
                height_m=existing.height_m,
                quantity=existing.quantity + opening.quantity,
            )

        return grouped

    def _update_opening_profile_choices(
        self,
        projection: WallWizardProjection,
    ) -> None:
        element_text = (projection.element_label or "").lower()

        is_external_wall = "external wall" in element_text
        is_internal_wall = "internal wall" in element_text
        is_wall = "wall" in element_text

        self._profile_combo.clear()

        if is_external_wall:
            allowed_ids = [
                "SMALL_WINDOW",
                "STANDARD_WINDOW",
                "LARGE_WINDOW",
                "EXTERNAL_DOOR",
            ]
        elif is_internal_wall:
            allowed_ids = [
                "INTERNAL_DOOR",
            ]
        else:
            allowed_ids = []

        for profile_id in allowed_ids:
            profile = OPENING_PROFILES[profile_id]
            label = (
                f'{profile["name"]} '
                f'({float(profile["width_m"]):.2f} × '
                f'{float(profile["height_m"]):.2f} m)'
            )
            self._profile_combo.addItem(label, profile_id)

        enabled = is_wall and bool(allowed_ids)

        self._profile_combo.setEnabled(enabled)
        self._quantity_spin.setEnabled(enabled)
        self._add_opening_btn.setEnabled(enabled)

        if self._preview_openings:
            return

        if is_external_wall:
            self._opening_hint.setText(
                "No room-level external openings defined yet."
            )
        elif is_internal_wall:
            self._opening_hint.setText(
                "No internal door/opening defined yet."
            )
        else:
            self._opening_hint.setText(
                "Openings are only available for wall surfaces."
            )