from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.uvp_panel import UVPPanel


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_heat_flow_temperature_contexts(
        [
            ("room-001", "Lounge", 21.0, -3.0, "room override"),
            ("room-002", "Hall", 18.0, -3.0, "Environment default"),
        ],
        "room-002",
    )
    assert panel._heat_flow_room_combo.count() == 2
    assert panel._heat_flow_room_combo.currentText() == "Hall"
    assert panel._teaching_schematic.temperature_context() == (18.0, -3.0)
    assert "Environment default" in panel._heat_flow_temperature_context.text()
    panel._heat_flow_room_combo.setCurrentIndex(0)
    app.processEvents()
    assert panel._teaching_schematic.temperature_context() == (21.0, -3.0)
    assert "room override" in panel._heat_flow_temperature_context.text()
    print("OK — U-S5D2A2 room-specific Ti and Environment Te combo projection passed.")


if __name__ == "__main__":
    main()
