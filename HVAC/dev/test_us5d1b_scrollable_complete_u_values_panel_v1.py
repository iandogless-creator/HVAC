from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main() -> None:
    panel_source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
        encoding="utf-8"
    )
    for required in (
        'page_scroll.setObjectName("uValuePanelOuterScroll")',
        "page_scroll.setWidgetResizable(True)",
        "page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)",
        "page_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)",
        "page_scroll.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)",
        "self._panel_scroll = page_scroll",
        "self._teaching_scroll = teaching_scroll",
        "self._teaching_property_scroll = property_scroll",
    ):
        assert required in panel_source, required

    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        print(
            "OK — U-S5D1B complete U-Values outer-scroll authority passed "
            "(source boundary; Qt unavailable)."
        )
        return

    from types import SimpleNamespace

    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.resize(900, 600)
    panel.show()
    app.processEvents()
    initial_size = panel.size()

    panel.set_teaching_workspace_expanded(True)
    panel._teaching_schematic.focus_item("layer", "plaster")
    app.processEvents()

    assert panel.size() == initial_size
    assert panel._panel_scroll.widget() is panel._panel_scroll_content
    assert panel._panel_scroll.horizontalScrollBarPolicy() == (
        Qt.ScrollBarAlwaysOff
    )
    assert panel._panel_scroll.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    assert panel._panel_scroll.verticalScrollBar().maximum() > 0
    assert panel._teaching_scroll is not panel._panel_scroll
    assert panel._teaching_property_scroll is not panel._panel_scroll

    panel._panel_scroll.verticalScrollBar().setValue(
        panel._panel_scroll.verticalScrollBar().maximum()
    )
    app.processEvents()
    assert panel._assign_btn.isVisible()

    panel.set_teaching_workspace_expanded(False)
    app.processEvents()
    assert panel.size() == initial_size

    print(
        "OK — U-S5D1B expanded modeller remains within the available window "
        "and all lower U-Values controls are reachable."
    )


if __name__ == "__main__":
    main()
