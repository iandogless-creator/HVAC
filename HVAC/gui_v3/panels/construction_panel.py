# ======================================================================
# HVACgooee — Construction Panel (GUI v3)
# Phase: GUI v3 — Observer
# Sub-Phase: Phase B (Static + Authoring Intent)
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QPushButton,
)


class ConstructionPanel(QWidget):
    """
    Construction Panel (GUI v3)

    Phase B responsibilities:
    • Allow element type selection (authoring intent)
    • Present construction definition placeholder
    • Provide navigation intent to U-Values panel
    • NO calculations
    • NO UV-value derivation
    • NO ProjectState mutation
    """

    # Future: surface selection from worksheet / room context can feed this.
    surface_selected = Signal(str)          # surface_id
    u_values_requested = Signal(object)     # surface_id | None


    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

        # Placeholder state (Phase B only)
        self._has_selection = False
        self._has_layers = False
        self._selected_surface_id: str | None = None

        self._refresh_placeholders()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # --------------------------------------------------------------
        # Element type
        # --------------------------------------------------------------
        element_box = QGroupBox("Element Type")
        element_layout = QVBoxLayout(element_box)

        element_layout.addWidget(QLabel("• Wall"))
        element_layout.addWidget(QLabel("• Roof"))
        element_layout.addWidget(QLabel("• Floor"))
        element_layout.addWidget(QLabel("• Window / Door"))

        root.addWidget(element_box)

        # --------------------------------------------------------------
        # Construction definition
        # --------------------------------------------------------------
        definition_box = QGroupBox("Construction Definition")
        definition_layout = QVBoxLayout(definition_box)

        self._definition_label = QLabel("Select an element to define its construction.")
        self._definition_label.setWordWrap(True)
        definition_layout.addWidget(self._definition_label)

        # --------------------------------------------------------------
        # U-values navigation (Phase B intent only)
        # --------------------------------------------------------------
        self._btn_uvalues = QPushButton("Open U-Values Panel…")
        self._btn_uvalues.setToolTip("Go to U-Values panel to author/inspect U-values.")
        self._btn_uvalues.clicked.connect(self._on_open_uvalues_clicked)
        definition_layout.addWidget(self._btn_uvalues)
        root.addWidget(definition_box)

        # --------------------------------------------------------------
        # Layers
        # --------------------------------------------------------------
        layers_box = QGroupBox("Layers")
        layers_layout = QVBoxLayout(layers_box)

        self._layers_label = QLabel("")
        self._layers_label.setWordWrap(True)

        layers_layout.addWidget(self._layers_label)
        root.addWidget(layers_box)

        # --------------------------------------------------------------
        # Guidance copy (explicit, Phase-B safe)
        # --------------------------------------------------------------
        guidance = QLabel(
            "Construction defines physical build-up only.\n"
            "Thermal properties are derived later (U-Values panel)."
        )
        guidance.setWordWrap(True)

        root.addWidget(guidance)
        root.addStretch()

    # ------------------------------------------------------------------
    # Public: selection (optional now, useful later)
    # ------------------------------------------------------------------
    def set_selected_surface(self, surface_id: str | None) -> None:
        """
        Phase B-safe: accept a selected surface id for navigation convenience.
        """
        self._selected_surface_id = surface_id
        self._has_selection = bool(surface_id)
        self._refresh_placeholders()

    def set_uvalue_missing_hint(self, missing: bool) -> None:
        """
        Optional UI hint: enable the navigation button regardless, but you can
        change label/tooltip later based on missing-U state.
        """
        # Keep always enabled for now (navigation is always valid).
        self._btn_uvalues.setEnabled(True)

    # ------------------------------------------------------------------
    # Intent
    # ------------------------------------------------------------------
    def _on_open_uvalues_clicked(self) -> None:
        # Emit navigation intent (surface_id may be None in Phase B)
        self.u_values_requested.emit(self._selected_surface_id)

    # ------------------------------------------------------------------
    # Placeholder state handling (Phase B)
    # ------------------------------------------------------------------
    def _refresh_placeholders(self) -> None:
        if not self._has_selection:
            self._definition_label.setText("Select an element to define its construction.")
            self._layers_label.setText("No layers defined.\n(Available in Phase C+)")
            return

        if self._has_selection and not self._has_layers:
            self._definition_label.setText("Construction selected.")
            self._layers_label.setText(
                "Construction selected, no layers yet.\n"
                "(Layers will be defined in Phase C+)"
            )
            return


    def open_uvp_requested(self) -> None:
        self.u_values_requested.emit(self._selected_surface_id)