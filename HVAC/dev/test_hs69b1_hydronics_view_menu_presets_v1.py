from __future__ import annotations

import ast
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def _method_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Method not found: {name}")


def main() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app

    panel = HydronicsSchematicPanel()
    panel.select_proportioning_tab()
    assert panel._tabs.tabText(panel._tabs.currentIndex()) == "Proportioning"
    panel.select_proportioned_tab()
    assert panel._tabs.tabText(panel._tabs.currentIndex()) == "Proportioned"
    panel.close()
    app.processEvents()

    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    assert 'view_menu.addMenu("Main Window Views")' in source
    for label in (
        "Hydronics Setup",
        "Basic Sizing",
        "Proportioning",
        "Results",
    ):
        assert f'("{label}", self._apply_' in source

    expected_methods = {
        "_apply_hydronics_setup_view_v1": (
            "_dock_environment",
            "_dock_topology_arranger",
            "_dock_rooms",
            "_dock_hydronic_control",
        ),
        "_apply_basic_sizing_view_v1": (
            "_dock_basic_hydronics",
            "_dock_local_k",
            "_dock_rooms",
        ),
        "_apply_proportioning_view_v1": (
            "_dock_hydronics",
            "_dock_local_k",
        ),
        "_apply_hydronics_results_view_v1": (
            "_dock_hydronics",
            "_dock_project",
            "_dock_rooms",
        ),
    }
    for method_name, dock_names in expected_methods.items():
        method = _method_source(source, method_name)
        for dock_name in dock_names:
            assert dock_name in method
        assert "project_state" not in method
        assert "mark_hydronics" not in method
        assert "mark_heatloss" not in method

    preparation = _method_source(
        source,
        "_prepare_hydronics_workspace_view_v1",
    )
    assert "showMaximized()" in preparation
    assert "centralWidget()" in preparation
    assert "central_widget.hide()" in preparation
    assert "setFloating(False)" in preparation
    assert "removeDockWidget" in preparation
    assert "project_state" not in preparation

    assert "select_proportioning_tab()" in _method_source(
        source,
        "_apply_proportioning_view_v1",
    )
    assert "select_proportioned_tab()" in _method_source(
        source,
        "_apply_hydronics_results_view_v1",
    )

    print(
        "OK — H-S69-B1 adds four navigation-only Hydronics View-menu "
        "presets using existing single-instance docks and explicit "
        "Proportioning/Proportioned tab selection."
    )


if __name__ == "__main__":
    main()
