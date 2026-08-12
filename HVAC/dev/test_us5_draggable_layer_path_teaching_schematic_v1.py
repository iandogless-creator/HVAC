from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    QApplication = None

from HVAC.constructions.physics.construction_layer_path_candidate_edit_v1 import (
    move_construction_layer_candidate_v1,
    restore_staged_construction_layer_candidate_v1,
    stage_construction_layer_candidate_v1,
)
from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    resolve_iso_6946_combined_u_value_v1,
)
from HVAC.constructions.physics.u_value_method_comparison_acceptance_v1 import (
    build_u_value_method_comparison_v1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    CAVITY_WALL_MODEL_ID,
    ONE_PATH_MODEL_ID,
    THREE_PATH_MODEL_ID,
    TWO_PATH_MODEL_ID,
    build_u_value_teaching_models_v1,
    teaching_model_by_id_v1,
)


def main() -> None:
    models = build_u_value_teaching_models_v1()
    assert [model.model_id for model in models] == [
        ONE_PATH_MODEL_ID,
        CAVITY_WALL_MODEL_ID,
        TWO_PATH_MODEL_ID,
        THREE_PATH_MODEL_ID,
    ]
    assert [len(model.evidence.paths) for model in models] == [1, 1, 2, 3]
    for model in models:
        assert resolve_iso_6946_combined_u_value_v1(model.evidence).ready
        assert build_u_value_method_comparison_v1(model.evidence).ready
    cavity = teaching_model_by_id_v1(CAVITY_WALL_MODEL_ID).evidence
    air = cavity.layer_by_id()["residual-air-cavity"]
    assert air.conductivity_W_mK is None
    assert air.declared_resistance_m2K_W == 0.18

    two_path = teaching_model_by_id_v1(TWO_PATH_MODEL_ID).evidence
    moved_shared = move_construction_layer_candidate_v1(
        two_path,
        layer_id="lining",
        source_path_id="insulated-bay",
        target_path_id="timber-stud",
        target_index=2,
    )
    assert moved_shared.operation_ready
    assert moved_shared.candidate_valid
    assert all(
        path.layer_ids[2] == "lining"
        for path in moved_shared.evidence.paths
    )

    cross_path = move_construction_layer_candidate_v1(
        two_path,
        layer_id="insulation",
        source_path_id="insulated-bay",
        target_path_id="timber-stud",
        target_index=1,
    )
    assert not cross_path.operation_ready
    assert "existing path" in " ".join(cross_path.blockers)

    staged = stage_construction_layer_candidate_v1(
        two_path,
        layer_id="stud",
        source_path_id="timber-stud",
    )
    assert staged.operation_ready
    assert staged.staged_layer is not None
    assert "stud" not in staged.evidence.paths[1].layer_ids
    assert not build_u_value_method_comparison_v1(staged.evidence).ready

    wrong_restore = restore_staged_construction_layer_candidate_v1(
        staged.evidence,
        staged.staged_layer,
        target_path_id="insulated-bay",
        target_index=1,
    )
    assert not wrong_restore.operation_ready
    restored = restore_staged_construction_layer_candidate_v1(
        staged.evidence,
        staged.staged_layer,
        target_path_id="timber-stud",
        target_index=1,
    )
    assert restored.operation_ready
    assert restored.candidate_valid
    assert restored.evidence == two_path

    staged_shared = stage_construction_layer_candidate_v1(
        two_path,
        layer_id="lining",
        source_path_id="insulated-bay",
    )
    assert staged_shared.operation_ready
    assert staged_shared.staged_layer.shared_layer_index == 0
    restored_shared = restore_staged_construction_layer_candidate_v1(
        staged_shared.evidence,
        staged_shared.staged_layer,
        target_path_id="timber-stud",
        target_index=0,
    )
    assert restored_shared.operation_ready
    assert restored_shared.evidence == two_path

    if QApplication is None:
        source = Path(
            "HVAC/gui_v3/widgets/"
            "construction_layer_path_schematic_widget_v1.py"
        ).read_text(encoding="utf-8")
        assert "class ConstructionLayerPathSchematicWidgetV1" in source
        assert "class ConstructionLayerStagingTrayV1" in source
        assert "candidate_changed = Signal(object)" in source
        print(
            "OK — U-S5 one/two/three-path teaching models and candidate "
            "drag/staging authority passed (source boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.widgets.construction_layer_path_schematic_widget_v1 import (
        PATH_DRAG_SOURCE,
        ConstructionLayerDragDropInteractionV1,
        ConstructionLayerDragEvidenceV1,
        ConstructionLayerDragTokenV1,
        ConstructionLayerPathSchematicWidgetV1,
        ConstructionLayerStagingTrayV1,
        ConstructionPathDropRowV1,
    )

    app = QApplication.instance() or QApplication([])
    del app
    widget = ConstructionLayerPathSchematicWidgetV1()
    widget.set_evidence(two_path)
    widget.grab()
    assert len(widget.findChildren(ConstructionPathDropRowV1)) == 2
    assert len(widget.findChildren(ConstructionLayerDragTokenV1)) == 6
    assert widget.findChild(ConstructionLayerStagingTrayV1) is not None
    assert "Knitted thermal network" in widget._network.text()
    assert "Legacy" in widget._status.text()
    assert "ISO base" in widget._status.text()

    drag = ConstructionLayerDragEvidenceV1(
        layer_id="stud",
        source_kind=PATH_DRAG_SOURCE,
        source_path_id="timber-stud",
        shared_layer=False,
    )
    decoded = ConstructionLayerDragDropInteractionV1.decode(
        ConstructionLayerDragDropInteractionV1.mime_data(drag)
    )
    assert decoded == drag

    changes = []
    widget.candidate_changed.connect(changes.append)
    stage_result = widget.stage_layer("stud", "timber-stud")
    assert stage_result.operation_ready
    assert [item.layer_id for item in widget.staged_layers()] == ["stud"]
    assert "Candidate incomplete" in widget._status.text()
    restore_result = widget.restore_layer("stud", "timber-stud", 1)
    assert restore_result.operation_ready
    assert not widget.staged_layers()
    assert widget.candidate_evidence() == two_path
    assert len(changes) == 2

    print(
        "OK — U-S5 no-air-gap one/two/three-path teaching models, knitted "
        "schematic and candidate-only drag/reorder/staging passed."
    )


if __name__ == "__main__":
    main()
