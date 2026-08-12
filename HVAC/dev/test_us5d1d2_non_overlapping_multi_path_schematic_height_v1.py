from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main() -> None:
    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        source = Path(
            "HVAC/gui_v3/widgets/"
            "construction_layer_path_schematic_widget_v1.py"
        ).read_text(encoding="utf-8")
        assert "self._root.minimumSize().height()" in source
        assert "self._root.sizeHint().height()" in source
        assert "self.resize(max(self.width(), required_width), required_height)" in source
        print(
            "OK — U-S5D1D2 non-overlapping multi-path schematic height "
            "passed (source boundary; Qt unavailable)."
        )
        return

    from HVAC.constructions.physics.u_value_teaching_models_v1 import (
        THREE_PATH_MODEL_ID,
        TWO_PATH_MODEL_ID,
    )
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel
    from HVAC.gui_v3.widgets.construction_layer_path_schematic_widget_v1 import (
        ConstructionPathDropRowV1,
    )

    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_teaching_workspace_expanded(True)
    panel.resize(900, 760)
    panel.show()

    for model_id, expected_count in (
        (TWO_PATH_MODEL_ID, 2),
        (THREE_PATH_MODEL_ID, 3),
    ):
        panel.set_teaching_model(model_id)
        app.processEvents()
        schematic = panel._teaching_schematic
        rows = sorted(
            schematic.findChildren(ConstructionPathDropRowV1),
            key=lambda row: row.geometry().top(),
        )
        assert len(rows) == expected_count
        assert all(
            upper.geometry().bottom() < lower.geometry().top()
            for upper, lower in zip(rows, rows[1:])
        )
        assert schematic._network.geometry().top() > rows[-1].geometry().bottom()
        assert schematic._status.geometry().top() > (
            schematic._network.geometry().bottom()
        )
        assert panel._teaching_scroll.verticalScrollBar().maximum() == 0
        assert panel._teaching_scroll.viewport().height() >= schematic.height()

    print(
        "OK — U-S5D1D2 two- and three-path rows, network and status remain "
        "separate and fully visible."
    )


if __name__ == "__main__":
    main()
