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
    QComboBox,
    QScrollArea,
    QAbstractScrollArea,
    QCheckBox,
    QLineEdit,
    QFormLayout,
)
from PySide6.QtWidgets import QListWidgetItem

from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    build_u_value_teaching_models_v1,
    teaching_model_by_id_v1,
)
from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
)
from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
)
from HVAC.constructions.physics.u_value_method_comparison_acceptance_v1 import (
    NOT_SET_U_VALUE_METHOD,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    DECLARED_RESISTANCE_LAYER_BASIS,
    HOMOGENEOUS_LAYER_BASIS,
    ISOTROPIC_MATERIAL_DIRECTION,
    PARALLEL_MATERIAL_DIRECTION,
    PERPENDICULAR_MATERIAL_DIRECTION,
    UNSPECIFIED_MATERIAL_DIRECTION,
)
from HVAC.gui_v3.widgets.construction_layer_path_schematic_widget_v1 import (
    ConstructionLayerPathSchematicWidgetV1,
)

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
    construction_model_save_requested = Signal(str, str, object)

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
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        page_scroll = QScrollArea(self)
        page_scroll.setObjectName("uValuePanelOuterScroll")
        page_scroll.setWidgetResizable(True)
        page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        page_scroll.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        page_content = QWidget(page_scroll)
        page_content.setObjectName("uValuePanelScrollContent")
        root = QVBoxLayout(page_content)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)
        page_scroll.setWidget(page_content)
        outer.addWidget(page_scroll)
        self._panel_scroll = page_scroll
        self._panel_scroll_content = page_content

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
        # Candidate-only layer/path teaching schematic
        # --------------------------------------------------------------
        self._teaching_toggle = QPushButton(
            "Show layer/path modeller",
            self,
        )
        self._teaching_toggle.setObjectName(
            "uValueTeachingWorkspaceToggle"
        )
        self._teaching_toggle.setCheckable(True)
        self._teaching_toggle.setChecked(False)
        root.addWidget(self._teaching_toggle)

        teaching_box = QGroupBox("Layer / Path Teaching Models")
        teaching_box.setObjectName("uValueTeachingModelsGroup")
        self._teaching_box = teaching_box
        teaching_layout = QVBoxLayout(teaching_box)

        teaching_note = QLabel(
            "Explore one-, two- and three-path constructions. Dragging "
            "changes only this teaching candidate; the accepted U-value "
            "and assigned construction remain unchanged."
        )
        teaching_note.setWordWrap(True)
        teaching_layout.addWidget(teaching_note)

        self._teaching_model_combo = QComboBox(teaching_box)
        self._teaching_model_combo.setObjectName("uValueTeachingModelSelector")
        for model in build_u_value_teaching_models_v1():
            self._teaching_model_combo.addItem(model.label, model.model_id)
        teaching_layout.addWidget(self._teaching_model_combo)

        self._teaching_model_description = QLabel(teaching_box)
        self._teaching_model_description.setObjectName(
            "uValueTeachingModelDescription"
        )
        self._teaching_model_description.setWordWrap(True)
        teaching_layout.addWidget(self._teaching_model_description)

        self._teaching_schematic = ConstructionLayerPathSchematicWidgetV1(
            teaching_box
        )
        teaching_scroll = QScrollArea(teaching_box)
        teaching_scroll.setObjectName("uValueTeachingSchematicScroll")
        teaching_scroll.setWidgetResizable(False)
        teaching_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        teaching_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        teaching_scroll.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        teaching_scroll.setMinimumHeight(150)
        teaching_scroll.setWidget(self._teaching_schematic)
        self._teaching_scroll = teaching_scroll
        teaching_layout.addWidget(teaching_scroll)

        self._teaching_property_toggle = QPushButton(
            "Edit focused layer/path properties…",
            teaching_box,
        )
        self._teaching_property_toggle.setObjectName(
            "uValueTeachingPropertyEditorToggle"
        )
        self._teaching_property_toggle.setCheckable(True)
        teaching_layout.addWidget(self._teaching_property_toggle)

        property_box = QGroupBox(
            "Focused Candidate Layer / Path Properties",
            teaching_box,
        )
        property_box.setObjectName("uValueTeachingPropertyEditorGroup")
        self._teaching_property_box = property_box
        property_layout = QVBoxLayout(property_box)
        property_note = QLabel(
            "Select a layer token or path heading. Changes affect only the "
            "candidate until Save as construction model. Historical catalogue "
            "lookup follows in U-S5C1.",
            property_box,
        )
        property_note.setWordWrap(True)
        property_layout.addWidget(property_note)

        self._teaching_property_target = QComboBox(property_box)
        self._teaching_property_target.setObjectName(
            "uValueTeachingPropertyTarget"
        )
        property_layout.addWidget(self._teaching_property_target)

        property_scroll = QScrollArea(property_box)
        property_scroll.setObjectName("uValueTeachingPropertyEditorScroll")
        property_scroll.setWidgetResizable(True)
        property_scroll.setMinimumHeight(210)
        property_scroll.setMaximumHeight(300)
        property_scroll_content = QWidget(property_scroll)
        property_editor_layout = QVBoxLayout(property_scroll_content)
        property_editor_layout.setContentsMargins(4, 4, 4, 4)
        self._teaching_property_scroll = property_scroll

        self._teaching_layer_editor = QGroupBox("Layer properties", property_box)
        layer_form = QFormLayout(self._teaching_layer_editor)
        self._layer_included_check = QCheckBox(
            "Include this layer in the candidate calculation",
            self._teaching_layer_editor,
        )
        self._layer_label_edit = QLineEdit(self._teaching_layer_editor)
        self._layer_basis_combo = QComboBox(self._teaching_layer_editor)
        self._layer_basis_combo.addItem(
            "Thickness ÷ conductivity",
            HOMOGENEOUS_LAYER_BASIS,
        )
        self._layer_basis_combo.addItem(
            "Declared resistance",
            DECLARED_RESISTANCE_LAYER_BASIS,
        )
        self._layer_thickness_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "Thickness in millimetres",
        )
        self._layer_conductivity_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "λ in W/mK",
        )
        self._layer_declared_r_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "Declared R in m²K/W",
        )
        self._layer_density_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "Density in kg/m³",
        )
        self._layer_specific_heat_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "Specific heat in J/kgK",
        )
        self._layer_vapour_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "Vapour resistivity in MN·s/(g·m)",
        )
        self._layer_emissivity_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "Surface emissivity, 0–1",
        )
        self._layer_absorptivity_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "Solar absorptivity, 0–1",
        )
        self._layer_direction_combo = QComboBox(self._teaching_layer_editor)
        self._layer_direction_combo.addItem(
            "Not specified", UNSPECIFIED_MATERIAL_DIRECTION
        )
        self._layer_direction_combo.addItem(
            "Isotropic", ISOTROPIC_MATERIAL_DIRECTION
        )
        self._layer_direction_combo.addItem(
            "Parallel to grain/structure", PARALLEL_MATERIAL_DIRECTION
        )
        self._layer_direction_combo.addItem(
            "Perpendicular to grain/structure",
            PERPENDICULAR_MATERIAL_DIRECTION,
        )
        self._layer_temperature_edit = _optional_property_edit(
            self._teaching_layer_editor,
            "Property/test temperature in °C",
        )
        self._layer_moisture_edit = QLineEdit(self._teaching_layer_editor)
        self._layer_source_combo = QComboBox(self._teaching_layer_editor)
        for source_label, source_kind in (
            ("Manual / user entry", "user_entry"),
            ("Teaching model", "teaching_model"),
            ("IHVE Guide A3 — 1972", "ihve_a3_1972"),
            ("CIBSE Guide A3 — 1980", "cibse_a3_1980"),
            ("Manufacturer declared value", "manufacturer_declared"),
            ("Test certificate / report", "test_report"),
            ("Other published source", "other_published"),
        ):
            self._layer_source_combo.addItem(source_label, source_kind)
        self._layer_source_ref_edit = QLineEdit(self._teaching_layer_editor)
        self._layer_source_version_edit = QLineEdit(self._teaching_layer_editor)
        self._layer_notes_edit = QLineEdit(self._teaching_layer_editor)
        layer_form.addRow("Included", self._layer_included_check)
        layer_form.addRow("Material name", self._layer_label_edit)
        layer_form.addRow("Resistance basis", self._layer_basis_combo)
        layer_form.addRow("Thickness (mm)", self._layer_thickness_edit)
        layer_form.addRow("Conductivity λ (W/mK)", self._layer_conductivity_edit)
        layer_form.addRow("Declared R (m²K/W)", self._layer_declared_r_edit)
        layer_form.addRow("Density (kg/m³)", self._layer_density_edit)
        layer_form.addRow(
            "Specific heat (J/kgK)", self._layer_specific_heat_edit
        )
        layer_form.addRow(
            "Vapour resistivity", self._layer_vapour_edit
        )
        layer_form.addRow("Surface emissivity", self._layer_emissivity_edit)
        layer_form.addRow("Solar absorptivity", self._layer_absorptivity_edit)
        layer_form.addRow("Material direction", self._layer_direction_combo)
        layer_form.addRow("Property temperature (°C)", self._layer_temperature_edit)
        layer_form.addRow("Moisture condition", self._layer_moisture_edit)
        layer_form.addRow("Property source", self._layer_source_combo)
        layer_form.addRow("Source reference", self._layer_source_ref_edit)
        layer_form.addRow("Edition / version", self._layer_source_version_edit)
        layer_form.addRow("Notes", self._layer_notes_edit)
        self._teaching_layer_apply = QPushButton(
            "Apply focused layer properties",
            self._teaching_layer_editor,
        )
        self._teaching_layer_apply.setObjectName(
            "uValueTeachingApplyLayerProperties"
        )
        layer_form.addRow(self._teaching_layer_apply)
        property_editor_layout.addWidget(self._teaching_layer_editor)

        self._teaching_path_editor = QGroupBox("Path properties", property_box)
        path_form = QFormLayout(self._teaching_path_editor)
        self._path_label_edit = QLineEdit(self._teaching_path_editor)
        self._path_fraction_edit = _optional_property_edit(
            self._teaching_path_editor,
            "Area fraction as percentage",
        )
        path_form.addRow("Path name", self._path_label_edit)
        path_form.addRow("Area fraction (%)", self._path_fraction_edit)
        self._teaching_path_apply = QPushButton(
            "Apply focused path properties",
            self._teaching_path_editor,
        )
        self._teaching_path_apply.setObjectName(
            "uValueTeachingApplyPathProperties"
        )
        path_form.addRow(self._teaching_path_apply)
        property_editor_layout.addWidget(self._teaching_path_editor)
        property_editor_layout.addStretch()
        property_scroll.setWidget(property_scroll_content)
        property_layout.addWidget(property_scroll)

        self._teaching_property_reset = QPushButton(
            "Reset candidate to selected teaching model",
            property_box,
        )
        self._teaching_property_status = QLabel(
            "Select a layer token or path heading to edit its candidate values.",
            property_box,
        )
        self._teaching_property_status.setObjectName(
            "uValueTeachingPropertyStatus"
        )
        self._teaching_property_status.setWordWrap(True)
        property_layout.addWidget(self._teaching_property_reset)
        property_layout.addWidget(self._teaching_property_status)
        teaching_layout.addWidget(property_box)
        property_box.setVisible(False)

        self._teaching_property_toggle.toggled.connect(
            self._on_teaching_property_editor_toggled
        )
        self._teaching_property_target.currentIndexChanged.connect(
            self._on_teaching_property_target_changed
        )
        self._teaching_schematic.focus_changed.connect(
            self._on_teaching_focus_changed
        )
        self._teaching_schematic.candidate_changed.connect(
            self._on_teaching_candidate_changed
        )
        self._layer_basis_combo.currentIndexChanged.connect(
            self._update_layer_basis_enablement
        )
        self._teaching_layer_apply.clicked.connect(
            self._on_apply_focused_layer_properties
        )
        self._teaching_path_apply.clicked.connect(
            self._on_apply_focused_path_properties
        )
        self._teaching_property_reset.clicked.connect(
            lambda: self._on_teaching_model_selected(
                self._teaching_model_combo.currentIndex()
            )
        )

        save_box = QGroupBox("Save Candidate as Construction Model", teaching_box)
        save_box.setObjectName("uValueTeachingSaveModelGroup")
        save_layout = QVBoxLayout(save_box)

        self._teaching_save_name = QLineEdit(save_box)
        self._teaching_save_name.setObjectName("uValueTeachingSaveName")
        self._teaching_save_name.setPlaceholderText("New construction name")
        self._teaching_save_method = QComboBox(save_box)
        self._teaching_save_method.setObjectName("uValueTeachingSaveMethod")
        self._teaching_save_method.addItem("Not set", NOT_SET_U_VALUE_METHOD)
        self._teaching_save_method.addItem(
            "Legacy area-weighted paths",
            LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
        )
        self._teaching_save_method.addItem(
            "ISO 6946 combined limits — uncorrected base",
            ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
        )
        self._teaching_save_button = QPushButton(
            "Save as construction model…",
            save_box,
        )
        self._teaching_save_button.setObjectName("uValueTeachingSaveButton")
        self._teaching_save_status = QLabel(
            "Enter a unique name and explicitly choose the calculation method.",
            save_box,
        )
        self._teaching_save_status.setObjectName("uValueTeachingSaveStatus")
        self._teaching_save_status.setWordWrap(True)
        save_layout.addWidget(self._teaching_save_name)
        save_layout.addWidget(self._teaching_save_method)
        save_layout.addWidget(self._teaching_save_button)
        save_layout.addWidget(self._teaching_save_status)
        teaching_layout.addWidget(save_box)

        self._teaching_save_button.clicked.connect(
            self._on_save_teaching_model_requested
        )

        self._teaching_model_combo.currentIndexChanged.connect(
            self._on_teaching_model_selected
        )
        root.addWidget(teaching_box)
        teaching_box.setVisible(False)
        self._teaching_toggle.toggled.connect(
            self._on_teaching_workspace_toggled
        )
        self._on_teaching_model_selected(0)

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

        # --------------------------------------------------
        # Visible selected surface target
        # --------------------------------------------------
        surface_text = f"Surface: {surface_id}" if surface_id else "No surface selected"

        if hasattr(self, "_surface_label"):
            self._surface_label.setText(surface_text)

        if not surface_id:
            self._label_status.setText("No surface selected")
            self._label_status.setStyleSheet("color: #888;")
            return

        ps = self._context.project_state

        from HVAC.gui_v3.wizards.construction_wizard import ConstructionWizard

        assigned = ConstructionWizard.get_surface_construction(ps, surface_id)
        default = self._resolve_default_for_surface(surface_id)

        # --------------------------------------------------
        # Status text
        # --------------------------------------------------
        if assigned:
            text = f"✔ Assigned: {assigned}"
        else:
            text = f"Default: {default}"

        self._label_status.setText(text)

        # --------------------------------------------------
        # Visual styling
        # --------------------------------------------------
        if assigned:
            self._label_status.setStyleSheet("color: #2e7d32; font-weight: 600;")
        else:
            self._label_status.setStyleSheet("color: #888;")

        # --------------------------------------------------
        # Existing behaviour
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

    def set_teaching_model(self, model_id: str) -> None:
        """Select and reset one self-contained teaching candidate."""
        index = self._teaching_model_combo.findData(str(model_id or ""))
        if index < 0:
            raise KeyError(f"Unknown U-value teaching model: {model_id}")
        if index == self._teaching_model_combo.currentIndex():
            self._on_teaching_model_selected(index)
            return
        self._teaching_model_combo.setCurrentIndex(index)

    def teaching_model_id(self) -> str:
        return str(self._teaching_model_combo.currentData() or "")

    def teaching_candidate_evidence(self):
        return self._teaching_schematic.candidate_evidence()

    def set_teaching_workspace_expanded(self, expanded: bool) -> None:
        wanted = bool(expanded)
        self._teaching_toggle.blockSignals(True)
        self._teaching_toggle.setChecked(wanted)
        self._teaching_toggle.blockSignals(False)
        self._on_teaching_workspace_toggled(wanted)

    def teaching_workspace_expanded(self) -> bool:
        return bool(self._teaching_toggle.isChecked())

    def set_construction_model_save_result(
        self,
        *,
        ready: bool,
        status: str,
        construction_id: str = "",
        model_name: str = "",
    ) -> None:
        if ready:
            self._teaching_save_status.setText(
                f"Created “{model_name}” ({construction_id}) — available "
                "in Construction panel."
            )
            self._teaching_save_status.setStyleSheet(
                "color: #2e7d32; font-weight: 600;"
            )
            self._teaching_save_name.clear()
            return
        self._teaching_save_status.setText(status)
        self._teaching_save_status.setStyleSheet(
            "color: #9b3a24; font-weight: 600;"
        )

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

    def _on_teaching_workspace_toggled(self, expanded: bool) -> None:
        self._teaching_box.setVisible(bool(expanded))
        self._teaching_toggle.setText(
            "Hide layer/path modeller"
            if expanded
            else "Show layer/path modeller"
        )

    def _on_teaching_property_editor_toggled(self, expanded: bool) -> None:
        self._teaching_property_box.setVisible(bool(expanded))
        self._teaching_property_toggle.setText(
            "Hide focused layer/path properties"
            if expanded
            else "Edit focused layer/path properties…"
        )

    def _refresh_teaching_property_targets(self) -> None:
        evidence = self._teaching_schematic.candidate_evidence()
        focused_kind, focused_id = self._teaching_schematic.focused_item()
        wanted = f"{focused_kind}|{focused_id}" if focused_id else ""
        self._teaching_property_target.blockSignals(True)
        self._teaching_property_target.clear()
        self._teaching_property_target.addItem("Select layer or path…", "")
        if evidence is not None:
            for layer in evidence.layers:
                self._teaching_property_target.addItem(
                    f"Layer — {layer.label}",
                    f"layer|{layer.layer_id}",
                )
            for path in evidence.paths:
                self._teaching_property_target.addItem(
                    f"Path — {path.label} ({path.area_fraction * 100:.1f}%)",
                    f"path|{path.path_id}",
                )
        index = self._teaching_property_target.findData(wanted)
        self._teaching_property_target.setCurrentIndex(max(index, 0))
        self._teaching_property_target.blockSignals(False)

    def _on_teaching_property_target_changed(self, index: int) -> None:
        data = str(self._teaching_property_target.itemData(index) or "")
        if "|" not in data:
            self._teaching_schematic.focus_item("", "")
            return
        kind, item_id = data.split("|", 1)
        self._teaching_schematic.focus_item(kind, item_id)

    def _on_teaching_focus_changed(self, kind: str, item_id: str) -> None:
        wanted = f"{kind}|{item_id}" if item_id else ""
        index = self._teaching_property_target.findData(wanted)
        self._teaching_property_target.blockSignals(True)
        self._teaching_property_target.setCurrentIndex(max(index, 0))
        self._teaching_property_target.blockSignals(False)
        if item_id:
            self._teaching_property_toggle.setChecked(True)
        self._load_focused_property_fields()

    def _on_teaching_candidate_changed(self, _evidence) -> None:
        self._resize_teaching_schematic_viewport()
        self._refresh_teaching_property_targets()
        self._load_focused_property_fields()

    def _resize_teaching_schematic_viewport(self) -> None:
        """Expose the full schematic height; retain horizontal overflow only."""
        self._teaching_schematic.adjustSize()
        horizontal_extent = (
            self._teaching_scroll.horizontalScrollBar().sizeHint().height()
        )
        required_height = (
            self._teaching_schematic.height()
            + horizontal_extent
            + (2 * self._teaching_scroll.frameWidth())
        )
        self._teaching_scroll.setFixedHeight(max(150, required_height))
        self._teaching_scroll.verticalScrollBar().setValue(0)

    def _load_focused_property_fields(self) -> None:
        evidence = self._teaching_schematic.candidate_evidence()
        kind, item_id = self._teaching_schematic.focused_item()
        self._teaching_layer_editor.setVisible(False)
        self._teaching_path_editor.setVisible(False)
        if evidence is None or not item_id:
            self._teaching_property_status.setText(
                "Select a layer token or path heading to edit its candidate "
                "values."
            )
            return
        if kind == "layer":
            layer = evidence.layer_by_id().get(item_id)
            if layer is None:
                return
            self._teaching_layer_editor.setVisible(True)
            self._layer_included_check.setChecked(layer.included)
            self._layer_label_edit.setText(layer.label)
            _select_combo_data(self._layer_basis_combo, layer.basis)
            _set_optional_text(
                self._layer_thickness_edit,
                None if layer.thickness_m is None else layer.thickness_m * 1000,
            )
            _set_optional_text(
                self._layer_conductivity_edit,
                layer.conductivity_W_mK,
            )
            _set_optional_text(
                self._layer_declared_r_edit,
                layer.declared_resistance_m2K_W,
            )
            _set_optional_text(self._layer_density_edit, layer.density_kg_m3)
            _set_optional_text(
                self._layer_specific_heat_edit,
                layer.specific_heat_capacity_J_kgK,
            )
            _set_optional_text(
                self._layer_vapour_edit,
                layer.vapour_resistivity_MNs_gm,
            )
            _set_optional_text(
                self._layer_emissivity_edit,
                layer.surface_emissivity,
            )
            _set_optional_text(
                self._layer_absorptivity_edit,
                layer.solar_absorptivity,
            )
            _select_combo_data(
                self._layer_direction_combo,
                layer.material_direction,
            )
            _set_optional_text(
                self._layer_temperature_edit,
                layer.property_temperature_C,
            )
            self._layer_moisture_edit.setText(layer.moisture_condition)
            source_index = self._layer_source_combo.findData(layer.source_kind)
            if source_index < 0 and layer.source_kind:
                self._layer_source_combo.addItem(
                    f"Other retained source — {layer.source_kind}",
                    layer.source_kind,
                )
            _select_combo_data(self._layer_source_combo, layer.source_kind)
            self._layer_source_ref_edit.setText(layer.source_ref)
            self._layer_source_version_edit.setText(layer.source_version)
            self._layer_notes_edit.setText(layer.property_notes)
            self._update_layer_basis_enablement()
            self._teaching_property_status.setText(
                f"Focused layer: {layer.label}. Candidate only."
            )
            return
        if kind == "path":
            path = next(
                (item for item in evidence.paths if item.path_id == item_id),
                None,
            )
            if path is None:
                return
            self._teaching_path_editor.setVisible(True)
            self._path_label_edit.setText(path.label)
            _set_optional_text(
                self._path_fraction_edit,
                path.area_fraction * 100,
            )
            self._teaching_property_status.setText(
                f"Focused path: {path.label}. Fractions must total 100%."
            )

    def _update_layer_basis_enablement(self, _index: int = -1) -> None:
        homogeneous = self._layer_basis_combo.currentData() == (
            HOMOGENEOUS_LAYER_BASIS
        )
        self._layer_conductivity_edit.setEnabled(homogeneous)
        self._layer_declared_r_edit.setEnabled(not homogeneous)

    def _on_apply_focused_layer_properties(self) -> None:
        try:
            thickness_mm = _optional_float(self._layer_thickness_edit)
            result = self._teaching_schematic.update_focused_layer(
                label=self._layer_label_edit.text(),
                basis=str(self._layer_basis_combo.currentData() or ""),
                included=self._layer_included_check.isChecked(),
                thickness_m=(
                    None if thickness_mm is None else thickness_mm / 1000.0
                ),
                conductivity_W_mK=_optional_float(
                    self._layer_conductivity_edit
                ),
                declared_resistance_m2K_W=_optional_float(
                    self._layer_declared_r_edit
                ),
                density_kg_m3=_optional_float(self._layer_density_edit),
                specific_heat_capacity_J_kgK=_optional_float(
                    self._layer_specific_heat_edit
                ),
                vapour_resistivity_MNs_gm=_optional_float(
                    self._layer_vapour_edit
                ),
                surface_emissivity=_optional_float(
                    self._layer_emissivity_edit
                ),
                solar_absorptivity=_optional_float(
                    self._layer_absorptivity_edit
                ),
                material_direction=str(
                    self._layer_direction_combo.currentData() or ""
                ),
                property_temperature_C=_optional_float(
                    self._layer_temperature_edit
                ),
                moisture_condition=self._layer_moisture_edit.text(),
                source_kind=str(self._layer_source_combo.currentData() or ""),
                source_ref=self._layer_source_ref_edit.text(),
                source_version=self._layer_source_version_edit.text(),
                property_notes=self._layer_notes_edit.text(),
            )
        except ValueError as exc:
            self._set_teaching_property_result(False, f"Blocked — {exc}")
            return
        self._show_candidate_property_result(result)

    def _on_apply_focused_path_properties(self) -> None:
        try:
            fraction_percent = _required_float(self._path_fraction_edit)
        except ValueError as exc:
            self._set_teaching_property_result(False, f"Blocked — {exc}")
            return
        result = self._teaching_schematic.update_focused_path(
            label=self._path_label_edit.text(),
            area_fraction=fraction_percent / 100.0,
        )
        self._show_candidate_property_result(result)

    def _show_candidate_property_result(self, result) -> None:
        if not result.operation_ready:
            self._set_teaching_property_result(
                False,
                "Blocked — " + "; ".join(result.blockers),
            )
            return
        if result.candidate_valid:
            self._set_teaching_property_result(True, result.status)
            return
        self._teaching_property_status.setText(
            result.status + " — incomplete: " + "; ".join(result.blockers)
        )
        self._teaching_property_status.setStyleSheet(
            "color: #a45c08; font-weight: 600;"
        )

    def _set_teaching_property_result(self, ready: bool, status: str) -> None:
        self._teaching_property_status.setText(status)
        self._teaching_property_status.setStyleSheet(
            "color: #2e7d32; font-weight: 600;"
            if ready
            else "color: #9b3a24; font-weight: 600;"
        )

    def _on_teaching_model_selected(self, index: int) -> None:
        model_id = self._teaching_model_combo.itemData(index)
        if not model_id:
            return
        model = teaching_model_by_id_v1(str(model_id))
        self._teaching_model_description.setText(model.description)
        self._teaching_schematic.set_evidence(model.evidence)
        self._resize_teaching_schematic_viewport()
        self._refresh_teaching_property_targets()
        self._load_focused_property_fields()

    def _on_save_teaching_model_requested(self) -> None:
        evidence = self._teaching_schematic.candidate_evidence()
        if evidence is None:
            self.set_construction_model_save_result(
                ready=False,
                status="Blocked — complete construction evidence is required.",
            )
            return
        if self._teaching_schematic.staged_layers():
            self.set_construction_model_save_result(
                ready=False,
                status=(
                    "Blocked — restore or remove staged layers before saving "
                    "the construction model."
                ),
            )
            return
        self.construction_model_save_requested.emit(
            self._teaching_save_name.text(),
            str(self._teaching_save_method.currentData() or ""),
            evidence,
        )

    def _on_construction_selected(self, current, _previous):
        if not current:
            return

        cid = current.data(Qt.UserRole)
        if not cid:
            return

        self._selected_cid = cid

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


def _optional_property_edit(parent: QWidget, placeholder: str) -> QLineEdit:
    editor = QLineEdit(parent)
    editor.setPlaceholderText(placeholder)
    return editor


def _set_optional_text(editor: QLineEdit, value: float | None) -> None:
    editor.setText("" if value is None else f"{float(value):g}")


def _optional_float(editor: QLineEdit) -> float | None:
    text = editor.text().strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(
            f"{editor.placeholderText() or 'Property'} must be numeric"
        ) from exc


def _required_float(editor: QLineEdit) -> float:
    value = _optional_float(editor)
    if value is None:
        raise ValueError(
            f"{editor.placeholderText() or 'Property'} is required"
        )
    return value


def _select_combo_data(combo: QComboBox, value: str) -> None:
    index = combo.findData(str(value or ""))
    combo.setCurrentIndex(max(index, 0))
