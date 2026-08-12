from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    TWO_PATH_MODEL_ID,
)

try:
    from PySide6.QtWidgets import QApplication, QGroupBox, QPushButton, QScrollArea
except ModuleNotFoundError:
    QApplication = None


class _ContextStub:
    project_state = None


def main() -> None:
    if QApplication is None:
        source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        for marker in (
            '"Show layer/path modeller"',
            '"Hide layer/path modeller"',
            '"uValueTeachingWorkspaceToggle"',
            "teaching_box.setVisible(False)",
            "teaching_scroll.setMinimumHeight(150)",
            "def set_teaching_workspace_expanded(",
            "def teaching_workspace_expanded(",
        ):
            assert marker in source
        print(
            "OK — U-S5B2 collapsed teaching-workspace boundary and relaxed "
            "vertical minimum passed (source boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    panel = UVPPanel(_ContextStub())
    toggle = panel.findChild(QPushButton, "uValueTeachingWorkspaceToggle")
    group = panel.findChild(QGroupBox, "uValueTeachingModelsGroup")
    scroll = panel.findChild(QScrollArea, "uValueTeachingSchematicScroll")

    assert toggle is not None
    assert group is not None
    assert scroll is not None
    assert not panel.teaching_workspace_expanded()
    assert group.isHidden()
    assert toggle.text() == "Show layer/path modeller"
    assert scroll.minimumHeight() == 150

    panel.set_teaching_workspace_expanded(True)
    assert panel.teaching_workspace_expanded()
    assert not group.isHidden()
    assert toggle.text() == "Hide layer/path modeller"

    panel.set_teaching_model(TWO_PATH_MODEL_ID)
    moved = panel._teaching_schematic.move_layer(
        "lining",
        "insulated-bay",
        "timber-stud",
        2,
    )
    assert moved.operation_ready
    edited = panel.teaching_candidate_evidence()
    panel.set_teaching_workspace_expanded(False)
    assert group.isHidden()
    assert panel.teaching_candidate_evidence() == edited
    panel.set_teaching_workspace_expanded(True)
    assert panel.teaching_candidate_evidence() == edited

    print(
        "OK — U-S5B2 starts compact, expands with internal scrolling and "
        "preserves the edited construction candidate while collapsed."
    )


if __name__ == "__main__":
    main()
