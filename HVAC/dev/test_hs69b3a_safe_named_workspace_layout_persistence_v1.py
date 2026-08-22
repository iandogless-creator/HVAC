from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.gui_v3.context.gui_settings import GuiSettings


def _layout(x: int = 100) -> dict:
    return {
        "docks": {
            "dock_environment": {
                "x": x,
                "y": 80,
                "width": 520,
                "height": 760,
                "screen_name": "Display-1",
            }
        }
    }


def main() -> None:
    with TemporaryDirectory() as directory:
        settings_dir = Path(directory)
        path = settings_dir / "gui_v3_workspace.json"

        # Legacy geometry remains readable; the unsafe opaque state does not.
        path.write_text(
            json.dumps({"geometry": "0102", "state": "aabb"}),
            encoding="utf-8",
        )
        legacy = GuiSettings(settings_dir)
        assert legacy.window_geometry == b"\x01\x02"
        assert legacy.window_state is None
        assert legacy.named_workspace_layouts_v1 == {}

        assert legacy.set_named_workspace_layout_v1(
            "basic_sizing:exploded",
            _layout(),
        )
        assert not legacy.set_named_workspace_layout_v1(
            "broken",
            {"docks": {"dock_local_k": {"width": -1}}},
        )
        legacy.save()

        stored = json.loads(path.read_text(encoding="utf-8"))
        assert stored["state"] == ""
        assert "basic_sizing:exploded" in stored["named_workspace_layouts_v1"]

        restored = GuiSettings(settings_dir)
        layout = restored.named_workspace_layout_v1(
            "basic_sizing:exploded"
        )
        assert layout is not None
        assert layout["docks"]["dock_environment"]["x"] == 100

        # Callers receive a copy and cannot mutate persisted runtime state.
        layout["docks"]["dock_environment"]["x"] = 999
        again = restored.named_workspace_layout_v1(
            "basic_sizing:exploded"
        )
        assert again["docks"]["dock_environment"]["x"] == 100

    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    restore_start = source.index("    def _restore_workspace(self)")
    restore_end = source.index("    # ------------------------------------------------------------------", restore_start)
    workspace_source = source[restore_start:restore_end]
    assert "restoreState(" not in workspace_source
    assert "saveState(" not in workspace_source

    print(
        "OK — H-S69-B3A persists validated named workspace geometry, "
        "retains main-window geometry and refuses legacy opaque Qt dock "
        "state before it can reach restoreState()."
    )


if __name__ == "__main__":
    main()
