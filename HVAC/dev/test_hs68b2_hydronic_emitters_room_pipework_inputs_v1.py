from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import HVAC.gui_v3.adapters.hydronic_control_panel_adapter as adapter_module
from HVAC.gui_v3.adapters.hydronic_control_panel_adapter import (
    HydronicControlPanelAdapter,
)
from HVAC.gui_v3.panels.hydronic_control_panel import HydronicControlPanel


class ProjectStub:
    def __init__(self) -> None:
        self.rooms = {
            "room-source": SimpleNamespace(name="Boiler / Heat Source"),
            "room-middle": SimpleNamespace(name="Middle room"),
            "room-terminal": SimpleNamespace(name="Terminal room"),
        }
        self.emitters = {}
        self.hydronic_topology = SimpleNamespace(
            heat_source_room_id="room-source",
            legs=[
                SimpleNamespace(
                    route_room_ids=["room-middle", "room-terminal"],
                    sublegs=[
                        SimpleNamespace(
                            route_room_ids=[
                                "room-middle",
                                "room-terminal",
                            ],
                            sublegs=[],
                        )
                    ],
                )
            ],
        )
        self.hydronic_room_paired_pipe_length_intent = None
        self.hydronics_valid = True
        self.heatloss_valid = True
        self.dirty_count = 0

    def mark_hydronics_dirty(self) -> None:
        self.hydronics_valid = False
        self.dirty_count += 1


class ContextStub:
    def __init__(self) -> None:
        self.current_room_id = "room-middle"

    def set_current_room(self, room_id: str) -> None:
        self.current_room_id = room_id


def main() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app

    inventory_rows = (
        SimpleNamespace(room_id="room-source", is_terminal=False),
        SimpleNamespace(room_id="room-middle", is_terminal=False),
        SimpleNamespace(room_id="room-terminal", is_terminal=True),
    )
    adapter_module.build_topology_unassigned_room_inventory_v1 = (
        lambda _project: SimpleNamespace(ready=True, rows=inventory_rows)
    )

    project = ProjectStub()
    context = ContextStub()
    refresh_count = {"value": 0}
    panel = HydronicControlPanel()
    adapter = HydronicControlPanelAdapter(
        panel=panel,
        project_state=project,
        context=context,
        refresh_all=lambda: refresh_count.__setitem__(
            "value", refresh_count["value"] + 1
        ),
    )

    assert panel._before_emitter_length_m.objectName() == (
        "hydronicRoomPipeworkBeforeInput"
    )
    assert panel._after_emitter_length_m.objectName() == (
        "hydronicRoomPipeworkAfterInput"
    )
    assert panel._before_emitter_length_m.isEnabled()
    assert panel._after_emitter_length_m.isEnabled()
    assert "not the sum" in panel._before_emitter_length_m.toolTip().lower()
    assert "not the sum" in (
        panel._before_emitter_length_m.lineEdit().toolTip().lower()
    )
    assert "not the sum" in panel._before_emitter_label.toolTip().lower()

    panel._before_emitter_length_m.setValue(3.25)
    panel._before_emitter_length_m.editingFinished.emit()
    panel._after_emitter_length_m.setValue(1.50)
    panel._after_emitter_length_m.editingFinished.emit()

    intent = project.hydronic_room_paired_pipe_length_intent
    assert intent is not None
    middle = intent.lengths_by_room_id["room-middle"]
    assert middle.before_emitter_length_m == 3.25
    assert middle.after_emitter_length_m == 1.50
    assert project.dirty_count == 2
    assert project.hydronics_valid is False
    assert project.heatloss_valid is True
    assert refresh_count["value"] == 2

    # Persisted after-emitter evidence is suppressed, not destroyed, when
    # the room currently becomes a terminal.
    intent.set_room_lengths(
        room_id="room-terminal",
        before_emitter_length_m=2.0,
        after_emitter_length_m=9.0,
    )
    context.current_room_id = "room-terminal"
    adapter.refresh()
    assert panel._before_emitter_length_m.isEnabled()
    assert not panel._after_emitter_length_m.isEnabled()
    assert "terminal" in panel._after_emitter_length_m.toolTip().lower()
    assert panel._after_emitter_length_m.value() < 0.0

    panel._before_emitter_length_m.setValue(4.0)
    panel._before_emitter_length_m.editingFinished.emit()
    terminal = intent.lengths_by_room_id["room-terminal"]
    assert terminal.before_emitter_length_m == 4.0
    assert terminal.after_emitter_length_m == 9.0

    blocked_inventory = SimpleNamespace(
        ready=False,
        rows=(),
        blockers=("Legacy topology is not safely migratable",),
    )
    adapter_module.build_topology_unassigned_room_inventory_v1 = (
        lambda _project: blocked_inventory
    )
    context.current_room_id = "room-terminal"
    adapter.refresh()
    assert panel._before_emitter_length_m.isEnabled()
    assert not panel._after_emitter_length_m.isEnabled()
    assert "terminal" in panel._after_emitter_label.toolTip().lower()

    context.current_room_id = "room-source"
    adapter.refresh()
    assert not panel._before_emitter_length_m.isEnabled()
    assert not panel._after_emitter_length_m.isEnabled()
    dirty_before_blocked_intent = project.dirty_count
    adapter._on_room_pipe_length_changed("room-source", "before", 5.0)
    assert project.dirty_count == dirty_before_blocked_intent
    assert "room-source" not in intent.lengths_by_room_id

    terminal_index = panel._room_combo.findData("room-terminal")
    panel._room_combo.setCurrentIndex(terminal_index)
    assert context.current_room_id == "room-terminal"
    assert not panel._after_emitter_length_m.isEnabled()

    print(
        "OK — H-S68-B2 Hydronic Emitters stores live room paired-pipe "
        "lengths, marks Hydronics dirty, keeps Heat-Loss untouched and "
        "suppresses Heat Source/terminal inputs without deleting evidence."
    )


if __name__ == "__main__":
    main()
