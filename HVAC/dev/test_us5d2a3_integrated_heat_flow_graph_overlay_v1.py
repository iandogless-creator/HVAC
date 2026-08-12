from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

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
    panel.resize(1100, 900)
    panel.show()
    app.processEvents()
    graph = panel._teaching_schematic._profile_graph
    result = graph.result()
    assert graph.isVisible()
    assert result is not None and result.ready, getattr(result, "blockers", ())
    assert len(result.paths) == 2
    assert all(path.heat_flow_W_m2 > 0.0 for path in result.paths)
    labels = [label.text() for label in panel._teaching_schematic.findChildren(QLabel)]
    assert any(text.startswith("Rsi\n") for text in labels)
    assert any(text.startswith("Rso\n") for text in labels)
    assert "Inside →" not in labels
    assert "→ Outside" not in labels
    print("OK — U-S5D2A3 Rsi/layers/Rso heat-flow and temperature graph overlay passed.")


if __name__ == "__main__":
    main()
