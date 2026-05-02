# ======================================================================
# HVAC/gui_v3/panels/uvp_panel.py
# ======================================================================

"""
HVACgooee — GUI v3
UVP Panel (U-Value & Properties) — Phase V-B (Interactive)

Purpose
-------
• Display selected surface context
• Allow construction selection
• Allow U-value editing (intent only)
• Allow assignment of construction to surface (intent only)

Authority
---------
• NO ProjectState access
• NO calculations
• NO persistence

This panel emits intent signals only.
External controllers/adapters handle all mutations.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QSpacerItem,
    QSizePolicy,
    QListWidget,
    QDoubleSpinBox,
    QPushButton,
)
from PySide6.QtWidgets import QListWidgetItem

# ======================================================================
# UVPPanel
# ======================================================================

class UVPPanel(QWidget):
    """
    GUI v3 — U-Values Panel (Observer + Intent)

    Emits:
    • construction_selected(cid)
    • u_value_changed(cid, value)
    • assign_requested(surface_id, cid)
    """

    # ------------------------------------------------------------------
    # Signals (INTENT ONLY)
    # ------------------------------------------------------------------
    construction_selected = Signal(str)        # construction_id
    u_value_changed = Signal(str, float)       # cid, new_u
    assign_requested = Signal(str, str)        # surface_id, construction_id

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, context, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._context = context  # 🔥 THIS FIXES YOUR CRASH

        self._selected_surface_id: str | None = None
        self._selected_cid: str | None = None
        self._construction_list = QListWidget(self)
        self._label_status = QLabel("No surface selected", self)

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

        self._element_label = QLabel("Element: —")
        self._type_label = QLabel("Type: —")

        summary_layout.addWidget(self._element_label)
        summary_layout.addWidget(self._type_label)

        root.addWidget(summary_box)
        root.addWidget(self._label_status)
        # --------------------------------------------------------------
        # Construction selection
        # --------------------------------------------------------------
        root.addWidget(QLabel("Constructions"))

        self._construction_list = QListWidget()
        self._construction_list.currentItemChanged.connect(
            self._on_construction_selected
        )

        root.addWidget(self._construction_list)

        # --------------------------------------------------------------
        # Thermal Properties
        # --------------------------------------------------------------
        thermal_box = QGroupBox("Thermal Properties")
        thermal_layout = QVBoxLayout(thermal_box)

        self._u_label = QLabel("U-Value (W/m²·K): —")
        self._r_label = QLabel("R-Value (m²·K/W): —")
        self._cap_label = QLabel("Heat Capacity: —")

        thermal_layout.addWidget(self._u_label)
        thermal_layout.addWidget(self._r_label)
        thermal_layout.addWidget(self._cap_label)

        root.addWidget(thermal_box)

        # --------------------------------------------------------------
        # U-value editor
        # --------------------------------------------------------------
        root.addWidget(QLabel("Edit U-Value"))

        self._u_spin = QDoubleSpinBox()
        self._u_spin.setRange(0.01, 10.0)
        self._u_spin.setDecimals(3)
        self._u_spin.valueChanged.connect(self._on_u_changed)

        root.addWidget(self._u_spin)

        # --------------------------------------------------------------
        # Assign button
        # --------------------------------------------------------------
        self._assign_btn = QPushButton("Assign to Surface")
        self._assign_btn.clicked.connect(self._on_assign)

        root.addWidget(self._assign_btn)

        # --------------------------------------------------------------
        # Surface indicator
        # --------------------------------------------------------------
        self._surface_label = QLabel("No surface selected")
        root.addWidget(self._surface_label)

        # --------------------------------------------------------------
        # Guidance
        # --------------------------------------------------------------
        notes = QLabel(
            "Construction defines thermal behaviour.\n"
            "U-value is authoritative per construction."
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

    # ------------------------------------------------------------------
    # Public API (called by adapters / main window)
    # ------------------------------------------------------------------

    def set_constructions(self, constructions: dict) -> None:
        self._construction_list.clear()

        for cid, c in constructions.items():
            item = QListWidgetItem(c.name)

            # 🔥 THIS IS THE LINE YOU WERE ASKING ABOUT
            item.setData(Qt.UserRole, cid)

            self._construction_list.addItem(item)

    def set_selected_surface(self, surface_id: str | None) -> None:
        self._selected_surface_id = surface_id

        if not surface_id:
            self._label_status.setText("No surface selected")
            self._label_status.setStyleSheet("color: #888;")
            return

        ps = self._context.project_state

        from HVAC.gui_v3.wizards.construction_wizard import ConstructionWizard

        assigned = ConstructionWizard.get_surface_construction(ps, surface_id)
        default = self._resolve_default_for_surface(surface_id)

        # --------------------------------------------------
        # 🔥 STEP 3 — Status text
        # --------------------------------------------------
        if assigned:
            text = f"✔ Assigned: {assigned}"
        else:
            text = f"Default: {default}"

        self._label_status.setText(text)

        # --------------------------------------------------
        # 🔥 STEP 5 — Visual styling
        # --------------------------------------------------
        if assigned:
            self._label_status.setStyleSheet("color: #2e7d32; font-weight: 600;")
        else:
            self._label_status.setStyleSheet("color: #888;")

        # --------------------------------------------------
        # Existing behaviour (keep this)
        # --------------------------------------------------
        cid = assigned or default
        self._select_construction_in_list(cid)

    def _select_construction_in_list(self, cid: str) -> None:
        list_widget = self._construction_list

        if not cid:
            return

        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.data(Qt.UserRole) == cid:
                list_widget.setCurrentItem(item)
                return

    def highlight_construction(self, cid: str) -> None:
        for i in range(self._construction_list.count()):
            item = self._construction_list.item(i)
            if item.data(Qt.UserRole) == cid:
                self._construction_list.setCurrentItem(item)
                return

    def set_u_value(self, u_value: float | None) -> None:
        if u_value is None:
            return

        self._u_spin.blockSignals(True)
        self._u_spin.setValue(float(u_value))
        self._u_spin.blockSignals(False)

        self._u_label.setText(f"U-Value (W/m²·K): {u_value:.3f}")

        if u_value > 0:
            r = 1.0 / u_value
            self._r_label.setText(f"R-Value (m²·K/W): {r:.3f}")

    def _resolve_default_for_surface(self, surface_id: str) -> str:
        # simple heuristic (v1)
        if "seg" in surface_id:
            return "DEV-WALL"
        if "roof" in surface_id:
            return "DEV-ROOF"
        if "floor" in surface_id:
            return "DEV-FLOOR"
        return "UNKNOWN"

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _on_construction_selected(self, current, _previous):
        if not current:
            return

        cid = current.data(Qt.UserRole)
        if not cid:
            return

        self._selected_cid = cid

        print("UVP SELECT", cid)

        # 🔥 update panel immediately
        ps = self._context.project_state
        c = ps.constructions.get(cid)
        if c:
            self.set_u_value(c.u_value_W_m2K)

        # 🔥 emit intent
        self.construction_selected.emit(cid)

    def _on_u_changed(self, value: float) -> None:
        if self._selected_cid:
            self.u_value_changed.emit(self._selected_cid, float(value))

    def _on_assign(self) -> None:
        if self._selected_surface_id and self._selected_cid:
            self.assign_requested.emit(
                self._selected_surface_id,
                self._selected_cid,
            )

