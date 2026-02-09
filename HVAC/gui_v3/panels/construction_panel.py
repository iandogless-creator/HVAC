# ======================================================================
# HVACgooee — Construction Panel (GUI v3)
# Phase: GUI v3 — Observer
# Sub-Phase: Phase B (Static + Authoring Intent)
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
)


class ConstructionPanel(QWidget):
    """
    Construction Panel (GUI v3)

    Phase B responsibilities:
    • Allow element type selection (authoring intent)
    • Present construction definition placeholder
    • NO calculations
    • NO UV-value derivation
    • NO ProjectState mutation
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

        # Placeholder state (Phase B only)
        self._has_selection = False
        self._has_layers = False

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

        self._definition_label = QLabel(
            "Select an element to define its construction."
        )
        self._definition_label.setWordWrap(True)

        definition_layout.addWidget(self._definition_label)
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
    # Placeholder state handling (Phase B)
    # ------------------------------------------------------------------
    def _refresh_placeholders(self) -> None:
        if not self._has_selection:
            self._definition_label.setText(
                "Select an element to define its construction."
            )
            self._layers_label.setText(
                "No layers defined.\n(Available in Phase C+)"
            )
            return

        # Element selected, but no layers yet
        if self._has_selection and not self._has_layers:
            self._definition_label.setText(
                "Construction selected."
            )
            self._layers_label.setText(
                "Construction selected, no layers yet.\n"
                "(Layers will be defined in Phase C+)"
            )
            return
