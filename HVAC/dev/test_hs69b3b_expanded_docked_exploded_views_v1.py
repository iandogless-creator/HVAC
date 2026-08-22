from __future__ import annotations

import ast
from pathlib import Path

from HVAC.gui_v3.context.workspace_view_geometry_v1 import (
    WorkspaceScreenGeometryV1,
    resolve_exploded_dock_geometry_v1,
)


def _method_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Method not found: {name}")


def main() -> None:
    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    assert 'view_menu.addMenu("Main Window Views")' in source
    assert 'view_menu.addMenu("Exploded Views")' in source
    assert 'view_menu.addMenu("Project & Heat-Loss Panels")' in source
    assert 'view_menu.addMenu("Hydronics Panels")' in source
    assert 'view_menu.addMenu("Utility Panels")' in source

    for label in (
        "Heat Loss",
        "Building Edit",
        "Openings",
        "Hydronics Setup",
        "Basic Sizing",
        "Proportioning",
        "Results",
    ):
        assert source.count(f'QAction("{label}", self)') == 0
        assert source.count(f'("{label}", self._apply_') == 2

    workspace_docks = _method_source(source, "_workspace_docks_v1")
    for view_id in (
        "heat_loss",
        "building_edit",
        "openings",
        "hydronics_setup",
        "basic_sizing",
        "proportioning",
        "results",
    ):
        assert f'"{view_id}"' in workspace_docks
    assert "project_state" not in workspace_docks

    exploded = _method_source(source, "_apply_exploded_workspace_view_v1")
    assert "setFloating(True)" in exploded
    assert "resolve_exploded_dock_geometry_v1" in exploded
    assert "named_workspace_layout_v1" in exploded
    assert "project_state" not in exploded
    assert "mark_hydronics" not in exploded
    assert "mark_heatloss" not in exploded

    screens_source = _method_source(source, "_qt_workspace_screens_v1")
    assert "primaryScreen" in screens_source

    save_active = _method_source(
        source, "_save_active_exploded_workspace_layout_v1"
    )
    assert "set_named_workspace_layout_v1" in save_active
    assert "temporarily_clamped" in save_active
    close_event = _method_source(source, "closeEvent")
    assert "_save_active_exploded_workspace_layout_v1" in close_event

    screens = (
        WorkspaceScreenGeometryV1("HDMI-1", 0, 0, 1920, 1080),
        WorkspaceScreenGeometryV1("HDMI-2", 1920, 0, 1920, 1080),
    )
    primary = resolve_exploded_dock_geometry_v1(
        saved_geometry=None,
        screens=screens,
        dock_index=0,
        dock_count=4,
    )
    companion = resolve_exploded_dock_geometry_v1(
        saved_geometry=None,
        screens=screens,
        dock_index=1,
        dock_count=4,
    )
    assert primary is not None and primary.screen_name == "HDMI-1"
    assert companion is not None and companion.screen_name == "HDMI-2"
    assert companion.x >= 1920

    missing_screen = resolve_exploded_dock_geometry_v1(
        saved_geometry={
            "x": 2100,
            "y": 100,
            "width": 800,
            "height": 700,
            "screen_name": "HDMI-2",
        },
        screens=(screens[0],),
        dock_index=1,
        dock_count=4,
    )
    assert missing_screen is not None
    assert missing_screen.screen_name == "HDMI-1"
    assert missing_screen.used_fallback_screen
    assert 0 <= missing_screen.x <= 1920 - missing_screen.width

    print(
        "OK — H-S69-B3B provides seven docked and exploded navigation "
        "views, grouped panel toggles, dual-1080 defaults and safe named "
        "floating placement persistence without engineering mutation."
    )


if __name__ == "__main__":
    main()
