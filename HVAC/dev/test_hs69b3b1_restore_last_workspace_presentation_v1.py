from __future__ import annotations

import ast
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.gui_v3.context.gui_settings import GuiSettings
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
    with TemporaryDirectory() as directory:
        settings_dir = Path(directory)
        settings = GuiSettings(settings_dir)

        assert settings.last_workspace_presentation_v1() is None
        assert not settings.set_last_workspace_presentation_v1(
            "unknown", "exploded"
        )
        assert not settings.set_last_workspace_presentation_v1(
            "heat_loss", "unknown"
        )
        assert settings.set_last_workspace_presentation_v1(
            "building_edit", "exploded"
        )
        settings.save()

        path = settings_dir / "gui_v3_workspace.json"
        stored = json.loads(path.read_text(encoding="utf-8"))
        assert stored["last_workspace_presentation_v1"] == {
            "view_id": "building_edit",
            "mode": "exploded",
        }

        restored = GuiSettings(settings_dir)
        assert restored.last_workspace_presentation_v1() == {
            "view_id": "building_edit",
            "mode": "exploded",
        }

        stored["last_workspace_presentation_v1"] = {
            "view_id": "not-a-view",
            "mode": "exploded",
        }
        path.write_text(json.dumps(stored), encoding="utf-8")
        invalid = GuiSettings(settings_dir)
        assert invalid.last_workspace_presentation_v1() is None

    compact_saved_dock = resolve_exploded_dock_geometry_v1(
        saved_geometry={
            "x": 2254,
            "y": 588,
            "width": 248,
            "height": 88,
            "screen_name": "DisplayPort-1",
        },
        screens=(
            WorkspaceScreenGeometryV1(
                "DisplayPort-1", 1920, 0, 1920, 1080
            ),
        ),
        dock_index=4,
        dock_count=5,
    )
    assert compact_saved_dock is not None
    assert compact_saved_dock.width == 248
    assert compact_saved_dock.height == 88

    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    restore_workspace = _method_source(source, "_restore_workspace")
    assert "QTimer.singleShot" in restore_workspace
    assert "_restore_last_workspace_presentation_v1" in restore_workspace

    restore_presentation = _method_source(
        source, "_restore_last_workspace_presentation_v1"
    )
    for view_id in (
        "heat_loss",
        "building_edit",
        "openings",
        "hydronics_setup",
        "basic_sizing",
        "proportioning",
        "results",
    ):
        assert restore_presentation.count(f'("{view_id}", "docked")') == 1
        assert restore_presentation.count(f'("{view_id}", "exploded")') == 1

    docked = _method_source(
        source, "_prepare_hydronics_workspace_view_v1"
    )
    assert "set_last_workspace_presentation_v1" in docked
    assert '"docked"' in docked

    exploded = _method_source(source, "_apply_exploded_workspace_view_v1")
    assert "set_last_workspace_presentation_v1" in exploded
    assert '"exploded"' in exploded
    assert "named_workspace_layout_v1" in exploded
    assert "showNormal()" in exploded
    assert "showMaximized()" not in exploded
    assert "self.resize(360, 96)" in exploded
    assert "QTimer.singleShot" in exploded
    assert exploded.index("dock.show()") < exploded.index(
        "dock.setGeometry(*target_geometry)"
    )

    close_event = _method_source(source, "closeEvent")
    assert "_save_active_exploded_workspace_layout_v1" in close_event

    print(
        "OK — H-S69-B3B1 remembers and restores the last docked/exploded "
        "workspace presentation while retaining independent exploded "
        "geometry for all seven named views, including compact docks "
        "and a compact main-window shell."
    )


if __name__ == "__main__":
    main()
