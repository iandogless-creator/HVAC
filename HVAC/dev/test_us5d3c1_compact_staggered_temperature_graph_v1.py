from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from HVAC.constructions.physics.u_value_teaching_models_v1 import TWO_PATH_MODEL_ID
from HVAC.gui_v3.panels.uvp_panel import UVPPanel
from HVAC.gui_v3.widgets.construction_layer_path_schematic_widget_v1 import (
    PROFILE_GRAPH_MAXIMUM_WIDTH,
    PROFILE_GRAPH_POINT_RADIUS,
    _compact_profile_graph_label,
    _profile_temperature_label_y_offset,
)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_teaching_workspace_expanded(True)
    panel.set_teaching_model(TWO_PATH_MODEL_ID)
    panel.set_heat_flow_temperature_contexts(
        [("room-001", "Lounge", 21.0, -3.0, "room override")],
        "room-001",
    )
    graph = panel._teaching_schematic._profile_graph
    result = graph.result()
    assert result is not None and result.ready
    assert graph.maximumWidth() == PROFILE_GRAPH_MAXIMUM_WIDTH == 1120
    assert PROFILE_GRAPH_POINT_RADIUS == 2.5
    assert _compact_profile_graph_label(("tai",)) == "Ti"
    assert _compact_profile_graph_label(("Rsi",)) == "Rsi"
    assert _compact_profile_graph_label(
        (
            "Mineral wool between studs",
            "Timber stud — 38 × 140 mm finished CLS",
        )
    ) == "Insulation / Stud"
    assert _compact_profile_graph_label(("Structural OSB sheathing",)) == "OSB"
    assert _profile_temperature_label_y_offset(0) < 0.0
    assert _profile_temperature_label_y_offset(1) > 0.0

    graph.resize(PROFILE_GRAPH_MAXIMUM_WIDTH, graph.minimumHeight())
    image = QImage(graph.size(), QImage.Format_ARGB32)
    image.fill(0)
    graph.render(image)
    assert not image.isNull()
    app.processEvents()
    print(
        "OK — U-S5D3C1 compact staggered graph labels and coloured "
        "above/below node temperatures rendered."
    )


if __name__ == "__main__":
    main()
