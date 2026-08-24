from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.gui_v3.context.gui_settings import GuiSettings


def main() -> None:
    with TemporaryDirectory() as directory:
        settings_dir = Path(directory)
        path = settings_dir / "gui_v3_workspace.json"
        settings = GuiSettings(settings_dir)
        assert settings.set_workspace_panel_set_v1(
            "heat_loss:docked",
            ["dock_heat_loss", "dock_rooms", "dock_rooms", ""],
        )
        assert not settings.set_workspace_panel_set_v1(
            "user:docked", ["dock_rooms"]
        )
        assert not settings.set_workspace_panel_set_v1(
            "heat_loss:exploded", ["dock_rooms"]
        )
        settings.save()

        stored = json.loads(path.read_text(encoding="utf-8"))
        assert stored["workspace_panel_sets_v1"] == {
            "heat_loss:docked": ["dock_heat_loss", "dock_rooms"]
        }
        restored = GuiSettings(settings_dir)
        assert restored.workspace_panel_set_v1(
            "heat_loss:docked"
        ) == ("dock_heat_loss", "dock_rooms")
        assert restored.clear_workspace_panel_set_v1(
            "heat_loss:docked"
        )
        assert restored.workspace_panel_set_v1(
            "heat_loss:docked"
        ) is None

    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    assert 'main_views_menu.addAction(choose_current_main_view_panels_action)' in source
    assert 'main_views_menu.addAction(reset_current_main_view_panels_action)' in source
    assert "def _choose_current_docked_view_panels_v1" in source
    assert "def _reset_current_docked_view_panels_v1" in source
    assert 'self.addDockWidget(Qt.RightDockWidgetArea, dock)' in source
    assert 'self.tabifyDockWidget(anchor, dock)' in source
    assert 'self._active_docked_workspace_docks_v1 = visible_docks' in source
    assert 'self._active_docked_workspace_view_id_v1 = ""' in source

    prepare_start = source.index(
        "    def _prepare_hydronics_workspace_view_v1"
    )
    prepare_end = source.index(
        "    def _qt_workspace_screens_v1", prepare_start
    )
    docked_source = source[prepare_start:prepare_end]
    assert "saveState(" not in docked_source
    assert "restoreState(" not in docked_source

    print(
        "OK — H-S69-B3F stores bounded GUI-only panel membership for "
        "the seven Main Window Views, retains factory dock structure and "
        "places added panels in a predictable right-side tab group."
    )


if __name__ == "__main__":
    main()
