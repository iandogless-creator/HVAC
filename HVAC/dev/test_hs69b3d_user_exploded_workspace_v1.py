from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.context.workspace_view_geometry_v1 import (
    WorkspaceScreenGeometryV1,
    resolve_user_workspace_dock_geometry_v1,
)


def _layout() -> dict:
    return {
        "docks": {
            "dock_rooms": {
                "x": 40,
                "y": 60,
                "width": 520,
                "height": 760,
                "screen_name": "Display-1",
            },
            "dock_heat_loss": {
                "x": 580,
                "y": 60,
                "width": 920,
                "height": 760,
                "screen_name": "Display-2",
            },
        }
    }


def main() -> None:
    screens = (
        WorkspaceScreenGeometryV1("Display-1", 0, 0, 1920, 1080),
        WorkspaceScreenGeometryV1("Display-2", 1920, 0, 1920, 1080),
    )
    resolved = tuple(
        resolve_user_workspace_dock_geometry_v1(
            screens=screens, dock_index=index, dock_count=4
        )
        for index in range(4)
    )
    assert all(item is not None for item in resolved)
    assert {item.screen_name for item in resolved} == {
        "Display-1", "Display-2"
    }
    assert all(item.width <= 720 for item in resolved)
    assert all(item.height <= 820 for item in resolved)
    assert len({(item.x, item.y) for item in resolved}) == 4

    with TemporaryDirectory() as directory:
        settings_dir = Path(directory)
        path = settings_dir / "gui_v3_workspace.json"
        settings = GuiSettings(settings_dir)

        assert settings.set_named_workspace_layout_v1(
            "user:exploded", _layout()
        )
        assert settings.set_last_workspace_presentation_v1(
            "user", "exploded"
        )
        assert not settings.set_last_workspace_presentation_v1(
            "user", "docked"
        )
        settings.save()

        stored = json.loads(path.read_text(encoding="utf-8"))
        assert set(
            stored["named_workspace_layouts_v1"]
            ["user:exploded"]["docks"]
        ) == {"dock_rooms", "dock_heat_loss"}
        assert stored["last_workspace_presentation_v1"] == {
            "view_id": "user",
            "mode": "exploded",
        }

        restored = GuiSettings(settings_dir)
        assert restored.last_workspace_presentation_v1() == {
            "view_id": "user",
            "mode": "exploded",
        }
        assert restored.named_workspace_layout_v1(
            "user:exploded"
        ) is not None

    source = Path("HVAC/gui_v3/main_window.py").read_text(
        encoding="utf-8"
    )
    assert 'QAction("User Workspace", self)' in source
    assert '"Choose User Workspace Panels…"' in source
    assert "QDialogButtonBox.StandardButton.Ok" in source
    assert "resolve_user_workspace_dock_geometry_v1(" in source
    assert '"user:exploded"' in source
    assert 'self._apply_exploded_workspace_view_v1("user", docks)' in source

    method_start = source.index(
        "    def _choose_user_workspace_panels_v1(self)"
    )
    method_end = source.index(
        "    def _save_active_exploded_workspace_layout_v1(self)",
        method_start,
    )
    user_source = source[method_start:method_end]
    assert "saveState(" not in user_source
    assert "restoreState(" not in user_source

    print(
        "OK — H-S69-B3D1 chooses panels without opening main-window "
        "docks, creates a compact bounded exploded setout and never uses "
        "opaque Qt dock state."
    )


if __name__ == "__main__":
    main()
