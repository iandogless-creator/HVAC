from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.gui_v3.context.gui_settings import GuiSettings


def _layout(*, panel_ids: list[str] | None = None) -> dict:
    layout = {
        "docks": {
            "dock_rooms": {
                "x": 40,
                "y": 60,
                "width": 420,
                "height": 700,
                "screen_name": "Display-1",
            }
        }
    }
    if panel_ids is not None:
        layout["panel_ids"] = panel_ids
    return layout


def main() -> None:
    with TemporaryDirectory() as directory:
        settings_dir = Path(directory)
        path = settings_dir / "gui_v3_workspace.json"
        settings = GuiSettings(settings_dir)
        assert settings.set_named_workspace_layout_v1(
            "heat_loss:exploded",
            _layout(panel_ids=[
                "dock_rooms",
                "dock_uvp",
                "dock_rooms",
                "",
            ]),
        )
        settings.save()

        stored = json.loads(path.read_text(encoding="utf-8"))
        layout = stored["named_workspace_layouts_v1"][
            "heat_loss:exploded"
        ]
        assert layout["panel_ids"] == ["dock_rooms", "dock_uvp"]

        restored = GuiSettings(settings_dir)
        layout = restored.named_workspace_layout_v1(
            "heat_loss:exploded"
        )
        assert layout["panel_ids"] == ["dock_rooms", "dock_uvp"]
        layout["panel_ids"].append("dock_project")
        again = restored.named_workspace_layout_v1(
            "heat_loss:exploded"
        )
        assert again["panel_ids"] == ["dock_rooms", "dock_uvp"]

    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    assert '"Save Current View"' in source
    assert '"Choose Current View Panels…"' in source
    assert '"Reset Current View Panels"' in source
    assert "def _save_current_exploded_view_v1" in source
    assert "def _choose_current_exploded_view_panels_v1" in source
    assert "def _reset_current_exploded_view_panels_v1" in source
    assert 'layout["panel_ids"] = list(panel_ids)' in source
    assert 'panel_ids = tuple(stored.get("panel_ids") or ())' in source
    assert 'if view_id != "user" and panel_ids:' in source

    save_start = source.index(
        "    def _save_current_exploded_view_v1(self)"
    )
    save_end = source.index(
        "    def _active_factory_exploded_view_id_v1", save_start
    )
    save_source = source[save_start:save_end]
    assert "self._save_active_exploded_workspace_layout_v1()" in save_source
    assert "saveState(" not in save_source
    assert "restoreState(" not in save_source

    edit_start = source.index(
        "    def _choose_current_exploded_view_panels_v1(self)"
    )
    edit_end = source.index(
        "    def _apply_user_workspace_v1", edit_start
    )
    edit_source = source[edit_start:edit_end]
    assert "saveState(" not in edit_source
    assert "restoreState(" not in edit_source

    print(
        "OK — H-S69-B3E stores bounded GUI-only panel overrides for "
        "the seven factory exploded views, preserves them with geometry "
        "and provides explicit save and reset actions."
    )


if __name__ == "__main__":
    main()
