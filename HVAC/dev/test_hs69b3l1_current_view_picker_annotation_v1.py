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
    membership = _method_source(source, "_current_workspace_dock_ids_v1")
    annotation = _method_source(source, "_current_workspace_annotation_v1")
    picker = _method_source(source, "_choose_workspace_panels_v1")
    single = _method_source(source, "_show_exclusive_panel_view_v1")
    docked = _method_source(source, "_prepare_hydronics_workspace_view_v1")
    exploded = _method_source(source, "_apply_exploded_workspace_view_v1")

    assert "_active_single_panel_dock_v1" in membership
    assert "_active_exploded_workspace_docks_v1" in membership
    assert "_active_docked_workspace_docks_v1" in membership
    assert "_active_single_panel_dock_v1" in annotation
    assert "single.windowTitle()" in annotation
    assert 'return f"{panel_title} — Main Window"' in annotation
    assert "windowTitle()" in annotation
    assert 'prefix = "HVACgooee — "' in annotation
    assert "Current view:" in picker
    assert "— current view" in picker
    assert "checkbox.setChecked(dock_id in selected_ids)" in picker
    assert "_active_single_panel_dock_v1 = dock" in single
    assert "_active_single_panel_dock_v1 = None" in docked
    assert "_active_single_panel_dock_v1 = None" in exploded
    assert "project_state" not in membership + annotation + picker

    print(
        "OK — H-S69-B3L1 annotates the current presentation and its member "
        "panels in workspace pickers without changing stored selections or "
        "engineering state."
    )


if __name__ == "__main__":
    main()
