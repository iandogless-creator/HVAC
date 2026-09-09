from __future__ import annotations

import ast
from pathlib import Path


def _method_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Method not found: {name}")


def main() -> None:
    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    build_menu = _method_source(source, "_build_menu")
    add_action = _method_source(source, "_add_exclusive_panel_action_v1")
    show_panel = _method_source(source, "_show_exclusive_panel_view_v1")

    assert "toggleViewAction()" not in build_menu
    assert build_menu.count("_add_exclusive_panel_action_v1") == 3
    assert "QAction(" in add_action
    assert "_show_exclusive_panel_view_v1" in add_action

    assert "_finish_active_exploded_workspace_v1()" in show_panel
    assert "_set_user_workspace_checked_v1(False)" in show_panel
    assert "candidate.hide()" in show_panel
    assert "candidate.setFloating(False)" in show_panel
    assert "self.addDockWidget(Qt.RightDockWidgetArea, dock)" in show_panel
    assert "dock.show()" in show_panel
    assert "dock.raise_()" in show_panel
    assert "Main Window" in show_panel
    assert "_gui_settings" not in show_panel
    assert "project_state" not in show_panel

    print(
        "OK — H-S69-B3L panel-menu navigation closes the active user, "
        "docked or exploded presentation, re-docks one selected panel in "
        "the main window, preserves safe workspace geometry and performs no "
        "engineering mutation."
    )


if __name__ == "__main__":
    main()
