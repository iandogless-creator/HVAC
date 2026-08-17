from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.adapters.project_panel_adapter import ProjectPanelAdapter
from HVAC.gui_v3.panels.project_panel import ProjectPanel


class _Context(QObject):
    project_changed = Signal()
    environment_changed = Signal()
    room_state_changed = Signal(str)

    def __init__(self, project_state) -> None:
        super().__init__()
        self.project_state = project_state


def _project(**overrides):
    values = dict(
        name="Compact test",
        project_dir=Path("/tmp/HVACgooee compact test"),
        rooms={"room-1": object(), "room-2": object()},
        heatloss_results=None,
        heatloss_valid=False,
        hydronics_results=None,
        hydronics_valid=False,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    context = _Context(_project())
    panel = ProjectPanel()
    adapter = ProjectPanelAdapter(panel=panel, context=context)

    assert panel._lbl_project_name.text() == "Compact test"
    assert panel._lbl_project_folder.text() == "HVACgooee compact test"
    assert panel._lbl_room_count.text() == "2"
    assert panel._lbl_heatloss_status.text() == "NOT RUN"
    assert panel._lbl_hydronics_status.text() == "NOT RUN"

    context.project_state.heatloss_results = {"room_totals": {}}
    context.room_state_changed.emit("room-1")
    assert panel._lbl_heatloss_status.text() == "DIRTY"

    context.project_state.heatloss_valid = True
    adapter.refresh()
    assert panel._lbl_heatloss_status.text() == "VALID"

    context.project_state = _project(
        name="Replacement",
        project_dir=None,
        rooms={"room-a": object()},
        hydronics_results={"sections": {}},
    )
    context.project_changed.emit()
    app.processEvents()
    assert panel._lbl_project_name.text() == "Replacement"
    assert panel._lbl_project_folder.text() == "Unsaved"
    assert panel._lbl_room_count.text() == "1"
    assert panel._lbl_hydronics_status.text() == "DIRTY"

    print(
        "OK — HL-S2C3B Project panel shows compact live project, folder, "
        "room-count and lifecycle status evidence."
    )


if __name__ == "__main__":
    main()
