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
from PySide6.QtGui import QColor, QPalette
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

from HVAC.constructions.physics.two_path_member_spacing_fraction_v1 import (
    CALCULATED_REPEATING_MEMBER_FRACTION,
    DECLARED_EFFECTIVE_MEMBER_FRACTION,
    TwoPathMemberSpacingIntentV1,
)
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
    declared_opening_construction_save_requested = Signal(object)

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
        # Declared whole-window / whole-door construction
        # --------------------------------------------------------------
        self._declared_opening_toggle = QPushButton(
            "▸ Show declared window/door entry",
            self,
        )
        self._declared_opening_toggle.setObjectName(
            "uValueDeclaredOpeningToggle"
        )
        self._declared_opening_toggle.setCheckable(True)
        self._declared_opening_toggle.setChecked(False)
        root.addWidget(self._declared_opening_toggle)

        declared_box = QGroupBox(
            "Declared Window / Door Construction",
            self,
        )
        declared_box.setObjectName("uValueDeclaredOpeningGroup")
        self._declared_opening_box = declared_box
        declared_layout = QVBoxLayout(declared_box)
        declared_note = QLabel(
            "Enter a manufacturer or schedule whole-window Uw or "
            "whole-door Ud. Saving explicitly accepts that declared "
            "whole-product value; no frame or thermal-bridge calculation "
            "is performed.",
            declared_box,
        )
        declared_note.setWordWrap(True)
        declared_layout.addWidget(declared_note)
        declared_form = QFormLayout()
        self._declared_opening_type = QComboBox(declared_box)
        self._declared_opening_type.setObjectName("uValueDeclaredOpeningType")
        self._declared_opening_type.addItem("Window", "WINDOW")
        self._declared_opening_type.addItem("External door", "DOOR")
        self._declared_opening_name = QLineEdit(declared_box)
        self._declared_opening_name.setObjectName("uValueDeclaredOpeningName")
        self._declared_opening_name.setPlaceholderText("Construction name")
        self._declared_opening_u_value = QDoubleSpinBox(declared_box)
        self._declared_opening_u_value.setObjectName(
            "uValueDeclaredOpeningUValue"
        )
        self._declared_opening_u_value.setRange(0.01, 10.0)
        self._declared_opening_u_value.setDecimals(3)
        self._declared_opening_u_value.setSuffix(" W/m²K")
        self._declared_opening_u_value.setValue(1.4)
        self._declared_opening_source_kind = QComboBox(declared_box)
        self._declared_opening_source_kind.setObjectName(
            "uValueDeclaredOpeningSourceKind"
        )
        self._declared_opening_source_kind.addItem(
            "Manufacturer declaration",
            "manufacturer_declaration",
        )
        self._declared_opening_source_kind.addItem(
            "Product schedule",
            "product_schedule",
        )
        self._declared_opening_source_kind.addItem(
            "Assessment / certificate",
            "assessment_or_certificate",
        )
        self._declared_opening_source_ref = QLineEdit(declared_box)
        self._declared_opening_source_ref.setObjectName(
            "uValueDeclaredOpeningSourceRef"
        )
        self._declared_opening_source_ref.setPlaceholderText(
            "Manufacturer, product or document reference"
        )
        self._declared_opening_source_version = QLineEdit(declared_box)
        self._declared_opening_source_version.setObjectName(
            "uValueDeclaredOpeningSourceVersion"
        )
        self._declared_opening_source_version.setPlaceholderText(
            "Edition / version (optional)"
        )
        declared_form.addRow("Type", self._declared_opening_type)
        declared_form.addRow("Construction name", self._declared_opening_name)
        declared_form.addRow(
            "Declared whole-product U-value",
            self._declared_opening_u_value,
        )
        declared_form.addRow("Source type", self._declared_opening_source_kind)
        declared_form.addRow("Source reference", self._declared_opening_source_ref)
        declared_form.addRow(
            "Edition / version",
            self._declared_opening_source_version,
        )
        declared_layout.addLayout(declared_form)
        self._declared_opening_save_button = QPushButton(
            "Save declared construction",
            declared_box,
        )
        self._declared_opening_save_button.setObjectName(
            "uValueDeclaredOpeningSaveButton"
        )
        self._declared_opening_status = QLabel(
            "Enter a unique name, declared U-value and source reference.",
            declared_box,
        )
        self._declared_opening_status.setObjectName(
            "uValueDeclaredOpeningStatus"
        )
        self._declared_opening_status.setWordWrap(True)
        declared_layout.addWidget(self._declared_opening_save_button)
        declared_layout.addWidget(self._declared_opening_status)
        root.addWidget(declared_box)
        declared_box.setVisible(False)
        self._declared_opening_toggle.toggled.connect(
            self._on_declared_opening_toggled
        )
        self._declared_opening_save_button.clicked.connect(
            self._on_save_declared_opening_requested
        )

        # --------------------------------------------------------------
        # Candidate-only layer/path teaching schematic
        # --------------------------------------------------------------
        self._teaching_toggle = QPushButton(
            "▸ Show layer/path modeller",
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

        self._heat_flow_room_combo = QComboBox(teaching_box)
        self._heat_flow_room_combo.setObjectName(
            "uValueHeatFlowRoomSelector"
        )
        self._heat_flow_room_combo.setToolTip(
            "Select the room design-temperature context for the "
            "candidate heat-flow profile"
        )
        teaching_layout.addWidget(self._heat_flow_room_combo)
        self._heat_flow_temperature_context = QLabel(teaching_box)
        self._heat_flow_temperature_context.setObjectName(
            "uValueHeatFlowTemperatureContext"
        )
        teaching_layout.addWidget(self._heat_flow_temperature_context)

        self._member_spacing_box = QGroupBox(
            "Member spacing / path fractions",
            teaching_box,
        )
        self._member_spacing_box.setObjectName("uValueMemberSpacingGroup")
        member_form = QFormLayout(self._member_spacing_box)
        self._member_width_mm = QDoubleSpinBox(self._member_spacing_box)
        self._member_width_mm.setRange(1.0, 500.0)
        self._member_width_mm.setDecimals(1)
        self._member_width_mm.setSuffix(" mm")
        self._member_centres_mm = QDoubleSpinBox(self._member_spacing_box)
        self._member_centres_mm.setRange(10.0, 5000.0)
        self._member_centres_mm.setDecimals(1)
        self._member_centres_mm.setSuffix(" mm")
        self._member_fraction_basis = QComboBox(self._member_spacing_box)
        self._member_fraction_basis.addItem(
            "Calculated from member width ÷ centres",
            CALCULATED_REPEATING_MEMBER_FRACTION,
        )
        self._member_fraction_basis.addItem(
            "Declared effective framing fraction",
            DECLARED_EFFECTIVE_MEMBER_FRACTION,
        )
        self._member_declared_fraction = QDoubleSpinBox(self._member_spacing_box)
        self._member_declared_fraction.setRange(0.1, 99.9)
        self._member_declared_fraction.setDecimals(2)
        self._member_declared_fraction.setSuffix(" %")
        self._member_calculated_fraction = QLabel("—", self._member_spacing_box)
        self._member_controlling_fraction = QLabel("—", self._member_spacing_box)
        self._member_clear_fraction = QLabel("—", self._member_spacing_box)
        self._member_spacing_apply = QPushButton(
            "Apply member spacing to candidate",
            self._member_spacing_box,
        )
        self._member_spacing_apply.setObjectName("uValueApplyMemberSpacing")
        self._member_spacing_status = QLabel(self._member_spacing_box)
        self._member_spacing_status.setWordWrap(True)
        member_form.addRow("Finished member width", self._member_width_mm)
        member_form.addRow("Member centres", self._member_centres_mm)
        member_form.addRow("Calculated repeating fraction", self._member_calculated_fraction)
        member_form.addRow("Controlling basis", self._member_fraction_basis)
        member_form.addRow("Declared effective fraction", self._member_declared_fraction)
        member_form.addRow("Controlling member fraction", self._member_controlling_fraction)
        member_form.addRow("Clear insulated fraction", self._member_clear_fraction)
        member_form.addRow(self._member_spacing_apply)
        member_form.addRow(self._member_spacing_status)
        teaching_layout.addWidget(self._member_spacing_box)
        self._member_spacing_box.setVisible(False)
        self._member_spacing_intent = None

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
            "▸ Edit focused layer/path properties…",
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
            "Reset to selected preset",
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

        self._heat_flow_room_combo.currentIndexChanged.connect(
            self._on_heat_flow_room_context_changed
        )
        self._member_fraction_basis.currentIndexChanged.connect(
            self._on_member_fraction_basis_changed
        )
        self._member_spacing_apply.clicked.connect(
            self._on_apply_member_spacing
        )
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

        self._apply_uvp_button_hierarchy_v1()
        self._set_assign_target_available_v1(False)

        # Spacer
        root.addItem(
            QSpacerItem(
                20,
                40,
                QSizePolicy.Minimum,
                QSizePolicy.Expanding,
            )
        )

    def _apply_uvp_button_hierarchy_v1(self) -> None:
        """Give U-Values section controls and actions distinct visual roles."""
        primary_actions = (
            self._declared_opening_save_button,
            self._member_spacing_apply,
            self._teaching_layer_apply,
            self._teaching_path_apply,
            self._teaching_save_button,
            self._assign_btn,
        )
        for button in primary_actions:
            button.setProperty("uvpButtonRole", "primaryAction")
            button.setMinimumHeight(34)
            button.setMinimumWidth(230)
            button.setMaximumWidth(360)
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            parent_layout = button.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.setAlignment(button, Qt.AlignRight)

        self._teaching_property_reset.setProperty(
            "uvpButtonRole",
            "secondaryAction",
        )
        self._teaching_property_reset.setMinimumHeight(34)
        self._teaching_property_reset.setMinimumWidth(230)
        self._teaching_property_reset.setMaximumWidth(360)
        self._teaching_property_reset.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed,
        )
        reset_layout = self._teaching_property_reset.parentWidget().layout()
        if reset_layout is not None:
            reset_layout.setAlignment(
                self._teaching_property_reset,
                Qt.AlignRight,
            )

        for toggle in (
            self._declared_opening_toggle,
            self._teaching_toggle,
            self._teaching_property_toggle,
        ):
            toggle.setProperty("uvpButtonRole", "sectionToggle")
            toggle.setMinimumHeight(32)
            toggle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Let each selector follow its longest current option.  This also
        # responds when adapters later replace room or construction choices.
        for combo in self.findChildren(QComboBox):
            combo.setProperty("uvpControlRole", "contentSizedCombo")
            combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToContents
            )
            combo.setMinimumWidth(0)
            combo.setMaximumWidth(16777215)
            combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            parent_layout = combo.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.setAlignment(combo, Qt.AlignLeft)

        # Declared-product entries need useful writing space, not the entire
        # panel width.  Derive their widths from their prompt text so they
        # remain sensible with the active application font.
        declared_entry_widths = (
            (self._declared_opening_name, 300, 440),
            (self._declared_opening_source_ref, 360, 560),
            (self._declared_opening_source_version, 230, 340),
        )
        for entry, minimum, maximum in declared_entry_widths:
            prompt = entry.placeholderText() or ("M" * 24)
            text_width = entry.fontMetrics().horizontalAdvance(prompt) + 36
            entry.setFixedWidth(max(minimum, min(maximum, text_width)))

        u_value_width = (
            self._declared_opening_u_value.fontMetrics().horizontalAdvance(
                "10.000 W/m²K"
            )
            + 42
        )
        self._declared_opening_u_value.setFixedWidth(max(160, u_value_width))

        edit_u_value_width = self._u_spin.fontMetrics().horizontalAdvance(
            "10.000"
        ) + 42
        self._u_spin.setFixedWidth(max(130, edit_u_value_width))

        member_spacing_width = max(
            150,
            self._member_centres_mm.fontMetrics().horizontalAdvance(
                "5000.0 mm"
            )
            + 42,
        )
        for member_spin in (
            self._member_width_mm,
            self._member_centres_mm,
            self._member_declared_fraction,
        ):
            member_spin.setFixedWidth(member_spacing_width)
            member_layout = member_spin.parentWidget().layout()
            if member_layout is not None:
                member_layout.setAlignment(member_spin, Qt.AlignLeft)

        # Keep the remaining editable values close to the amount of text they
        # are intended to hold.  Longer references and notes retain more room.
        remaining_entry_widths = (
            (self._teaching_save_name, 320, 440),
            (self._layer_label_edit, 300, 440),
            (self._layer_thickness_edit, 180, 240),
            (self._layer_conductivity_edit, 180, 240),
            (self._layer_declared_r_edit, 180, 240),
            (self._layer_density_edit, 180, 240),
            (self._layer_specific_heat_edit, 180, 240),
            (self._layer_vapour_edit, 220, 320),
            (self._layer_emissivity_edit, 180, 240),
            (self._layer_absorptivity_edit, 180, 240),
            (self._layer_temperature_edit, 220, 300),
            (self._layer_moisture_edit, 260, 360),
            (self._layer_source_ref_edit, 360, 560),
            (self._layer_source_version_edit, 230, 340),
            (self._layer_notes_edit, 420, 620),
            (self._path_label_edit, 300, 440),
            (self._path_fraction_edit, 180, 240),
        )
        for entry, minimum, maximum in remaining_entry_widths:
            prompt = entry.placeholderText() or ("M" * 24)
            text_width = entry.fontMetrics().horizontalAdvance(prompt) + 36
            entry.setFixedWidth(max(minimum, min(maximum, text_width)))

        self.setStyleSheet(
            self.styleSheet()
            + """
            QLineEdit {
                selection-background-color: #e5a24f;
                selection-color: #202020;
            }
            QAbstractSpinBox QLineEdit {
                selection-background-color: #e5a24f;
                selection-color: #202020;
            }
            QPushButton[uvpButtonRole="primaryAction"] {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1f5d27;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton[uvpButtonRole="primaryAction"]:hover {
                background-color: #3b9145;
                border-color: #1d5525;
            }
            QPushButton[uvpButtonRole="primaryAction"]:pressed {
                background-color: #25652e;
            }
            QPushButton[uvpButtonRole="primaryAction"]:disabled {
                background-color: #b8c1c8;
                color: #eef1f3;
                border-color: #a5afb7;
            }
            QPushButton[uvpButtonRole="secondaryAction"] {
                background-color: #e8edf1;
                color: #263b4d;
                border: 1px solid #8fa1b0;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton[uvpButtonRole="secondaryAction"]:hover {
                background-color: #d9e2e9;
                border-color: #667f93;
            }
            QPushButton[uvpButtonRole="sectionToggle"] {
                background-color: #dfe8ef;
                color: #243746;
                border: 1px solid #91a5b4;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton[uvpButtonRole="sectionToggle"]:hover {
                background-color: #d1dee8;
                border-color: #6f899d;
            }
            QPushButton[uvpButtonRole="sectionToggle"]:checked {
                background-color: #c7d8e5;
                border-color: #5f7f97;
            }
            """
        )

        # Qt platform themes may ignore selected-text colours inherited from
        # a parent stylesheet, especially inside QAbstractSpinBox.  Apply the
        # readable focus palette to each real editor explicitly.
        for editor in self.findChildren(QLineEdit):
            # A widget-local declaration outranks the native Mint theme and
            # any stylesheet later installed on MainWindow.
            editor.setStyleSheet(
                editor.styleSheet()
                + " selection-background-color: #e0a15a;"
                + " selection-color: #000000;"
            )
            palette = editor.palette()
            for group in (
                QPalette.ColorGroup.Active,
                QPalette.ColorGroup.Inactive,
                QPalette.ColorGroup.Disabled,
            ):
                palette.setColor(
                    group,
                    QPalette.ColorRole.Highlight,
                    QColor("#e0a15a"),
                )
                palette.setColor(
                    group,
                    QPalette.ColorRole.HighlightedText,
                    QColor("#000000"),
                )
            editor.setPalette(palette)

    def _set_assign_target_available_v1(self, available: bool) -> None:
        ready = bool(available)
        self._assign_btn.setEnabled(ready)
        self._assign_btn.setToolTip(
            "Assign the selected construction to the focused surface"
            if ready
            else "Select a surface before assigning a construction"
        )

    # ------------------------------------------------------------------
    # Public API (called by adapters / main window)
    # ------------------------------------------------------------------

    def set_heat_flow_temperature_contexts(
        self,
        contexts: list[tuple[str, str, float, float, str]],
        selected_room_id: str | None = None,
    ) -> None:
        previous = str(
            selected_room_id
            or self._heat_flow_room_combo.currentData()
            or ""
        )
        self._heat_flow_room_combo.blockSignals(True)
        self._heat_flow_room_combo.clear()
        for room_id, room_label, ti_C, te_C, source in contexts:
            self._heat_flow_room_combo.addItem(
                room_label,
                (room_id, float(ti_C), float(te_C), source),
            )
        wanted = next(
            (
                index
                for index in range(self._heat_flow_room_combo.count())
                if str(self._heat_flow_room_combo.itemData(index)[0])
                == previous
            ),
            0 if self._heat_flow_room_combo.count() else -1,
        )
        self._heat_flow_room_combo.setCurrentIndex(wanted)
        self._heat_flow_room_combo.blockSignals(False)
        self._on_heat_flow_room_context_changed(wanted)

    def _on_heat_flow_room_context_changed(self, index: int) -> None:
        data = self._heat_flow_room_combo.itemData(index)
        if not data:
            self._heat_flow_temperature_context.setText(
                "Heat-flow temperature context unavailable"
            )
            self._teaching_schematic.set_temperature_context(None, None)
            return
        _room_id, ti_C, te_C, source = data
        self._heat_flow_temperature_context.setText(
            f"Ti {ti_C:.1f} °C ({source})   •   Te {te_C:.1f} °C "
            "(Environment)"
        )
        self._teaching_schematic.set_temperature_context(ti_C, te_C)

    def set_declared_opening_save_result(
        self,
        *,
        ready: bool,
        status: str,
        construction_id: str = "",
        model_name: str = "",
    ) -> None:
        if ready:
            self._declared_opening_status.setText(
                f"Created “{model_name}” ({construction_id}) — available "
                "for assignment."
            )
            self._declared_opening_status.setStyleSheet(
                "color: #2e7d32; font-weight: 600;"
            )
            self._declared_opening_name.clear()
            self._declared_opening_source_ref.clear()
            self._declared_opening_source_version.clear()
            return
        self._declared_opening_status.setText(status)
        self._declared_opening_status.setStyleSheet(
            "color: #9b3a24; font-weight: 600;"
        )

    def set_constructions(self, constructions: dict) -> None:
        self._construction_list.clear()

        for cid, c in constructions.items():
            item = QListWidgetItem(c.name)

            # 🔥 THIS IS THE LINE YOU WERE ASKING ABOUT
            item.setData(Qt.UserRole, cid)

            self._construction_list.addItem(item)

    def set_selected_surface(self, surface_id: str | None) -> None:
        self._selected_surface_id = surface_id
        self._set_assign_target_available_v1(bool(surface_id))

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

    def set_selected_construction(
        self,
        cid: str,
        u_value_W_m2K: float | None,
    ) -> None:
        """Project one complete construction focus without emitting intent."""
        wanted = str(cid or "")
        if not wanted:
            return
        for i in range(self._construction_list.count()):
            item = self._construction_list.item(i)
            if item.data(Qt.UserRole) != wanted:
                continue
            self._construction_list.blockSignals(True)
            self._construction_list.setCurrentItem(item)
            self._construction_list.blockSignals(False)
            self._selected_cid = wanted
            self.set_u_value(u_value_W_m2K)
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

    def _load_member_spacing_intent(self, intent) -> None:
        self._member_spacing_intent = intent
        self._member_spacing_box.setVisible(intent is not None)
        if intent is None:
            return
        controls = (
            self._member_width_mm,
            self._member_centres_mm,
            self._member_fraction_basis,
            self._member_declared_fraction,
        )
        for control in controls:
            control.blockSignals(True)
        self._member_width_mm.setValue(intent.member_width_m * 1000.0)
        self._member_centres_mm.setValue(intent.member_centres_m * 1000.0)
        basis_index = self._member_fraction_basis.findData(intent.controlling_basis)
        self._member_fraction_basis.setCurrentIndex(max(0, basis_index))
        self._member_declared_fraction.setValue(
            100.0 * float(intent.declared_effective_member_fraction or 0.15)
        )
        for control in controls:
            control.blockSignals(False)
        self._on_member_fraction_basis_changed()
        self._refresh_member_fraction_labels()

    def _on_member_fraction_basis_changed(self, _index: int = -1) -> None:
        declared = self._member_fraction_basis.currentData() == (
            DECLARED_EFFECTIVE_MEMBER_FRACTION
        )
        self._member_declared_fraction.setEnabled(declared)

    def _current_member_spacing_intent(self):
        existing = self._member_spacing_intent
        if existing is None:
            return None
        return TwoPathMemberSpacingIntentV1(
            member_path_id=existing.member_path_id,
            clear_path_id=existing.clear_path_id,
            member_label=existing.member_label,
            member_width_m=self._member_width_mm.value() / 1000.0,
            member_centres_m=self._member_centres_mm.value() / 1000.0,
            controlling_basis=str(self._member_fraction_basis.currentData() or ""),
            declared_effective_member_fraction=(
                self._member_declared_fraction.value() / 100.0
            ),
            source_note=existing.source_note,
        )

    def _on_apply_member_spacing(self) -> None:
        intent = self._current_member_spacing_intent()
        if intent is None:
            return
        result = self._teaching_schematic.update_member_spacing_intent(intent)
        if not result.ready:
            self._member_spacing_status.setText(
                "Blocked — " + "; ".join(result.blockers)
            )
            self._member_spacing_status.setStyleSheet("color: #9b3a24;")
            return
        self._member_spacing_intent = intent
        self._refresh_member_fraction_labels(result.fraction)
        self._member_spacing_status.setText(result.status)
        self._member_spacing_status.setStyleSheet("color: #2e7d32;")
        self._resize_teaching_schematic_viewport()

    def _refresh_member_fraction_labels(self, fraction=None) -> None:
        intent = self._current_member_spacing_intent()
        if intent is None:
            return
        if fraction is None:
            fraction = self._teaching_schematic.resolve_member_spacing_intent(
                intent
            )
        if not fraction.ready:
            return
        self._member_calculated_fraction.setText(
            f"{fraction.calculated_repeating_member_fraction * 100:.2f} %"
        )
        self._member_controlling_fraction.setText(
            f"{fraction.controlling_member_fraction * 100:.2f} %"
        )
        self._member_clear_fraction.setText(
            f"{fraction.controlling_clear_fraction * 100:.2f} %"
        )

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
            "▾ Hide layer/path modeller"
            if expanded
            else "▸ Show layer/path modeller"
        )

    def _on_teaching_property_editor_toggled(self, expanded: bool) -> None:
        self._teaching_property_box.setVisible(bool(expanded))
        self._teaching_property_toggle.setText(
            "▾ Hide focused layer/path properties"
            if expanded
            else "▸ Edit focused layer/path properties…"
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
        has_focused_item = evidence is not None and bool(item_id)
        self._teaching_property_scroll.setVisible(has_focused_item)
        if not has_focused_item:
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
        self._load_member_spacing_intent(model.member_spacing_intent)
        self._teaching_schematic.set_evidence(model.evidence)
        self._resize_teaching_schematic_viewport()
        self._refresh_teaching_property_targets()
        self._load_focused_property_fields()

    def _on_declared_opening_toggled(self, expanded: bool) -> None:
        self._declared_opening_box.setVisible(bool(expanded))
        self._declared_opening_toggle.setText(
            "▾ Hide declared window/door entry"
            if expanded
            else "▸ Show declared window/door entry"
        )

    def _on_save_declared_opening_requested(self) -> None:
        self.declared_opening_construction_save_requested.emit(
            {
                "opening_type": str(
                    self._declared_opening_type.currentData() or ""
                ),
                "name": self._declared_opening_name.text(),
                "declared_u_value_W_m2K": float(
                    self._declared_opening_u_value.value()
                ),
                "source_kind": str(
                    self._declared_opening_source_kind.currentData() or ""
                ),
                "source_ref": self._declared_opening_source_ref.text(),
                "source_version": self._declared_opening_source_version.text(),
            }
        )

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
