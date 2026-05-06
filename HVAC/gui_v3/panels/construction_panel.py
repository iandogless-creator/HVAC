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
    QComboBox,
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
    u_values_requested = Signal(object)     # surface_id | None
    construction_assign_requested = Signal(str)   # construction_id
    construction_selection_changed = Signal(str)  # construction_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

        # Placeholder state (Phase B only)
        self._has_selection = False
        # Phase B: layers not implemented yet
        self._has_layers = False
        self._selected_surface_id: str | None = None
        self._selected_construction_id: str | None = None
        self._selected_construction_name: str | None = None
        self._selected_u_value: float | None = None
        self._usage_count: int = 0
        self._construction_library: dict[str, dict[str, list[tuple[str, str]]]] = {}
        self._suppress_combo_signals: bool = False
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
        selector_box = QGroupBox("Construction Selector")
        selector_layout = QVBoxLayout(selector_box)

        selector_layout.addWidget(QLabel("Element Type"))
        self._element_combo = QComboBox(self)
        selector_layout.addWidget(self._element_combo)

        selector_layout.addWidget(QLabel("Category"))
        self._category_combo = QComboBox(self)
        selector_layout.addWidget(self._category_combo)

        selector_layout.addWidget(QLabel("Construction"))
        self._construction_combo = QComboBox(self)
        selector_layout.addWidget(self._construction_combo)

        self._btn_assign = QPushButton("Assign to selected surface", self)
        self._btn_assign.setToolTip(
            "Assign the selected construction to the currently focused HLP surface."
        )
        selector_layout.addWidget(self._btn_assign)

        self._element_combo.currentTextChanged.connect(self._on_element_changed)
        self._category_combo.currentTextChanged.connect(self._on_category_changed)
        self._construction_combo.currentIndexChanged.connect(
            self._on_construction_combo_changed
        )
        self._btn_assign.clicked.connect(self._on_assign_clicked)

        root.addWidget(selector_box)

        # --------------------------------------------------------------
        # Construction definition
        # --------------------------------------------------------------
        definition_box = QGroupBox("Construction Definition")
        definition_layout = QVBoxLayout(definition_box)
        self._usage_label = QLabel("Used by: 0 surfaces", self)
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

    def set_construction_library(
        self,
        library: dict[str, dict[str, list[tuple[str, str]]]],
    ) -> None:
        """
        Set available construction choices.

        Shape:
            {
                "Wall": {
                    "External Wall": [("DEV-EXT-WALL", "External Wall")],
                }
            }
        """

        self._construction_library = library or {}

        self._suppress_combo_signals = True
        try:
            self._element_combo.clear()
            self._element_combo.addItems(sorted(self._construction_library.keys()))

            self._populate_categories()
            self._populate_constructions()
        finally:
            self._suppress_combo_signals = False

    def set_selected_construction_id(self, construction_id: str | None) -> None:
        if not construction_id:
            return

        for element, categories in self._construction_library.items():
            for category, items in categories.items():
                for cid, _label in items:
                    if cid == construction_id:
                        self._suppress_combo_signals = True
                        try:
                            self._element_combo.setCurrentText(element)
                            self._populate_categories()
                            self._category_combo.setCurrentText(category)
                            self._populate_constructions()

                            index = self._construction_combo.findData(construction_id)
                            if index >= 0:
                                self._construction_combo.setCurrentIndex(index)
                        finally:
                            self._suppress_combo_signals = False
                        return

    def get_selected_construction_id(self) -> str | None:
        cid = self._construction_combo.currentData()
        return str(cid) if cid else None

    def set_selected_surface(self, surface_id: str | None) -> None:
        """
        Project the currently focused HLP surface into the Construction panel.
        """

        self._selected_surface_id = surface_id

        if self._selected_construction_id:
            self.set_focused_construction(
                construction_id=self._selected_construction_id,
                name=self._selected_construction_name,
                u_value_W_m2K=self._selected_u_value,
                usage_count=self._usage_count,
            )
            return

        self._refresh_placeholders()

    def _populate_categories(self) -> None:
        element = self._element_combo.currentText()
        categories = self._construction_library.get(element, {})

        self._category_combo.clear()
        self._category_combo.addItems(sorted(categories.keys()))

    def _populate_constructions(self) -> None:
        element = self._element_combo.currentText()
        category = self._category_combo.currentText()

        items = (
            self._construction_library
            .get(element, {})
            .get(category, [])
        )

        self._construction_combo.clear()

        for cid, label in items:
            self._construction_combo.addItem(label, cid)

    def _on_element_changed(self, _text: str) -> None:
        if self._suppress_combo_signals:
            return

        self._suppress_combo_signals = True
        try:
            self._populate_categories()
            self._populate_constructions()
        finally:
            self._suppress_combo_signals = False

    def _on_category_changed(self, _text: str) -> None:
        if self._suppress_combo_signals:
            return

        self._suppress_combo_signals = True
        try:
            self._populate_constructions()
        finally:
            self._suppress_combo_signals = False

    def _on_construction_combo_changed(self, _index: int) -> None:
        if self._suppress_combo_signals:
            return

        cid = self.get_selected_construction_id()
        if cid:
            self.construction_selection_changed.emit(cid)

    def _on_assign_clicked(self) -> None:
        cid = self.get_selected_construction_id()
        if cid:
            self.construction_assign_requested.emit(cid)

    # ------------------------------------------------------------------
    # Placeholder state handling (Phase B)
    # ------------------------------------------------------------------
    def _refresh_placeholders(self) -> None:
        surface_id = getattr(self, "_selected_surface_id", None)

        if self._selected_construction_id:
            return

        if not surface_id:
            self._definition_label.setText(
                "Surface: None\n"
                "No surface selected."
            )
            self._layers_label.setText("No layers defined.\n(Available in Phase C+)")
            return

        self._definition_label.setText(
            f"Surface: {surface_id}\n"
            "No construction selected."
        )
        self._layers_label.setText("No layers defined.\n(Available in Phase C+)")

    def set_focused_construction(
            self,
            *,
            construction_id: str | None,
            name: str | None,
            u_value_W_m2K: float | None,
            usage_count: int = 0,
    ) -> None:
        """
        Display the currently focused construction.

        Projection only:
        • Does not mutate ProjectState
        • Does not calculate
        """

        self._selected_construction_id = construction_id
        self._selected_construction_name = name
        self._selected_u_value = u_value_W_m2K
        self._usage_count = usage_count

        self._has_selection = bool(construction_id)

        if not construction_id:
            self._definition_label.setText(
                f"Surface: {self._selected_surface_id or 'None'}\n"
                "No construction selected."
            )
            self._layers_label.setText("No layers defined.\n(Available in Phase C+)")
            return

        u_text = (
            f"{float(u_value_W_m2K):.3f} W/m²·K"
            if isinstance(u_value_W_m2K, (int, float))
            else "—"
        )

        surface_id = getattr(self, "_selected_surface_id", None)

        self._definition_label.setText(
            f"Surface: {surface_id or 'None'}\n"
            f"Construction: {name}\n"
            f"CID: {construction_id}\n"
            f"U-value: {u_text}\n"
            f"Used by: {usage_count} surfaces"
        )

        self._layers_label.setText(
            "No layers defined.\n"
            "Using project construction-library U-value."
        )