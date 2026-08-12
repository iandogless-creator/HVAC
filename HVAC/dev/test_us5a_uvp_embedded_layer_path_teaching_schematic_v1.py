from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QGroupBox, QScrollArea
except ModuleNotFoundError:
    QApplication = None

from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    CAVITY_WALL_MODEL_ID,
    ONE_PATH_MODEL_ID,
    THREE_PATH_MODEL_ID,
    TWO_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)
class _ContextStub:
    project_state = None


def main() -> None:
    if QApplication is None:
        source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        for marker in (
            'QGroupBox("Layer / Path Teaching Models")',
            'setObjectName("uValueTeachingModelSelector")',
            "ConstructionLayerPathSchematicWidgetV1(",
            "def set_teaching_model(",
            "def teaching_candidate_evidence(",
            "accepted U-value",
        ):
            assert marker in source
        print(
            "OK — U-S5A U-Values teaching-schematic embed boundary passed "
            "(source boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.panels.uvp_panel import UVPPanel
    from HVAC.gui_v3.widgets.construction_layer_path_schematic_widget_v1 import (
        ConstructionLayerPathSchematicWidgetV1,
        ConstructionPathDropRowV1,
    )

    app = QApplication.instance() or QApplication([])
    del app

    panel = UVPPanel(_ContextStub())
    group = panel.findChild(QGroupBox, "uValueTeachingModelsGroup")
    selector = panel.findChild(QComboBox, "uValueTeachingModelSelector")
    scroll = panel.findChild(QScrollArea, "uValueTeachingSchematicScroll")
    schematic = panel.findChild(ConstructionLayerPathSchematicWidgetV1)

    assert group is not None
    assert selector is not None
    assert scroll is not None
    assert schematic is not None
    assert selector.count() == 4
    assert [selector.itemData(index) for index in range(selector.count())] == [
        ONE_PATH_MODEL_ID,
        CAVITY_WALL_MODEL_ID,
        TWO_PATH_MODEL_ID,
        THREE_PATH_MODEL_ID,
    ]

    authoritative_u_intents = []
    assignment_intents = []
    panel.u_value_changed.connect(authoritative_u_intents.append)
    panel.assign_requested.connect(assignment_intents.append)

    panel.set_teaching_model(TWO_PATH_MODEL_ID)
    assert panel.teaching_model_id() == TWO_PATH_MODEL_ID
    assert panel.teaching_candidate_evidence() == teaching_model_by_id_v1(
        TWO_PATH_MODEL_ID
    ).evidence
    assert len(schematic.findChildren(ConstructionPathDropRowV1)) == 2

    staged = schematic.stage_layer("stud", "timber-stud")
    assert staged.operation_ready
    assert schematic.staged_layers()
    panel.set_teaching_model(TWO_PATH_MODEL_ID)
    assert not schematic.staged_layers()
    assert panel.teaching_candidate_evidence() == teaching_model_by_id_v1(
        TWO_PATH_MODEL_ID
    ).evidence

    panel.set_teaching_model(THREE_PATH_MODEL_ID)
    assert len(schematic.findChildren(ConstructionPathDropRowV1)) == 3
    assert "Two core regions" in panel._teaching_model_description.text()
    assert not authoritative_u_intents
    assert not assignment_intents

    try:
        panel.set_teaching_model("unknown-model")
    except KeyError:
        pass
    else:
        raise AssertionError("Unknown teaching model must be rejected")

    print(
        "OK — U-S5A embeds the candidate-only one/two/three-path teaching "
        "schematic in U-Values without changing accepted U-value intent."
    )


if __name__ == "__main__":
    main()
