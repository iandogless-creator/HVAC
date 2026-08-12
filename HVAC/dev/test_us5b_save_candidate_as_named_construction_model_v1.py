from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.constructions.physics.construction_model_save_candidate_v1 import (
    USER_CONSTRUCTION_MODEL_SOURCE,
    build_construction_model_save_candidate_v1,
)
from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
)
from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    SharedConstructionLayerPathEvidenceV1,
)
from HVAC.constructions.physics.u_value_method_comparison_acceptance_v1 import (
    NOT_SET_U_VALUE_METHOD,
    UValueMethodAcceptanceIntentV1,
    resolve_accepted_u_value_method_v1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    TWO_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)
from HVAC.core.construction_v1 import ConstructionV1
from HVAC.project.project_state import ProjectState

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    QApplication = None


def main() -> None:
    teaching = teaching_model_by_id_v1(TWO_PATH_MODEL_ID).evidence
    existing = {
        "DEV-WALL": ConstructionV1("DEV-WALL", "Existing Wall", 0.28)
    }

    missing_name = build_construction_model_save_candidate_v1(
        teaching,
        name="  ",
        selected_method=ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
        existing_constructions=existing,
    )
    assert not missing_name.ready
    assert "name is required" in " ".join(missing_name.blockers)

    duplicate = build_construction_model_save_candidate_v1(
        teaching,
        name=" existing   wall ",
        selected_method=ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
        existing_constructions=existing,
    )
    assert not duplicate.ready
    assert "already exists" in " ".join(duplicate.blockers)

    method_missing = build_construction_model_save_candidate_v1(
        teaching,
        name="Ian's timber wall",
        selected_method=NOT_SET_U_VALUE_METHOD,
        existing_constructions=existing,
    )
    assert not method_missing.ready
    assert "explicit" in " ".join(method_missing.blockers)

    saved = build_construction_model_save_candidate_v1(
        teaching,
        name="  Ian's   timber wall  ",
        selected_method=ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
        existing_constructions=existing,
    )
    assert saved.ready, saved.blockers
    assert saved.name == "Ian's timber wall"
    assert saved.construction_id.startswith("USR-IAN-S-TIMBER-WALL-")
    assert saved.evidence.construction_id == saved.construction_id
    assert saved.evidence.label == saved.name
    assert saved.evidence.source_kind == USER_CONSTRUCTION_MODEL_SOURCE
    assert saved.u_value_W_m2K > 0.0
    assert teaching.construction_id == "teaching-stud-wall-001"

    repeated = build_construction_model_save_candidate_v1(
        teaching,
        name="Ian's timber wall",
        selected_method=ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
        existing_constructions=existing,
    )
    assert repeated.construction_id == saved.construction_id

    legacy = build_construction_model_save_candidate_v1(
        teaching,
        name="Legacy timber wall",
        selected_method=LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
        existing_constructions=existing,
    )
    assert legacy.ready
    assert "Legacy method" in " ".join(legacy.warnings)

    model = ConstructionV1(
        construction_id=saved.construction_id,
        name=saved.name,
        u_value_W_m2K=float(saved.u_value_W_m2K),
        layer_path_evidence=saved.evidence.to_dict(),
        u_value_method_acceptance=saved.method_acceptance.to_dict(),
    )
    project = ProjectState(project_id="us5b-project", name="U-S5B")
    project.constructions = {model.construction_id: model}
    restored = ProjectState.from_dict(project.to_dict())
    restored_model = restored.constructions[model.construction_id]
    assert restored_model.layer_path_evidence == model.layer_path_evidence
    assert (
        restored_model.u_value_method_acceptance
        == model.u_value_method_acceptance
    )
    restored_evidence = SharedConstructionLayerPathEvidenceV1.from_dict(
        restored_model.layer_path_evidence
    )
    restored_intent = UValueMethodAcceptanceIntentV1.from_dict(
        restored_model.u_value_method_acceptance
    )
    restored_acceptance = resolve_accepted_u_value_method_v1(
        restored_evidence,
        restored_intent,
    )
    assert restored_acceptance.ready, restored_acceptance.blockers
    assert (
        restored_acceptance.accepted_u_value_W_m2K
        == restored_model.u_value_W_m2K
    )

    if QApplication is None:
        panel_source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        adapter_source = Path(
            "HVAC/gui_v3/adapters/uvp_panel_adapter.py"
        ).read_text(encoding="utf-8")
        construction_adapter_source = Path(
            "HVAC/gui_v3/adapters/construction_panel_adapter.py"
        ).read_text(encoding="utf-8")
        for marker in (
            "construction_model_save_requested = Signal(str, str, object)",
            '"Save as construction model…"',
            "def _on_save_teaching_model_requested",
            "restore or remove staged layers",
        ):
            assert marker in panel_source
        assert "build_construction_model_save_candidate_v1(" in adapter_source
        assert "ps.constructions[result.construction_id]" in adapter_source
        assert "layer_path_evidence" in construction_adapter_source
        own_source = Path(__file__).read_text(encoding="utf-8")
        assert "construction_adapter = ConstructionPanelAdapter(" in own_source
        assert "uvp_adapter = UVPPanelAdapter(" in own_source
        print(
            "OK — U-S5B named construction-model save authority and "
            "persistence passed (source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.adapters.construction_panel_adapter import (
        ConstructionPanelAdapter,
    )
    from HVAC.gui_v3.adapters.uvp_panel_adapter import UVPPanelAdapter
    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.construction_panel import ConstructionPanel
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    gui_project = ProjectState(project_id="us5b-gui", name="U-S5B GUI")
    gui_project.constructions = dict(existing)
    gui_project.heatloss_valid = True
    context = GuiProjectContext(project_state=gui_project)
    construction_panel = ConstructionPanel()
    construction_adapter = ConstructionPanelAdapter(
        panel=construction_panel,
        context=context,
    )
    uvp_panel = UVPPanel(context)
    uvp_adapter = UVPPanelAdapter(panel=uvp_panel, context=context)
    uvp_panel.set_teaching_model(TWO_PATH_MODEL_ID)
    uvp_panel._teaching_save_name.setText("Saved timber wall")
    method_index = uvp_panel._teaching_save_method.findData(
        ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1
    )
    uvp_panel._teaching_save_method.setCurrentIndex(method_index)
    uvp_panel._teaching_save_button.click()

    saved_rows = [
        construction
        for construction in gui_project.constructions.values()
        if construction.name == "Saved timber wall"
    ]
    assert len(saved_rows) == 1
    saved_row = saved_rows[0]
    assert saved_row.layer_path_evidence
    assert saved_row.u_value_method_acceptance
    assert not gui_project.heatloss_valid
    assert construction_adapter is not None
    assert uvp_adapter is not None
    assert construction_panel.get_selected_construction_id() == (
        saved_row.construction_id
    )
    assert "Created" in uvp_panel._teaching_save_status.text()

    count = len(gui_project.constructions)
    uvp_panel._teaching_save_name.setText("Saved timber wall")
    uvp_panel._teaching_save_button.click()
    assert len(gui_project.constructions) == count
    assert "already exists" in uvp_panel._teaching_save_status.text()

    uvp_panel._teaching_schematic.stage_layer("stud", "timber-stud")
    uvp_panel._teaching_save_name.setText("Incomplete wall")
    uvp_panel._teaching_save_button.click()
    assert len(gui_project.constructions) == count
    assert "staged layers" in uvp_panel._teaching_save_status.text()

    print(
        "OK — U-S5B saves complete edited candidates under unique names, "
        "persists their method evidence and refreshes Construction panel."
    )


if __name__ == "__main__":
    main()
