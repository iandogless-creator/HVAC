from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.constructions.physics.two_path_member_spacing_fraction_v1 import (
    CALCULATED_REPEATING_MEMBER_FRACTION,
    DECLARED_EFFECTIVE_MEMBER_FRACTION,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import TWO_PATH_MODEL_ID
from HVAC.gui_v3.panels.uvp_panel import UVPPanel


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_teaching_workspace_expanded(True)
    panel.set_teaching_model(TWO_PATH_MODEL_ID)
    panel.set_heat_flow_temperature_contexts(
        [("room-001", "Lounge", 21.0, -3.0, "room override")],
        "room-001",
    )
    assert panel._member_spacing_box.isVisibleTo(panel._teaching_box)
    assert panel._member_width_mm.value() == 38.0
    assert panel._member_centres_mm.value() == 600.0
    assert panel._member_calculated_fraction.text() == "6.33 %"

    index = panel._member_fraction_basis.findData(
        CALCULATED_REPEATING_MEMBER_FRACTION
    )
    panel._member_fraction_basis.setCurrentIndex(index)
    panel._on_apply_member_spacing()
    evidence = panel.teaching_candidate_evidence()
    fractions = {path.path_id: path.area_fraction for path in evidence.paths}
    assert abs(fractions["timber-stud"] - 0.038 / 0.600) < 1e-12
    assert abs(sum(fractions.values()) - 1.0) < 1e-12
    graph_result = panel._teaching_schematic._profile_graph.result()
    assert graph_result is not None and graph_result.ready

    index = panel._member_fraction_basis.findData(
        DECLARED_EFFECTIVE_MEMBER_FRACTION
    )
    panel._member_fraction_basis.setCurrentIndex(index)
    panel._member_declared_fraction.setValue(20.0)
    panel._on_apply_member_spacing()
    fractions = {
        path.path_id: path.area_fraction
        for path in panel.teaching_candidate_evidence().paths
    }
    assert fractions["timber-stud"] == 0.20
    assert fractions["insulated-bay"] == 0.80
    assert panel._member_controlling_fraction.text() == "20.00 %"
    assert panel._member_clear_fraction.text() == "80.00 %"
    app.processEvents()
    print("OK — U-S5D3A2 member-spacing controls update both paths and graph atomically.")


if __name__ == "__main__":
    main()
