from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.adapters.environment_panel_adapter import EnvironmentPanelAdapter
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.hydronics.topology.hydronic_topology_v1 import HydronicTopologyV1
from HVAC.project.project_state import ProjectState


class _Context(QObject):
    environment_changed = Signal()
    project_changed = Signal()

    def __init__(self, project_state) -> None:
        super().__init__()
        self.project_state = project_state


def main() -> None:
    app = QApplication.instance() or QApplication([])

    route_rooms = ["room-002", "room-003"]
    topology = SimpleNamespace(
        heat_source_room_id="room-001",
        route_room_ids=route_rooms,
    )
    project = SimpleNamespace(
        environment=EnvironmentStateV1(),
        rooms={
            "room-001": SimpleNamespace(name="Plant room"),
            "room-002": SimpleNamespace(name="Kitchen"),
            "room-003": SimpleNamespace(name="Hall"),
        },
        hydronic_topology=topology,
        hydronics_valid=True,
        heatloss_valid=True,
    )
    context = _Context(project)
    panel = EnvironmentPanel()
    adapter = EnvironmentPanelAdapter(context, panel)
    adapter.refresh()

    combo = panel._heat_source_room_input
    assert combo.count() == 3
    assert combo.currentData() == "room-001"
    assert combo.currentText() == "Plant room"

    project_change_count = 0

    def _count_project_change() -> None:
        nonlocal project_change_count
        project_change_count += 1

    context.project_changed.connect(_count_project_change)
    combo.setCurrentIndex(combo.findData("room-002"))
    app.processEvents()

    assert topology.heat_source_room_id == "room-002"
    assert topology.route_room_ids is route_rooms
    assert topology.route_room_ids == ["room-002", "room-003"]
    assert project.hydronics_valid is False
    assert project.heatloss_valid is True
    assert project_change_count == 1

    persisted = ProjectState(
        project_id="hs68a",
        name="Heat-source room persistence",
        hydronic_topology=HydronicTopologyV1(
            heat_source_room_id="room-002",
        ),
    )
    restored = ProjectState.from_dict(persisted.to_dict())
    assert restored.hydronic_topology is not None
    assert restored.hydronic_topology.heat_source_room_id == "room-002"

    print(
        "OK — H-S68-A Environment selects the persisted topology heat-source "
        "room, marks Hydronics dirty and leaves Heat-Loss and route membership "
        "unchanged."
    )


if __name__ == "__main__":
    main()
