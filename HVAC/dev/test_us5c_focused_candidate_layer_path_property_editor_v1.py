from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.constructions.physics.construction_layer_path_candidate_edit_v1 import (
    update_construction_layer_properties_candidate_v1,
    update_construction_path_properties_candidate_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    PARALLEL_MATERIAL_DIRECTION,
    SharedConstructionLayerPathEvidenceV1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    TWO_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)


def main() -> None:
    original = teaching_model_by_id_v1(TWO_PATH_MODEL_ID).evidence
    original_insulation = original.layer_by_id()["insulation"]
    edited = update_construction_layer_properties_candidate_v1(
        original,
        layer_id="insulation",
        label="Audited mineral wool",
        basis=original_insulation.basis,
        thickness_m=0.12,
        conductivity_W_mK=0.032,
        declared_resistance_m2K_W=None,
        density_kg_m3=32.0,
        specific_heat_capacity_J_kgK=840.0,
        vapour_resistivity_MNs_gm=5.0,
        surface_emissivity=0.90,
        solar_absorptivity=0.55,
        material_direction=PARALLEL_MATERIAL_DIRECTION,
        property_temperature_C=10.0,
        moisture_condition="standard moisture content",
        source_kind="ihve_a3_1972",
        source_ref="IHVE Guide A3 table/page pending audit",
        source_version="1972",
        property_notes="Legacy source selected explicitly; value remains visible.",
    )
    assert edited.operation_ready
    assert edited.candidate_valid, edited.blockers
    assert edited.evidence is not None
    layer = edited.evidence.layer_by_id()["insulation"]
    assert layer.label == "Audited mineral wool"
    assert layer.thickness_m == 0.12
    assert layer.conductivity_W_mK == 0.032
    assert layer.density_kg_m3 == 32.0
    assert layer.specific_heat_capacity_J_kgK == 840.0
    assert layer.vapour_resistivity_MNs_gm == 5.0
    assert layer.surface_emissivity == 0.90
    assert layer.solar_absorptivity == 0.55
    assert layer.material_direction == PARALLEL_MATERIAL_DIRECTION
    assert layer.property_temperature_C == 10.0
    assert layer.moisture_condition == "standard moisture content"
    assert layer.source_kind == "ihve_a3_1972"
    assert original.layer_by_id()["insulation"] == original_insulation

    roundtrip = SharedConstructionLayerPathEvidenceV1.from_dict(
        edited.evidence.to_dict()
    )
    assert roundtrip == edited.evidence

    first_fraction = update_construction_path_properties_candidate_v1(
        edited.evidence,
        path_id="insulated-bay",
        label="Insulated bay",
        area_fraction=0.80,
    )
    assert first_fraction.operation_ready
    assert not first_fraction.candidate_valid
    assert "fractions total" in " ".join(first_fraction.blockers)
    second_fraction = update_construction_path_properties_candidate_v1(
        first_fraction.evidence,
        path_id="timber-stud",
        label="Timber stud",
        area_fraction=0.20,
    )
    assert second_fraction.operation_ready
    assert second_fraction.candidate_valid, second_fraction.blockers

    invalid_emissivity = update_construction_layer_properties_candidate_v1(
        original,
        layer_id="insulation",
        label="Invalid emissivity",
        basis=original_insulation.basis,
        thickness_m=0.10,
        conductivity_W_mK=0.035,
        declared_resistance_m2K_W=None,
        surface_emissivity=1.10,
    )
    assert invalid_emissivity.operation_ready
    assert not invalid_emissivity.candidate_valid
    assert "between 0 and 1" in " ".join(invalid_emissivity.blockers)

    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        widget_source = Path(
            "HVAC/gui_v3/widgets/"
            "construction_layer_path_schematic_widget_v1.py"
        ).read_text(encoding="utf-8")
        panel_source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        assert "focus_changed = Signal(str, str)" in widget_source
        assert "def update_focused_layer(" in widget_source
        assert "uValueTeachingPropertyEditorToggle" in panel_source
        assert "uValueTeachingPropertyEditorScroll" in panel_source
        assert "property_scroll.setMaximumHeight(300)" in panel_source
        assert "IHVE Guide A3 — 1972" in panel_source
        assert "CIBSE Guide A3 — 1980" in panel_source
        print(
            "OK — U-S5C focused candidate layer/path properties and source "
            "selection passed (source boundary; Qt unavailable)."
        )
        return

    from types import SimpleNamespace

    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.show()
    app.processEvents()
    panel.set_teaching_workspace_expanded(True)
    panel.set_teaching_model(TWO_PATH_MODEL_ID)
    panel._teaching_schematic.focus_item("layer", "insulation")
    assert panel._teaching_property_box.isVisible()
    assert panel._teaching_property_scroll.maximumHeight() == 300
    assert panel._teaching_layer_editor.isVisible()
    assert panel._layer_label_edit.text() == "Mineral wool"
    panel._layer_label_edit.setText("Podcast mineral wool")
    panel._layer_thickness_edit.setText("120")
    panel._layer_conductivity_edit.setText("0.032")
    panel._layer_density_edit.setText("32")
    panel._layer_specific_heat_edit.setText("840")
    panel._layer_vapour_edit.setText("5")
    panel._layer_emissivity_edit.setText("0.9")
    panel._layer_absorptivity_edit.setText("0.55")
    panel._layer_source_combo.setCurrentIndex(
        panel._layer_source_combo.findData("ihve_a3_1972")
    )
    panel._layer_source_ref_edit.setText("IHVE A3 source pending audit")
    panel._on_apply_focused_layer_properties()
    live = panel.teaching_candidate_evidence().layer_by_id()["insulation"]
    assert live.label == "Podcast mineral wool"
    assert live.thickness_m == 0.12
    assert live.density_kg_m3 == 32.0
    assert live.source_kind == "ihve_a3_1972"
    assert "Focused layer properties updated" in (
        panel._teaching_property_status.text()
    )

    panel._teaching_schematic.focus_item("path", "insulated-bay")
    assert panel._teaching_path_editor.isVisible()
    panel._path_fraction_edit.setText("80")
    panel._on_apply_focused_path_properties()
    assert "fractions total" in panel._teaching_property_status.text()
    panel._teaching_schematic.focus_item("path", "timber-stud")
    panel._path_fraction_edit.setText("20")
    panel._on_apply_focused_path_properties()
    assert "Focused path properties updated" in (
        panel._teaching_property_status.text()
    )

    panel._teaching_property_reset.click()
    reset = panel.teaching_candidate_evidence()
    assert reset == original

    print(
        "OK — U-S5C focused candidate layer/path property editor, complete "
        "property evidence and explicit source selection passed."
    )


if __name__ == "__main__":
    main()
