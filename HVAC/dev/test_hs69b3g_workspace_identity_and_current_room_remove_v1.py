from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel


def main() -> None:
    app = QApplication.instance() or QApplication([])

    heat_loss = HeatLossPanelV3()
    emitted: list[object] = []
    heat_loss.remove_room_requested.connect(emitted.append)
    assert not heat_loss._remove_room_btn.isEnabled()

    heat_loss.set_room("room-001")
    assert heat_loss._remove_room_btn.isEnabled()
    heat_loss._remove_room_btn.click()
    assert emitted == ["room-001"]

    heat_loss.clear()
    assert not heat_loss._remove_room_btn.isEnabled()
    heat_loss._remove_room_btn.click()
    assert emitted == ["room-001"]

    rooms = RoomTreePanel()
    assert not hasattr(rooms, "_remove_room_btn")

    adapter_source = Path(
        "HVAC/gui_v3/adapters/room_tree_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert "def request_room_removal_v1" in adapter_source
    assert "build_guarded_room_deletion_plan_v1" in adapter_source
    assert "delete_room_guarded_v1" in adapter_source

    main_source = Path("HVAC/gui_v3/main_window.py").read_text(
        encoding="utf-8"
    )
    assert "request_room_removal_v1" in main_source
    assert 'parent=self._heat_loss_panel' in main_source
    assert "def _workspace_window_title_v1" in main_source
    assert '"User Workspace":' not in main_source
    assert '"user": "User Workspace"' in main_source
    assert 'mode_label = "Floating"' in main_source
    assert 'mode_label = "Exploded"' in main_source
    assert 'mode_label = "Main Window"' in main_source
    assert 'self._set_workspace_window_title_v1(view_id, "docked")' in main_source
    assert 'self._set_workspace_window_title_v1(view_id, "exploded")' in main_source

    heat_loss.close()
    rooms.close()
    app.processEvents()
    print(
        "OK — H-S69-B3G identifies the active workspace in the main "
        "shell and places guarded Remove with the current-room Heat-Loss "
        "actions without changing deletion authority."
    )


if __name__ == "__main__":
    main()
