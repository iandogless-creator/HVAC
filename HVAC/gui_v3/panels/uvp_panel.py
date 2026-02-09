# ======================================================================
# HVAC/gui_v3/panels/uvp_panel.py
# ======================================================================

"""
HVACgooee — GUI v3
UVP Panel (U-Value & Properties) — Phase B (Static Layout)

BOOTSTRAP LOCK (Phase B)
-----------------------
Purpose
- Dockable panel displaying thermal property placeholders.
- Visual scaffold only. No data. No authority.

Explicitly Forbidden
- Importing ProjectState
- Importing construction or U-value engines
- Calculations
- Persistence
- Signals outward
- Public setters/getters

DONE (Phase B)
- Stable layout
- Clean docking / floating
- Survives hide/show and repack
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt


class UVPPanel(QWidget):
    """
    GUI v3 — UVP Panel (Observer)

    Phase B:
    - Static layout only
    - No data
    - No authority
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self.setMinimumWidth(300)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # --------------------------------------------------------------
        # Element Summary
        # --------------------------------------------------------------
        summary_box = QGroupBox("Element Summary")
        summary_layout = QVBoxLayout(summary_box)

        summary_layout.addWidget(QLabel("Element: —"))
        summary_layout.addWidget(QLabel("Type: —"))

        root.addWidget(summary_box)

        # --------------------------------------------------------------
        # Thermal Properties
        # --------------------------------------------------------------
        thermal_box = QGroupBox("Thermal Properties")
        thermal_layout = QVBoxLayout(thermal_box)

        thermal_layout.addWidget(QLabel("U-Value (W/m²·K): —"))
        thermal_layout.addWidget(QLabel("R-Value (m²·K/W): —"))
        thermal_layout.addWidget(QLabel("Heat Capacity: —"))

        root.addWidget(thermal_box)

        # --------------------------------------------------------------
        # Area Split
        # --------------------------------------------------------------
        area_box = QGroupBox("Area Split")
        area_layout = QVBoxLayout(area_box)

        area_layout.addWidget(QLabel("Gross area: —"))
        area_layout.addWidget(QLabel("Openings: —"))
        area_layout.addWidget(QLabel("Net area: —"))

        root.addWidget(area_box)

        # --------------------------------------------------------------
        # Notes / Guidance
        # --------------------------------------------------------------
        notes = QLabel(
            "Thermal properties are derived from construction definitions.\n"
            "Values become authoritative once resolved."
        )
        notes.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        notes.setWordWrap(True)

        root.addWidget(notes)

        # Spacer
        root.addItem(
            QSpacerItem(
                20,
                40,
                QSizePolicy.Minimum,
                QSizePolicy.Expanding,
            )
        )
